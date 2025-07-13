"""
Entity extraction for technical documents in Epic 2 Week 2.

This module provides entity extraction capabilities for RISC-V technical documents,
using spaCy for natural language processing and custom patterns for technical terms.
"""

import logging
import time
from typing import List, Dict, Any, Optional, Set, Tuple
import re
from dataclasses import dataclass

try:
    import spacy
    from spacy.matcher import Matcher
    from spacy.tokens import Doc, Span
    SPACY_AVAILABLE = True
except ImportError:
    spacy = None
    Span = None
    Doc = None
    Matcher = None
    SPACY_AVAILABLE = False

from src.core.interfaces import Document
from .config.graph_config import EntityExtractionConfig

logger = logging.getLogger(__name__)


@dataclass
class Entity:
    """Represents an extracted entity with metadata."""
    text: str
    label: str
    start_pos: int
    end_pos: int
    confidence: float
    document_id: str
    context: str = ""
    
    def __hash__(self) -> int:
        return hash((self.text.lower(), self.label, self.document_id))
    
    def __eq__(self, other) -> bool:
        if not isinstance(other, Entity):
            return False
        return (
            self.text.lower() == other.text.lower() and
            self.label == other.label and
            self.document_id == other.document_id
        )


class EntityExtractionError(Exception):
    """Raised when entity extraction operations fail."""
    pass


