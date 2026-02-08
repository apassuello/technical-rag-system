#!/usr/bin/env python3
"""
Retrieval Quality Evaluator using RAGAS Framework
=================================================

Implements proper RAG evaluation metrics focused on retrieval quality:
- Context Precision: relevant_docs / total_retrieved_docs  
- Context Recall: relevant_docs / total_relevant_docs
- Mean Reciprocal Rank (MRR): ranking quality
- NDCG@K: position-weighted relevance scoring

This replaces the inadequate 0.8000 "quality score" with meaningful metrics.
"""

import logging
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List

import numpy as np

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from src.core.interfaces import Document
from src.core.platform_orchestrator import PlatformOrchestrator

logger = logging.getLogger(__name__)

@dataclass
class QueryResult:
    """Result of a single query evaluation."""
    query_id: str
    query: str
    retrieved_docs: List[Dict[str, Any]]
    ground_truth_relevant: List[str]  # Document IDs that should be relevant
    context_precision: float
    context_recall: float  
    mrr: float
    ndcg_at_5: float
    response_time: float

@dataclass
class RetrievalEvaluationResults:
    """Complete evaluation results across all queries."""
    config_name: str
    query_results: List[QueryResult]
    avg_context_precision: float
    avg_context_recall: float
    avg_mrr: float
    avg_ndcg_at_5: float
    avg_response_time: float
    total_queries: int


