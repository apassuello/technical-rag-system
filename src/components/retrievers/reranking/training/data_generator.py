"""
Training Data Generator for Neural Reranking.

This module generates training data for neural reranking models from user
interactions, query logs, and explicit feedback to improve model performance
over time.
"""

import json
import time
import logging
from typing import List, Dict, Any, Tuple, Optional, Set
from pathlib import Path
from dataclasses import dataclass
from collections import defaultdict
import random

from ....core.interfaces import Document

logger = logging.getLogger(__name__)


@dataclass
class QueryDocumentPair:
    """A query-document pair with relevance label."""
    query: str
    document: Document
    relevance_score: float  # 0.0 (not relevant) to 1.0 (highly relevant)
    interaction_type: str   # "click", "dwell", "rating", "manual"
    timestamp: float
    metadata: Dict[str, Any]


@dataclass
class TrainingExample:
    """A training example for neural reranking."""
    query: str
    positive_docs: List[Document]
    negative_docs: List[Document]
    relevance_scores: Dict[str, float]  # doc_id -> relevance
    source: str  # "user_interaction", "explicit_feedback", "synthetic"


class TrainingDataGenerator:
    """
    Generates training data for neural reranking models.
    
    This class collects user interactions, explicit feedback, and generates
    synthetic training examples to create high-quality training data for
    improving neural reranking performance.
    """
    
    def __init__(self, 
                 data_dir: Path = Path("data/reranking_training"),
                 min_interactions_per_query: int = 3,
                 relevance_threshold: float = 0.6):
        """
        Initialize training data generator.
        
        Args:
            data_dir: Directory to store training data
            min_interactions_per_query: Minimum interactions needed per query
            relevance_threshold: Threshold for positive/negative classification
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.min_interactions_per_query = min_interactions_per_query
        self.relevance_threshold = relevance_threshold
        
        # Storage for interactions
        self.interactions: List[QueryDocumentPair] = []
        self.query_interactions: Dict[str, List[QueryDocumentPair]] = defaultdict(list)
        
        # Load existing interactions
        self._load_existing_interactions()
        
        logger.info(f"TrainingDataGenerator initialized with {len(self.interactions)} existing interactions")
    
    def record_interaction(self,
                          query: str,
                          document: Document,
                          interaction_type: str,
                          relevance_score: Optional[float] = None,
                          metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Record a user interaction for training data generation.
        
        Args:
            query: The search query
            document: The document that was interacted with
            interaction_type: Type of interaction (click, dwell, rating, etc.)
            relevance_score: Optional explicit relevance score
            metadata: Additional metadata about the interaction
        """
        # Infer relevance score if not provided
        if relevance_score is None:
            relevance_score = self._infer_relevance_from_interaction(interaction_type, metadata or {})
        
        # Create interaction record
        interaction = QueryDocumentPair(
            query=query,
            document=document,
            relevance_score=relevance_score,
            interaction_type=interaction_type,
            timestamp=time.time(),
            metadata=metadata or {}
        )
        
        # Store interaction
        self.interactions.append(interaction)
        self.query_interactions[query].append(interaction)
        
        # Periodically save interactions
        if len(self.interactions) % 100 == 0:
            self._save_interactions()
        
        logger.debug(f"Recorded interaction: {interaction_type} for query '{query[:50]}...'")
    
    def _infer_relevance_from_interaction(self, interaction_type: str, metadata: Dict[str, Any]) -> float:
        """
        Infer relevance score from interaction type and metadata.
        
        Args:
            interaction_type: Type of user interaction
            metadata: Additional interaction metadata
            
        Returns:
            Inferred relevance score between 0.0 and 1.0
        """
        if interaction_type == "click":
            # Base relevance for clicks
            base_score = 0.5
            
            # Adjust based on dwell time if available
            dwell_time = metadata.get("dwell_time_seconds", 0)
            if dwell_time > 30:
                base_score += 0.3
            elif dwell_time > 10:
                base_score += 0.2
            elif dwell_time < 3:
                base_score -= 0.2
            
            return max(0.0, min(1.0, base_score))
        
        elif interaction_type == "rating":
            # Explicit rating (assume 1-5 scale)
            rating = metadata.get("rating", 3)
            return (rating - 1) / 4.0  # Convert to 0-1 scale
        
        elif interaction_type == "bookmark":
            return 0.8  # High relevance for bookmarks
        
        elif interaction_type == "share":
            return 0.9  # Very high relevance for shares
        
        elif interaction_type == "download":
            return 0.85  # High relevance for downloads
        
        elif interaction_type == "copy":
            return 0.7  # Good relevance for copying content
        
        elif interaction_type == "skip":
            return 0.1  # Low relevance for skips
        
        else:
            return 0.5  # Default neutral relevance
    
    def generate_training_examples(self, 
                                  min_examples: int = 100,
                                  include_synthetic: bool = True) -> List[TrainingExample]:
        """
        Generate training examples from collected interactions.
        
        Args:
            min_examples: Minimum number of examples to generate
            include_synthetic: Whether to include synthetic examples
            
        Returns:
            List of training examples
        """
        examples = []
        
        # Generate examples from user interactions
        interaction_examples = self._generate_from_interactions()
        examples.extend(interaction_examples)
        
        # Generate synthetic examples if needed
        if include_synthetic and len(examples) < min_examples:
            needed = min_examples - len(examples)
            synthetic_examples = self._generate_synthetic_examples(needed)
            examples.extend(synthetic_examples)
        
        # Save training examples
        self._save_training_examples(examples)
        
        logger.info(f"Generated {len(examples)} training examples ({len(interaction_examples)} from interactions)")
        return examples
    
    def _generate_from_interactions(self) -> List[TrainingExample]:
        """Generate training examples from user interactions."""
        examples = []
        
        for query, interactions in self.query_interactions.items():
            if len(interactions) < self.min_interactions_per_query:
                continue
            
            # Separate positive and negative examples
            positive_docs = []
            negative_docs = []
            relevance_scores = {}
            
            for interaction in interactions:
                doc_id = interaction.document.metadata.get("id", f"doc_{hash(interaction.document.content)}")
                relevance_scores[doc_id] = interaction.relevance_score
                
                if interaction.relevance_score >= self.relevance_threshold:
                    positive_docs.append(interaction.document)
                else:
                    negative_docs.append(interaction.document)
            
            # Only create example if we have both positive and negative examples
            if positive_docs and negative_docs:
                example = TrainingExample(
                    query=query,
                    positive_docs=positive_docs,
                    negative_docs=negative_docs,
                    relevance_scores=relevance_scores,
                    source="user_interaction"
                )
                examples.append(example)
        
        return examples
    
    def _generate_synthetic_examples(self, num_examples: int) -> List[TrainingExample]:
        """Generate synthetic training examples."""
        synthetic_examples = []
        
        # Use existing interactions as templates
        if not self.interactions:
            logger.warning("No interactions available for synthetic example generation")
            return synthetic_examples
        
        for _ in range(num_examples):
            # Sample a random interaction as base
            base_interaction = random.choice(self.interactions)
            
            # Create variations of the query
            synthetic_query = self._create_query_variation(base_interaction.query)
            
            # Use the same document as positive
            positive_docs = [base_interaction.document]
            
            # Sample random documents as negatives
            negative_docs = self._sample_negative_documents(base_interaction.document)
            
            if negative_docs:
                relevance_scores = {
                    f"doc_{hash(base_interaction.document.content)}": 0.8,  # Positive
                }
                for i, neg_doc in enumerate(negative_docs):
                    relevance_scores[f"doc_{hash(neg_doc.content)}"] = 0.1 + (i * 0.05)  # Negatives
                
                example = TrainingExample(
                    query=synthetic_query,
                    positive_docs=positive_docs,
                    negative_docs=negative_docs,
                    relevance_scores=relevance_scores,
                    source="synthetic"
                )
                synthetic_examples.append(example)
        
        return synthetic_examples
    
    def _create_query_variation(self, original_query: str) -> str:
        """Create a variation of the original query."""
        # Simple variations: add synonyms, rephrase, etc.
        variations = [
            f"How to {original_query.lower()}",
            f"What is {original_query.lower()}",
            f"Explain {original_query.lower()}",
            f"{original_query} guide",
            f"{original_query} tutorial",
            f"{original_query} documentation",
        ]
        
        return random.choice(variations)
    
    def _sample_negative_documents(self, positive_doc: Document, num_negatives: int = 3) -> List[Document]:
        """Sample negative documents for training."""
        # For now, create simple negative examples
        # In practice, you'd sample from your document corpus
        negatives = []
        
        # Create variations that are clearly not relevant
        negative_contents = [
            "This document is about a completely different topic than the query.",
            "Unrelated content that should not match the search query.",
            "Random text that has no relevance to the user's information need.",
        ]
        
        for i, content in enumerate(negative_contents[:num_negatives]):
            neg_doc = Document(
                content=content,
                metadata={"id": f"synthetic_negative_{i}", "type": "synthetic"}
            )
            negatives.append(neg_doc)
        
        return negatives
    
    def _save_interactions(self) -> None:
        """Save interactions to disk."""
        interactions_file = self.data_dir / "interactions.jsonl"
        
        with open(interactions_file, "w") as f:
            for interaction in self.interactions:
                interaction_dict = {
                    "query": interaction.query,
                    "document_content": interaction.document.content,
                    "document_metadata": interaction.document.metadata,
                    "relevance_score": interaction.relevance_score,
                    "interaction_type": interaction.interaction_type,
                    "timestamp": interaction.timestamp,
                    "metadata": interaction.metadata
                }
                f.write(json.dumps(interaction_dict) + "\n")
    
    def _load_existing_interactions(self) -> None:
        """Load existing interactions from disk."""
        interactions_file = self.data_dir / "interactions.jsonl"
        
        if not interactions_file.exists():
            return
        
        try:
            with open(interactions_file, "r") as f:
                for line in f:
                    data = json.loads(line.strip())
                    
                    document = Document(
                        content=data["document_content"],
                        metadata=data["document_metadata"]
                    )
                    
                    interaction = QueryDocumentPair(
                        query=data["query"],
                        document=document,
                        relevance_score=data["relevance_score"],
                        interaction_type=data["interaction_type"],
                        timestamp=data["timestamp"],
                        metadata=data["metadata"]
                    )
                    
                    self.interactions.append(interaction)
                    self.query_interactions[interaction.query].append(interaction)
        
        except Exception as e:
            logger.warning(f"Failed to load existing interactions: {e}")
    
    def _save_training_examples(self, examples: List[TrainingExample]) -> None:
        """Save training examples to disk."""
        examples_file = self.data_dir / f"training_examples_{int(time.time())}.json"
        
        examples_data = []
        for example in examples:
            example_dict = {
                "query": example.query,
                "positive_docs": [
                    {"content": doc.content, "metadata": doc.metadata}
                    for doc in example.positive_docs
                ],
                "negative_docs": [
                    {"content": doc.content, "metadata": doc.metadata}
                    for doc in example.negative_docs
                ],
                "relevance_scores": example.relevance_scores,
                "source": example.source
            }
            examples_data.append(example_dict)
        
        with open(examples_file, "w") as f:
            json.dump(examples_data, f, indent=2)
        
        logger.info(f"Saved {len(examples)} training examples to {examples_file}")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about collected training data.
        
        Returns:
            Dictionary with training data statistics
        """
        interaction_types = defaultdict(int)
        for interaction in self.interactions:
            interaction_types[interaction.interaction_type] += 1
        
        return {
            "total_interactions": len(self.interactions),
            "unique_queries": len(self.query_interactions),
            "avg_interactions_per_query": len(self.interactions) / max(1, len(self.query_interactions)),
            "interaction_types": dict(interaction_types),
            "data_dir": str(self.data_dir),
            "min_interactions_per_query": self.min_interactions_per_query,
            "relevance_threshold": self.relevance_threshold
        }