class EntityExtractor:
    """
    Entity extractor for RISC-V technical documents.
    
    This class uses spaCy for natural language processing and custom patterns
    to identify technical entities in RISC-V documentation, including:
    - Technical concepts (TECH)
    - Protocols and standards (PROTOCOL)
    - Architectures and implementations (ARCH)
    - Extensions and specifications (EXTENSION)
    
    The extractor is optimized for technical documentation and provides
    high-accuracy entity recognition with configurable confidence thresholds.
    """
    
    def __init__(self, config: EntityExtractionConfig):
        """
        Initialize the entity extractor.
        
        Args:
            config: Entity extraction configuration
        """
        self.config = config
        self.nlp = None
        self.matcher = None
        self.custom_patterns = self._get_risc_v_patterns()
        self.stats = {
            "documents_processed": 0,
            "entities_extracted": 0,
            "processing_time": 0.0,
            "model_load_time": 0.0
        }
        
        # Initialize spaCy model
        self._initialize_model()
    
    def _initialize_model(self) -> None:
        """Initialize spaCy model and custom patterns."""
        if spacy is None:
            raise EntityExtractionError("spaCy is not installed. Install with: pip install spacy")
        
        start_time = time.time()
        
        try:
            # Load spaCy model
            self.nlp = spacy.load(self.config.model)
            logger.info(f"Loaded spaCy model: {self.config.model}")
            
            # Initialize matcher for custom patterns
            self.matcher = Matcher(self.nlp.vocab)
            self._add_custom_patterns()
            
            self.stats["model_load_time"] = time.time() - start_time
            logger.info(f"Entity extractor initialized in {self.stats['model_load_time']:.3f}s")
            
        except OSError as e:
            if "Can't find model" in str(e):
                raise EntityExtractionError(
                    f"spaCy model '{self.config.model}' not found. "
                    f"Install with: python -m spacy download {self.config.model}"
                ) from e
            else:
                raise EntityExtractionError(f"Failed to load spaCy model: {str(e)}") from e
        except Exception as e:
            raise EntityExtractionError(f"Failed to initialize entity extractor: {str(e)}") from e
    
    def _get_risc_v_patterns(self) -> Dict[str, List[List[Dict[str, Any]]]]:
        """
        Get RISC-V specific entity patterns.
        
        Returns:
            Dictionary mapping entity types to spaCy patterns
        """
        patterns = {
            "TECH": [
                # RISC-V technical terms
                [{"LOWER": "risc-v"}],
                [{"LOWER": "riscv"}],
                [{"LOWER": "isa"}],
                [{"LOWER": "instruction"}, {"LOWER": "set"}],
                [{"LOWER": "instruction"}, {"LOWER": "set"}, {"LOWER": "architecture"}],
                [{"LOWER": "vector"}, {"LOWER": "extension"}],
                [{"LOWER": "atomic"}, {"LOWER": "operations"}],
                [{"LOWER": "privilege"}, {"LOWER": "levels"}],
                [{"LOWER": "csr"}, {"LOWER": "registers"}],
                [{"LOWER": "control"}, {"LOWER": "status"}, {"LOWER": "register"}],
                [{"LOWER": "pipeline"}],
                [{"LOWER": "microarchitecture"}],
                [{"LOWER": "cache"}, {"LOWER": "coherence"}],
                [{"LOWER": "memory"}, {"LOWER": "management"}],
                [{"LOWER": "virtual"}, {"LOWER": "memory"}],
                [{"LOWER": "page"}, {"LOWER": "table"}],
                [{"LOWER": "interrupt"}, {"LOWER": "handling"}],
                [{"LOWER": "exception"}, {"LOWER": "handling"}],
                [{"LOWER": "floating"}, {"LOWER": "point"}],
                [{"LOWER": "compressed"}, {"LOWER": "instructions"}],
                [{"LOWER": "bit"}, {"LOWER": "manipulation"}],
            ],
            "PROTOCOL": [
                # Communication protocols and standards
                [{"LOWER": "axi"}],
                [{"LOWER": "ahb"}],
                [{"LOWER": "apb"}],
                [{"LOWER": "amba"}],
                [{"LOWER": "tilelink"}],
                [{"LOWER": "debug"}, {"LOWER": "transport"}, {"LOWER": "module"}],
                [{"LOWER": "jtag"}],
                [{"LOWER": "openocd"}],
                [{"LOWER": "gdb"}],
                [{"LOWER": "trace"}, {"LOWER": "encoder"}],
                [{"LOWER": "performance"}, {"LOWER": "counters"}],
                [{"LOWER": "pmp"}],  # Physical Memory Protection
                [{"LOWER": "pma"}],  # Physical Memory Attributes
            ],
            "ARCH": [
                # Architecture implementations and designs
                [{"LOWER": "rv32i"}],
                [{"LOWER": "rv64i"}],
                [{"LOWER": "rv32gc"}],
                [{"LOWER": "rv64gc"}],
                [{"LOWER": "rv32e"}],
                [{"LOWER": "zicsr"}],
                [{"LOWER": "zifencei"}],
                [{"LOWER": "zmmul"}],
                [{"LOWER": "rocket"}, {"LOWER": "chip"}],
                [{"LOWER": "boom"}],
                [{"LOWER": "ariane"}],
                [{"LOWER": "cva6"}],
                [{"LOWER": "ibex"}],
                [{"LOWER": "vexriscv"}],
                [{"LOWER": "picorv32"}],
                [{"LOWER": "syntacore"}],
                [{"LOWER": "scr1"}],
                [{"LOWER": "sifive"}],
                [{"LOWER": "berkeley"}],
                [{"LOWER": "lowrisc"}],
            ],
            "EXTENSION": [
                # RISC-V extensions
                [{"LOWER": "m"}, {"LOWER": "extension"}],
                [{"LOWER": "a"}, {"LOWER": "extension"}],
                [{"LOWER": "f"}, {"LOWER": "extension"}],
                [{"LOWER": "d"}, {"LOWER": "extension"}],
                [{"LOWER": "c"}, {"LOWER": "extension"}],
                [{"LOWER": "v"}, {"LOWER": "extension"}],
                [{"LOWER": "h"}, {"LOWER": "extension"}],
                [{"LOWER": "s"}, {"LOWER": "extension"}],
                [{"LOWER": "n"}, {"LOWER": "extension"}],
                [{"LOWER": "p"}, {"LOWER": "extension"}],
                [{"LOWER": "b"}, {"LOWER": "extension"}],
                [{"LOWER": "k"}, {"LOWER": "extension"}],
                [{"LOWER": "j"}, {"LOWER": "extension"}],
                [{"LOWER": "zb"}],
                [{"LOWER": "zk"}],
                [{"LOWER": "zf"}],
                [{"TEXT": {"REGEX": r"^rv\d+[a-z]+$"}}],  # RV32I, RV64GC, etc.
            ]
        }
        
        # Add user-defined custom patterns
        if self.config.custom_patterns:
            for entity_type, custom_patterns in self.config.custom_patterns.items():
                if entity_type in patterns:
                    # Convert string patterns to spaCy patterns
                    for pattern_text in custom_patterns:
                        pattern = [{"LOWER": token.lower()} for token in pattern_text.split()]
                        patterns[entity_type].append(pattern)
                else:
                    patterns[entity_type] = []
                    for pattern_text in custom_patterns:
                        pattern = [{"LOWER": token.lower()} for token in pattern_text.split()]
                        patterns[entity_type].append(pattern)
        
        return patterns
    
    def _add_custom_patterns(self) -> None:
        """Add custom patterns to the spaCy matcher."""
        try:
            for entity_type, patterns in self.custom_patterns.items():
                if entity_type in self.config.entity_types:
                    for i, pattern in enumerate(patterns):
                        pattern_id = f"{entity_type}_{i}"
                        self.matcher.add(pattern_id, [pattern])
            
            logger.info(f"Added {len(self.custom_patterns)} custom pattern sets")
            
        except Exception as e:
            logger.warning(f"Failed to add some custom patterns: {str(e)}")
    
    def extract_entities(self, documents: List[Document]) -> Dict[str, List[Entity]]:
        """
        Extract entities from a list of documents.
        
        Args:
            documents: List of documents to process
            
        Returns:
            Dictionary mapping document IDs to extracted entities
        """
        if not documents:
            return {}
        
        start_time = time.time()
        
        try:
            all_entities = {}
            
            # Process documents in batches for efficiency
            batch_size = self.config.batch_size
            for i in range(0, len(documents), batch_size):
                batch = documents[i:i + batch_size]
                batch_entities = self._extract_batch(batch)
                all_entities.update(batch_entities)
            
            # Update statistics
            processing_time = time.time() - start_time
            self.stats["documents_processed"] += len(documents)
            self.stats["processing_time"] += processing_time
            self.stats["entities_extracted"] += sum(len(entities) for entities in all_entities.values())
            
            logger.info(
                f"Extracted entities from {len(documents)} documents in {processing_time:.3f}s "
                f"({len(documents)/processing_time:.1f} docs/sec)"
            )
            
            return all_entities
            
        except Exception as e:
            logger.error(f"Entity extraction failed: {str(e)}")
            raise EntityExtractionError(f"Failed to extract entities: {str(e)}") from e
    
    def _extract_batch(self, documents: List[Document]) -> Dict[str, List[Entity]]:
        """
        Extract entities from a batch of documents.
        
        Args:
            documents: Batch of documents to process
            
        Returns:
            Dictionary mapping document IDs to extracted entities
        """
        batch_entities = {}
        
        for document in documents:
            try:
                entities = self._extract_from_document(document)
                doc_id = document.metadata.get("id", "unknown")
                batch_entities[doc_id] = entities
                
            except Exception as e:
                doc_id = document.metadata.get("id", "unknown")
                logger.warning(f"Failed to extract entities from document {doc_id}: {str(e)}")
                batch_entities[doc_id] = []
        
        return batch_entities
    
    def _extract_from_document(self, document: Document) -> List[Entity]:
        """
        Extract entities from a single document.
        
        Args:
            document: Document to process
            
        Returns:
            List of extracted entities
        """
        if not document.content or not document.content.strip():
            return []
        
        # Process text with spaCy
        doc = self.nlp(document.content)
        
        entities = []
        
        # Extract named entities from spaCy NER
        if hasattr(doc, 'ents'):
            for ent in doc.ents:
                if self._is_relevant_entity(ent):
                    entity = Entity(
                        text=ent.text.strip(),
                        label=self._normalize_label(ent.label_),
                        start_pos=ent.start_char,
                        end_pos=ent.end_char,
                        confidence=self._calculate_confidence(ent),
                        document_id=document.metadata.get("id", "unknown"),
                        context=self._extract_context(doc, ent)
                    )
                    entities.append(entity)
        
        # Extract custom pattern matches
        matches = self.matcher(doc)
        for match_id, start, end in matches:
            span = doc[start:end]
            label = self._get_label_from_match_id(self.nlp.vocab.strings[match_id])
            
            if label and self._meets_confidence_threshold(span):
                entity = Entity(
                    text=span.text.strip(),
                    label=label,
                    start_pos=span.start_char,
                    end_pos=span.end_char,
                    confidence=self._calculate_pattern_confidence(span),
                    document_id=document.metadata.get("id", "unknown"),
                    context=self._extract_context(doc, span)
                )
                entities.append(entity)
        
        # Remove duplicates and apply confidence filtering
        entities = self._deduplicate_entities(entities)
        entities = [e for e in entities if e.confidence >= self.config.confidence_threshold]
        
        return entities
    
    def _is_relevant_entity(self, ent: Any) -> bool:
        """Check if a spaCy entity is relevant for technical extraction."""
        # Map spaCy labels to our entity types
        relevant_labels = {
            "ORG": "TECH",      # Organizations (often tech companies)
            "PRODUCT": "TECH",  # Products (often technical products)
            "MISC": "TECH",     # Miscellaneous (often technical terms)
            "GPE": "ARCH",      # Geopolitical entities (sometimes architectures)
        }
        
        return ent.label_ in relevant_labels
    
    def _normalize_label(self, spacy_label: str) -> str:
        """Normalize spaCy labels to our entity types."""
        label_mapping = {
            "ORG": "TECH",
            "PRODUCT": "TECH", 
            "MISC": "TECH",
            "GPE": "ARCH",
        }
        
        return label_mapping.get(spacy_label, "TECH")
    
    def _calculate_confidence(self, ent: Any) -> float:
        """Calculate confidence score for a spaCy entity."""
        # Base confidence on entity properties
        base_confidence = 0.7
        
        # Boost confidence for longer entities (more specific)
        length_bonus = min(len(ent.text.split()) * 0.1, 0.2)
        
        # Boost confidence for uppercase entities (likely acronyms)
        if ent.text.isupper() and len(ent.text) > 1:
            acronym_bonus = 0.1
        else:
            acronym_bonus = 0.0
        
        # Check if it matches our patterns
        pattern_bonus = 0.1 if self._matches_technical_pattern(ent.text) else 0.0
        
        return min(base_confidence + length_bonus + acronym_bonus + pattern_bonus, 1.0)
    
    def _calculate_pattern_confidence(self, span: Any) -> float:
        """Calculate confidence score for pattern matches."""
        # Pattern matches have higher base confidence
        base_confidence = 0.8
        
        # Exact technical term matches get highest confidence
        if self._is_exact_technical_term(span.text):
            return 0.95
        
        return base_confidence
    
    def _matches_technical_pattern(self, text: str) -> bool:
        """Check if text matches common technical patterns."""
        technical_patterns = [
            r'^rv\d+[a-z]*$',  # RV32I, RV64GC, etc.
            r'^[a-z]+\d+$',    # Technical IDs
            r'^[A-Z]{2,}$',    # Acronyms
        ]
        
        for pattern in technical_patterns:
            if re.match(pattern, text, re.IGNORECASE):
                return True
        
        return False
    
    def _is_exact_technical_term(self, text: str) -> bool:
        """Check if text is an exact technical term."""
        exact_terms = {
            "risc-v", "riscv", "isa", "csr", "mmu", "alu", "fpu",
            "rv32i", "rv64i", "rv32gc", "rv64gc", "axi", "ahb", "apb"
        }
        
        return text.lower() in exact_terms
    
    def _get_label_from_match_id(self, match_id: str) -> Optional[str]:
        """Extract entity label from matcher ID."""
        try:
            return match_id.split('_')[0]
        except (IndexError, AttributeError):
            return None
    
    def _meets_confidence_threshold(self, span: Any) -> bool:
        """Check if span meets confidence threshold."""
        # Simple heuristics for pattern matches
        if len(span.text) < 2:
            return False
        
        if span.text.isdigit():
            return False
        
        return True
    
    def _extract_context(self, doc: Any, entity: Any) -> str:
        """Extract surrounding context for an entity."""
        context_window = 50  # Characters on each side
        
        start = max(0, entity.start_char - context_window)
        end = min(len(doc.text), entity.end_char + context_window)
        
        return doc.text[start:end].strip()
    
    def _deduplicate_entities(self, entities: List[Entity]) -> List[Entity]:
        """Remove duplicate entities, keeping the highest confidence ones."""
        seen = {}
        
        for entity in entities:
            key = (entity.text.lower(), entity.label, entity.document_id)
            
            if key not in seen or entity.confidence > seen[key].confidence:
                seen[key] = entity
        
        return list(seen.values())
    
    def get_entity_types(self) -> List[str]:
        """Get list of supported entity types."""
        return self.config.entity_types
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get extraction statistics.
        
        Returns:
            Dictionary with extraction statistics
        """
        stats = self.stats.copy()
        
        if stats["documents_processed"] > 0:
            stats["avg_entities_per_document"] = stats["entities_extracted"] / stats["documents_processed"]
            stats["avg_processing_time_per_document"] = stats["processing_time"] / stats["documents_processed"]
        else:
            stats["avg_entities_per_document"] = 0.0
            stats["avg_processing_time_per_document"] = 0.0
        
        return stats
    
    def reset_statistics(self) -> None:
        """Reset extraction statistics."""
        self.stats = {
            "documents_processed": 0,
            "entities_extracted": 0,
            "processing_time": 0.0,
            "model_load_time": self.stats["model_load_time"]  # Keep model load time
        }