class RetrievalQualityEvaluator:
    """
    Evaluator for retrieval quality using proper RAG metrics.
    
    Focuses on the key question: Are we retrieving the RIGHT documents?
    """
    
    def __init__(self, platform_orchestrator: PlatformOrchestrator):
        """Initialize with a configured platform orchestrator."""
        self.platform_orchestrator = platform_orchestrator
        self.indexed_documents = []
        
    def index_documents(self, documents: List[Document]) -> None:
        """Index documents for retrieval evaluation."""
        logger.info(f"Indexing {len(documents)} documents for evaluation")
        self.indexed_documents = documents
        self.platform_orchestrator.index_documents(documents)
        logger.info("Documents indexed successfully")
        
    def calculate_context_precision(self, retrieved_docs: List[Dict], relevant_doc_ids: List[str]) -> float:
        """
        Calculate Context Precision: relevant_retrieved / total_retrieved
        
        Measures signal-to-noise ratio in retrieval results.
        Higher is better - indicates fewer irrelevant documents retrieved.
        """
        if not retrieved_docs:
            return 0.0
            
        relevant_retrieved = sum(1 for doc in retrieved_docs 
                               if doc.get('source', '') in relevant_doc_ids)
        
        return relevant_retrieved / len(retrieved_docs)
    
    def calculate_context_recall(self, retrieved_docs: List[Dict], relevant_doc_ids: List[str]) -> float:
        """
        Calculate Context Recall: relevant_retrieved / total_relevant
        
        Measures coverage of relevant information.
        Higher is better - indicates we found most relevant documents.
        """
        if not relevant_doc_ids:
            return 1.0  # No relevant docs to find
            
        retrieved_doc_ids = set(doc.get('source', '') for doc in retrieved_docs)
        relevant_retrieved = sum(1 for doc_id in relevant_doc_ids 
                               if doc_id in retrieved_doc_ids)
        
        return relevant_retrieved / len(relevant_doc_ids)
    
    def calculate_mrr(self, retrieved_docs: List[Dict], relevant_doc_ids: List[str]) -> float:
        """
        Calculate Mean Reciprocal Rank: 1/rank_of_first_relevant_doc
        
        Measures ranking quality - how quickly we find relevant documents.
        Higher is better - indicates relevant docs appear early in ranking.
        """
        for rank, doc in enumerate(retrieved_docs, 1):
            if doc.get('source', '') in relevant_doc_ids:
                return 1.0 / rank
        
        return 0.0  # No relevant documents found
    
    def calculate_ndcg_at_k(self, retrieved_docs: List[Dict], relevant_doc_ids: List[str], k: int = 5) -> float:
        """
        Calculate Normalized Discounted Cumulative Gain at K.
        
        Measures ranking quality with position weighting.
        Higher positions get higher weights, relevant docs should appear early.
        """
        if not retrieved_docs or not relevant_doc_ids:
            return 0.0
            
        # Calculate DCG@K
        dcg = 0.0
        for i, doc in enumerate(retrieved_docs[:k]):
            if doc.get('source', '') in relevant_doc_ids:
                # Relevant document gets score of 1, discounted by position
                dcg += 1.0 / np.log2(i + 2)  # +2 because log2(1) = 0
        
        # Calculate IDCG@K (ideal ranking - all relevant docs first)
        num_relevant = min(len(relevant_doc_ids), k)
        idcg = sum(1.0 / np.log2(i + 2) for i in range(num_relevant))
        
        return dcg / idcg if idcg > 0 else 0.0
    
    def evaluate_single_query(self, query_id: str, query: str, 
                            relevant_doc_ids: List[str]) -> QueryResult:
        """
        Evaluate retrieval quality for a single query.
        
        Returns comprehensive metrics for this specific query.
        """
        logger.info(f"Evaluating query: {query}")
        
        # Measure retrieval performance
        start_time = time.time()
        
        # Get retrieval results (without generating answer)
        retriever = self.platform_orchestrator._components.get('retriever')
        if not retriever:
            raise ValueError("No retriever component found in platform orchestrator")
            
        # Perform retrieval
        retrieved_results = retriever.retrieve(query, k=10)  # Get top 10 for evaluation
        response_time = time.time() - start_time
        
        # Convert results to evaluation format
        retrieved_docs = []
        for result in retrieved_results:
            retrieved_docs.append({
                'content': result.document.content,
                'source': result.document.metadata.get('source', ''),
                'score': result.score
            })
        
        # Calculate all metrics
        context_precision = self.calculate_context_precision(retrieved_docs, relevant_doc_ids)
        context_recall = self.calculate_context_recall(retrieved_docs, relevant_doc_ids)
        mrr = self.calculate_mrr(retrieved_docs, relevant_doc_ids)
        ndcg_at_5 = self.calculate_ndcg_at_k(retrieved_docs, relevant_doc_ids, k=5)
        
        logger.info(f"Query '{query}' results:")
        logger.info(f"  Context Precision: {context_precision:.3f}")
        logger.info(f"  Context Recall: {context_recall:.3f}")
        logger.info(f"  MRR: {mrr:.3f}")
        logger.info(f"  NDCG@5: {ndcg_at_5:.3f}")
        logger.info(f"  Response Time: {response_time:.3f}s")
        
        return QueryResult(
            query_id=query_id,
            query=query,
            retrieved_docs=retrieved_docs,
            ground_truth_relevant=relevant_doc_ids,
            context_precision=context_precision,
            context_recall=context_recall,
            mrr=mrr,
            ndcg_at_5=ndcg_at_5,
            response_time=response_time
        )
    
    def evaluate_query_set(self, queries: List[Dict[str, Any]], 
                          config_name: str = "unknown") -> RetrievalEvaluationResults:
        """
        Evaluate retrieval quality across a set of queries.
        
        Args:
            queries: List of dicts with 'id', 'query', 'relevant_docs' keys
            config_name: Name of configuration being evaluated
            
        Returns:
            Comprehensive evaluation results with averages across all queries
        """
        logger.info(f"Starting evaluation of {len(queries)} queries for config: {config_name}")
        
        query_results = []
        
        for query_data in queries:
            try:
                result = self.evaluate_single_query(
                    query_id=query_data['id'],
                    query=query_data['query'],
                    relevant_doc_ids=query_data['relevant_docs']
                )
                query_results.append(result)
                
            except Exception as e:
                logger.error(f"Failed to evaluate query {query_data['id']}: {e}")
                continue
        
        if not query_results:
            logger.error("No queries were successfully evaluated")
            return RetrievalEvaluationResults(
                config_name=config_name,
                query_results=[],
                avg_context_precision=0.0,
                avg_context_recall=0.0,
                avg_mrr=0.0,
                avg_ndcg_at_5=0.0,
                avg_response_time=0.0,
                total_queries=0
            )
        
        # Calculate averages
        avg_context_precision = np.mean([r.context_precision for r in query_results])
        avg_context_recall = np.mean([r.context_recall for r in query_results])
        avg_mrr = np.mean([r.mrr for r in query_results])
        avg_ndcg_at_5 = np.mean([r.ndcg_at_5 for r in query_results])
        avg_response_time = np.mean([r.response_time for r in query_results])
        
        results = RetrievalEvaluationResults(
            config_name=config_name,
            query_results=query_results,
            avg_context_precision=avg_context_precision,
            avg_context_recall=avg_context_recall,
            avg_mrr=avg_mrr,
            avg_ndcg_at_5=avg_ndcg_at_5,
            avg_response_time=avg_response_time,
            total_queries=len(query_results)
        )
        
        # Log summary
        logger.info(f"Evaluation complete for {config_name}:")
        logger.info(f"  Average Context Precision: {avg_context_precision:.3f}")
        logger.info(f"  Average Context Recall: {avg_context_recall:.3f}")
        logger.info(f"  Average MRR: {avg_mrr:.3f}")
        logger.info(f"  Average NDCG@5: {avg_ndcg_at_5:.3f}")
        logger.info(f"  Average Response Time: {avg_response_time:.3f}s")
        
        return results
    
    def compare_configurations(self, baseline_results: RetrievalEvaluationResults,
                             optimized_results: RetrievalEvaluationResults) -> Dict[str, Any]:
        """
        Compare baseline vs optimized configuration results.
        
        Returns statistical comparison with improvement percentages.
        """
        comparison = {
            'baseline_config': baseline_results.config_name,
            'optimized_config': optimized_results.config_name,
            'improvements': {}
        }
        
        metrics = [
            ('context_precision', 'Context Precision'),
            ('context_recall', 'Context Recall'),
            ('mrr', 'Mean Reciprocal Rank'),
            ('ndcg_at_5', 'NDCG@5'),
            ('response_time', 'Response Time (lower is better)')
        ]
        
        for metric_key, metric_name in metrics:
            baseline_val = getattr(baseline_results, f'avg_{metric_key}')
            optimized_val = getattr(optimized_results, f'avg_{metric_key}')
            
            if baseline_val > 0:
                if metric_key == 'response_time':
                    # For response time, lower is better
                    improvement_pct = ((baseline_val - optimized_val) / baseline_val) * 100
                else:
                    # For other metrics, higher is better
                    improvement_pct = ((optimized_val - baseline_val) / baseline_val) * 100
            else:
                improvement_pct = 0.0
            
            comparison['improvements'][metric_key] = {
                'metric_name': metric_name,
                'baseline': baseline_val,
                'optimized': optimized_val,
                'improvement_pct': improvement_pct,
                'significant': abs(improvement_pct) >= 5.0  # 5% threshold
            }
        
        return comparison
    
    def print_evaluation_report(self, results: RetrievalEvaluationResults) -> None:
        """Print a comprehensive evaluation report."""
        
        logger.info(f"\n{'='*80}")
        logger.info("RETRIEVAL QUALITY EVALUATION REPORT")
        logger.info(f"Configuration: {results.config_name}")
        logger.info(f"{'='*80}")
        
        logger.info(f"\n📊 OVERALL METRICS (Average across {results.total_queries} queries)")
        logger.info("-" * 60)
        logger.info(f"Context Precision:    {results.avg_context_precision:.3f}")
        logger.info(f"Context Recall:       {results.avg_context_recall:.3f}")
        logger.info(f"Mean Reciprocal Rank: {results.avg_mrr:.3f}")
        logger.info(f"NDCG@5:              {results.avg_ndcg_at_5:.3f}")
        logger.info(f"Avg Response Time:    {results.avg_response_time:.3f}s")
        
        # Performance assessment
        logger.info("\n🎯 PERFORMANCE ASSESSMENT")
        logger.info("-" * 60)
        
        # Context Precision assessment
        if results.avg_context_precision >= 0.8:
            precision_status = "EXCELLENT ✅"
        elif results.avg_context_precision >= 0.6:
            precision_status = "GOOD 👍"
        elif results.avg_context_precision >= 0.4:
            precision_status = "FAIR ⚠️"
        else:
            precision_status = "POOR ❌"
        logger.info(f"Context Precision: {precision_status}")
        
        # Context Recall assessment  
        if results.avg_context_recall >= 0.8:
            recall_status = "EXCELLENT ✅"
        elif results.avg_context_recall >= 0.6:
            recall_status = "GOOD 👍"
        elif results.avg_context_recall >= 0.4:
            recall_status = "FAIR ⚠️"
        else:
            recall_status = "POOR ❌"
        logger.info(f"Context Recall:    {recall_status}")
        
        # MRR assessment
        if results.avg_mrr >= 0.7:
            mrr_status = "EXCELLENT ✅"
        elif results.avg_mrr >= 0.5:
            mrr_status = "GOOD 👍"
        elif results.avg_mrr >= 0.3:
            mrr_status = "FAIR ⚠️"
        else:
            mrr_status = "POOR ❌"
        logger.info(f"Ranking Quality:   {mrr_status}")
        
        logger.info("\n📈 DETAILED QUERY RESULTS")
        logger.info("-" * 60)
        for result in results.query_results[:5]:  # Show first 5 queries
            logger.info(f"Query: {result.query[:50]}...")
            logger.info(f"  Precision: {result.context_precision:.3f}, Recall: {result.context_recall:.3f}, MRR: {result.mrr:.3f}")
        
        if len(results.query_results) > 5:
            logger.info(f"... and {len(results.query_results) - 5} more queries")


if __name__ == "__main__":
    # Test the evaluator
    logging.basicConfig(level=logging.INFO)
    
    # Initialize platform orchestrator with test config
    po = PlatformOrchestrator("config/test_epic2_graph_enabled.yaml")
    evaluator = RetrievalQualityEvaluator(po)
    
    # Create test documents
    test_docs = [
        Document(
            content="RISC-V is an open-source instruction set architecture based on RISC principles.",
            metadata={"source": "riscv-intro.pdf", "title": "RISC-V Introduction"}
        ),
        Document(
            content="The RISC-V vector extension provides SIMD capabilities for parallel computation.",
            metadata={"source": "riscv-vector.pdf", "title": "RISC-V Vector Extension"}
        )
    ]
    
    evaluator.index_documents(test_docs)
    
    # Test query
    test_queries = [{
        'id': 'TEST_001',
        'query': 'What is RISC-V?',
        'relevant_docs': ['riscv-intro.pdf']
    }]
    
    results = evaluator.evaluate_query_set(test_queries, "test_config")
    evaluator.print_evaluation_report(results)