"""
Neural Reranking Evaluation System.

This module provides comprehensive evaluation metrics and tools for assessing
the performance of neural reranking models, including standard IR metrics
and custom quality assessments.
"""

import time
import logging
from typing import List, Dict, Any, Tuple, Optional, Set
from dataclasses import dataclass
from collections import defaultdict
import numpy as np
from statistics import mean, median

from ....core.interfaces import Document

logger = logging.getLogger(__name__)


@dataclass 
class EvaluationResult:
    """Results from a reranking evaluation."""
    metric_name: str
    score: float
    details: Dict[str, Any]
    query_scores: Optional[Dict[str, float]] = None


@dataclass
class RerankingComparison:
    """Comparison between different reranking approaches."""
    baseline_name: str
    test_name: str
    baseline_results: Dict[str, float]
    test_results: Dict[str, float]
    improvements: Dict[str, float]
    significance_test: Optional[Dict[str, Any]] = None


class RerankingEvaluator:
    """
    Comprehensive evaluation system for neural reranking models.
    
    This evaluator provides standard Information Retrieval metrics (NDCG, MAP, MRR)
    as well as custom metrics for assessing reranking quality, latency, and
    improvements over baseline approaches.
    """
    
    def __init__(self, k_values: List[int] = [1, 3, 5, 10, 20]):
        """
        Initialize reranking evaluator.
        
        Args:
            k_values: List of k values for computing metrics at different cutoffs
        """
        self.k_values = k_values
        
        # Available metrics
        self.metrics = {
            "ndcg": self._compute_ndcg,
            "map": self._compute_map,
            "mrr": self._compute_mrr,
            "precision": self._compute_precision,
            "recall": self._compute_recall,
            "f1": self._compute_f1,
            "hit_rate": self._compute_hit_rate,
            "rank_correlation": self._compute_rank_correlation,
        }
        
        logger.info(f"RerankingEvaluator initialized with k_values: {k_values}")
    
    def evaluate_reranking(self,
                          queries: List[str],
                          ground_truth: List[List[Tuple[Document, float]]],
                          predictions: List[List[Tuple[Document, float]]],
                          baseline_predictions: Optional[List[List[Tuple[Document, float]]]] = None,
                          metrics: Optional[List[str]] = None) -> Dict[str, EvaluationResult]:
        """
        Evaluate reranking performance.
        
        Args:
            queries: List of evaluation queries
            ground_truth: List of ground truth (document, relevance) pairs for each query
            predictions: List of predicted (document, score) pairs for each query
            baseline_predictions: Optional baseline predictions for comparison
            metrics: Optional list of specific metrics to compute
            
        Returns:
            Dictionary mapping metric names to evaluation results
        """
        if not queries or len(queries) != len(ground_truth) or len(queries) != len(predictions):
            raise ValueError("Queries, ground truth, and predictions must have same length")
        
        metrics_to_compute = metrics or list(self.metrics.keys())
        results = {}
        
        # Compute each metric
        for metric_name in metrics_to_compute:
            if metric_name not in self.metrics:
                logger.warning(f"Unknown metric: {metric_name}")
                continue
            
            metric_func = self.metrics[metric_name]
            result = metric_func(queries, ground_truth, predictions)
            results[metric_name] = result
        
        # Compute comparison with baseline if provided
        if baseline_predictions:
            comparison = self._compare_with_baseline(
                queries, ground_truth, predictions, baseline_predictions, metrics_to_compute
            )
            results["baseline_comparison"] = EvaluationResult(
                metric_name="baseline_comparison",
                score=0.0,  # Not applicable
                details=comparison
            )
        
        logger.info(f"Evaluation completed for {len(queries)} queries with {len(results)} metrics")
        return results
    
    def _compute_ndcg(self,
                     queries: List[str],
                     ground_truth: List[List[Tuple[Document, float]]],
                     predictions: List[List[Tuple[Document, float]]]) -> EvaluationResult:
        """Compute Normalized Discounted Cumulative Gain (NDCG)."""
        query_scores = {}
        all_scores = []
        
        for i, (query, gt, pred) in enumerate(zip(queries, ground_truth, predictions)):
            # Create relevance mapping
            relevance_map = {self._doc_id(doc): rel for doc, rel in gt}
            
            scores_at_k = {}
            for k in self.k_values:
                if k > len(pred):
                    continue
                
                # Compute DCG@k
                dcg = 0.0
                for rank, (doc, score) in enumerate(pred[:k]):
                    doc_id = self._doc_id(doc)
                    relevance = relevance_map.get(doc_id, 0.0)
                    dcg += (2 ** relevance - 1) / np.log2(rank + 2)
                
                # Compute IDCG@k
                ideal_relevances = sorted([rel for _, rel in gt], reverse=True)[:k]
                idcg = 0.0
                for rank, relevance in enumerate(ideal_relevances):
                    idcg += (2 ** relevance - 1) / np.log2(rank + 2)
                
                # Compute NDCG@k
                ndcg_k = dcg / idcg if idcg > 0 else 0.0
                scores_at_k[f"ndcg@{k}"] = ndcg_k
            
            query_scores[query] = scores_at_k
            all_scores.extend(scores_at_k.values())
        
        # Compute average across all queries and k values
        avg_score = mean(all_scores) if all_scores else 0.0
        
        # Compute average for each k
        k_averages = {}
        for k in self.k_values:
            k_scores = []
            for scores in query_scores.values():
                if f"ndcg@{k}" in scores:
                    k_scores.append(scores[f"ndcg@{k}"])
            k_averages[f"ndcg@{k}"] = mean(k_scores) if k_scores else 0.0
        
        return EvaluationResult(
            metric_name="ndcg",
            score=avg_score,
            details={"k_averages": k_averages, "num_queries": len(queries)},
            query_scores=query_scores
        )
    
    def _compute_map(self,
                    queries: List[str],
                    ground_truth: List[List[Tuple[Document, float]]],
                    predictions: List[List[Tuple[Document, float]]]) -> EvaluationResult:
        """Compute Mean Average Precision (MAP)."""
        query_scores = {}
        
        for query, gt, pred in zip(queries, ground_truth, predictions):
            # Create relevance mapping (binary: relevant if > threshold)
            relevance_threshold = 0.5
            relevant_docs = {self._doc_id(doc) for doc, rel in gt if rel > relevance_threshold}
            
            if not relevant_docs:
                query_scores[query] = 0.0
                continue
            
            # Compute average precision
            relevant_retrieved = 0
            precision_sum = 0.0
            
            for rank, (doc, score) in enumerate(pred):
                doc_id = self._doc_id(doc)
                if doc_id in relevant_docs:
                    relevant_retrieved += 1
                    precision_at_rank = relevant_retrieved / (rank + 1)
                    precision_sum += precision_at_rank
            
            average_precision = precision_sum / len(relevant_docs) if relevant_docs else 0.0
            query_scores[query] = average_precision
        
        map_score = mean(query_scores.values()) if query_scores else 0.0
        
        return EvaluationResult(
            metric_name="map",
            score=map_score,
            details={"num_queries": len(queries)},
            query_scores=query_scores
        )
    
    def _compute_mrr(self,
                    queries: List[str],
                    ground_truth: List[List[Tuple[Document, float]]],
                    predictions: List[List[Tuple[Document, float]]]) -> EvaluationResult:
        """Compute Mean Reciprocal Rank (MRR)."""
        query_scores = {}
        
        for query, gt, pred in zip(queries, ground_truth, predictions):
            # Find highest relevance score
            max_relevance = max([rel for _, rel in gt]) if gt else 0.0
            relevance_threshold = max_relevance * 0.8  # 80% of max relevance
            
            relevant_docs = {self._doc_id(doc) for doc, rel in gt if rel >= relevance_threshold}
            
            # Find rank of first relevant document
            reciprocal_rank = 0.0
            for rank, (doc, score) in enumerate(pred):
                doc_id = self._doc_id(doc)
                if doc_id in relevant_docs:
                    reciprocal_rank = 1.0 / (rank + 1)
                    break
            
            query_scores[query] = reciprocal_rank
        
        mrr_score = mean(query_scores.values()) if query_scores else 0.0
        
        return EvaluationResult(
            metric_name="mrr",
            score=mrr_score,
            details={"num_queries": len(queries)},
            query_scores=query_scores
        )
    
    def _compute_precision(self,
                          queries: List[str],
                          ground_truth: List[List[Tuple[Document, float]]],
                          predictions: List[List[Tuple[Document, float]]]) -> EvaluationResult:
        """Compute Precision at different k values."""
        query_scores = {}
        
        for query, gt, pred in zip(queries, ground_truth, predictions):
            relevance_threshold = 0.5
            relevant_docs = {self._doc_id(doc) for doc, rel in gt if rel > relevance_threshold}
            
            scores_at_k = {}
            for k in self.k_values:
                if k > len(pred):
                    continue
                
                retrieved_at_k = {self._doc_id(doc) for doc, _ in pred[:k]}
                relevant_retrieved = len(retrieved_at_k & relevant_docs)
                precision_k = relevant_retrieved / k if k > 0 else 0.0
                scores_at_k[f"precision@{k}"] = precision_k
            
            query_scores[query] = scores_at_k
        
        # Compute averages
        all_scores = []
        k_averages = {}
        for k in self.k_values:
            k_scores = []
            for scores in query_scores.values():
                if f"precision@{k}" in scores:
                    k_scores.append(scores[f"precision@{k}"])
                    all_scores.append(scores[f"precision@{k}"])
            k_averages[f"precision@{k}"] = mean(k_scores) if k_scores else 0.0
        
        avg_score = mean(all_scores) if all_scores else 0.0
        
        return EvaluationResult(
            metric_name="precision",
            score=avg_score,
            details={"k_averages": k_averages, "num_queries": len(queries)},
            query_scores=query_scores
        )
    
    def _compute_recall(self,
                       queries: List[str],
                       ground_truth: List[List[Tuple[Document, float]]],
                       predictions: List[List[Tuple[Document, float]]]) -> EvaluationResult:
        """Compute Recall at different k values."""
        query_scores = {}
        
        for query, gt, pred in zip(queries, ground_truth, predictions):
            relevance_threshold = 0.5
            relevant_docs = {self._doc_id(doc) for doc, rel in gt if rel > relevance_threshold}
            
            if not relevant_docs:
                # No relevant documents for this query
                scores_at_k = {f"recall@{k}": 0.0 for k in self.k_values}
                query_scores[query] = scores_at_k
                continue
            
            scores_at_k = {}
            for k in self.k_values:
                if k > len(pred):
                    continue
                
                retrieved_at_k = {self._doc_id(doc) for doc, _ in pred[:k]}
                relevant_retrieved = len(retrieved_at_k & relevant_docs)
                recall_k = relevant_retrieved / len(relevant_docs)
                scores_at_k[f"recall@{k}"] = recall_k
            
            query_scores[query] = scores_at_k
        
        # Compute averages
        all_scores = []
        k_averages = {}
        for k in self.k_values:
            k_scores = []
            for scores in query_scores.values():
                if f"recall@{k}" in scores:
                    k_scores.append(scores[f"recall@{k}"])
                    all_scores.append(scores[f"recall@{k}"])
            k_averages[f"recall@{k}"] = mean(k_scores) if k_scores else 0.0
        
        avg_score = mean(all_scores) if all_scores else 0.0
        
        return EvaluationResult(
            metric_name="recall",
            score=avg_score,
            details={"k_averages": k_averages, "num_queries": len(queries)},
            query_scores=query_scores
        )
    
    def _compute_f1(self,
                   queries: List[str],
                   ground_truth: List[List[Tuple[Document, float]]],
                   predictions: List[List[Tuple[Document, float]]]) -> EvaluationResult:
        """Compute F1 score at different k values."""
        # First compute precision and recall
        precision_result = self._compute_precision(queries, ground_truth, predictions)
        recall_result = self._compute_recall(queries, ground_truth, predictions)
        
        query_scores = {}
        k_averages = {}
        all_scores = []
        
        for k in self.k_values:
            k_scores = []
            
            for query in queries:
                prec_scores = precision_result.query_scores.get(query, {})
                rec_scores = recall_result.query_scores.get(query, {})
                
                prec_k = prec_scores.get(f"precision@{k}", 0.0)
                rec_k = rec_scores.get(f"recall@{k}", 0.0)
                
                if prec_k + rec_k > 0:
                    f1_k = 2 * (prec_k * rec_k) / (prec_k + rec_k)
                else:
                    f1_k = 0.0
                
                k_scores.append(f1_k)
                all_scores.append(f1_k)
                
                if query not in query_scores:
                    query_scores[query] = {}
                query_scores[query][f"f1@{k}"] = f1_k
            
            k_averages[f"f1@{k}"] = mean(k_scores) if k_scores else 0.0
        
        avg_score = mean(all_scores) if all_scores else 0.0
        
        return EvaluationResult(
            metric_name="f1",
            score=avg_score,
            details={"k_averages": k_averages, "num_queries": len(queries)},
            query_scores=query_scores
        )
    
    def _compute_hit_rate(self,
                         queries: List[str],
                         ground_truth: List[List[Tuple[Document, float]]],
                         predictions: List[List[Tuple[Document, float]]]) -> EvaluationResult:
        """Compute hit rate (whether any relevant document is in top-k)."""
        query_scores = {}
        
        for query, gt, pred in zip(queries, ground_truth, predictions):
            relevance_threshold = 0.5
            relevant_docs = {self._doc_id(doc) for doc, rel in gt if rel > relevance_threshold}
            
            scores_at_k = {}
            for k in self.k_values:
                if k > len(pred):
                    continue
                
                retrieved_at_k = {self._doc_id(doc) for doc, _ in pred[:k]}
                hit = 1.0 if len(retrieved_at_k & relevant_docs) > 0 else 0.0
                scores_at_k[f"hit_rate@{k}"] = hit
            
            query_scores[query] = scores_at_k
        
        # Compute averages
        all_scores = []
        k_averages = {}
        for k in self.k_values:
            k_scores = []
            for scores in query_scores.values():
                if f"hit_rate@{k}" in scores:
                    k_scores.append(scores[f"hit_rate@{k}"])
                    all_scores.append(scores[f"hit_rate@{k}"])
            k_averages[f"hit_rate@{k}"] = mean(k_scores) if k_scores else 0.0
        
        avg_score = mean(all_scores) if all_scores else 0.0
        
        return EvaluationResult(
            metric_name="hit_rate",
            score=avg_score,
            details={"k_averages": k_averages, "num_queries": len(queries)},
            query_scores=query_scores
        )
    
    def _compute_rank_correlation(self,
                                 queries: List[str],
                                 ground_truth: List[List[Tuple[Document, float]]],
                                 predictions: List[List[Tuple[Document, float]]]) -> EvaluationResult:
        """Compute rank correlation between predictions and ground truth."""
        query_scores = {}
        
        for query, gt, pred in zip(queries, ground_truth, predictions):
            # Create relevance mapping
            relevance_map = {self._doc_id(doc): rel for doc, rel in gt}
            
            # Get prediction scores for documents that have ground truth
            pred_scores = []
            true_scores = []
            
            for doc, score in pred:
                doc_id = self._doc_id(doc)
                if doc_id in relevance_map:
                    pred_scores.append(score)
                    true_scores.append(relevance_map[doc_id])
            
            # Compute Spearman correlation if we have enough data
            if len(pred_scores) >= 2:
                try:
                    correlation = np.corrcoef(pred_scores, true_scores)[0, 1]
                    if np.isnan(correlation):
                        correlation = 0.0
                except:
                    correlation = 0.0
            else:
                correlation = 0.0
            
            query_scores[query] = correlation
        
        avg_correlation = mean(query_scores.values()) if query_scores else 0.0
        
        return EvaluationResult(
            metric_name="rank_correlation",
            score=avg_correlation,
            details={"num_queries": len(queries)},
            query_scores=query_scores
        )
    
    def _compare_with_baseline(self,
                              queries: List[str],
                              ground_truth: List[List[Tuple[Document, float]]],
                              test_predictions: List[List[Tuple[Document, float]]],
                              baseline_predictions: List[List[Tuple[Document, float]]],
                              metrics: List[str]) -> Dict[str, Any]:
        """Compare test results with baseline."""
        # Evaluate baseline
        baseline_results = {}
        for metric_name in metrics:
            if metric_name in self.metrics:
                result = self.metrics[metric_name](queries, ground_truth, baseline_predictions)
                baseline_results[metric_name] = result.score
        
        # Evaluate test
        test_results = {}
        for metric_name in metrics:
            if metric_name in self.metrics:
                result = self.metrics[metric_name](queries, ground_truth, test_predictions)
                test_results[metric_name] = result.score
        
        # Compute improvements
        improvements = {}
        for metric_name in baseline_results:
            baseline_score = baseline_results[metric_name]
            test_score = test_results[metric_name]
            
            if baseline_score > 0:
                improvement = ((test_score - baseline_score) / baseline_score) * 100
            else:
                improvement = 0.0 if test_score == 0 else float('inf')
            
            improvements[metric_name] = improvement
        
        return {
            "baseline_results": baseline_results,
            "test_results": test_results,
            "improvements": improvements,
            "summary": {
                "avg_improvement": mean(improvements.values()) if improvements else 0.0,
                "positive_improvements": sum(1 for imp in improvements.values() if imp > 0),
                "total_metrics": len(improvements)
            }
        }
    
    def _doc_id(self, document: Document) -> str:
        """Get a unique identifier for a document."""
        return document.metadata.get("id", f"doc_{hash(document.content)}")
    
    def print_evaluation_summary(self, results: Dict[str, EvaluationResult]) -> None:
        """Print a formatted summary of evaluation results."""
        print("\n" + "="*60)
        print("NEURAL RERANKING EVALUATION SUMMARY")
        print("="*60)
        
        for metric_name, result in results.items():
            if metric_name == "baseline_comparison":
                print(f"\n📊 BASELINE COMPARISON:")
                comparison = result.details
                for metric, improvement in comparison["improvements"].items():
                    print(f"   {metric.upper()}: {improvement:+.2f}% improvement")
                continue
            
            print(f"\n📈 {metric_name.upper()}: {result.score:.4f}")
            
            if "k_averages" in result.details:
                for k_metric, score in result.details["k_averages"].items():
                    print(f"   {k_metric}: {score:.4f}")
        
        print("\n" + "="*60)