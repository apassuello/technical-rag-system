"""
Domain Relevance Filter for Epic 1 Phase 1 Implementation

This module implements a 3-tier domain relevance filtering system that determines
whether queries are relevant to RISC-V before expensive processing.

The filter operates as a pre-processing step in the query pipeline:
- High Relevance (0.8-1.0): Clearly RISC-V related → Continue to full processing
- Medium Relevance (0.3-0.7): General architecture → Conservative processing  
- Low Relevance (0.0-0.2): Other domains → Early exit with explanation

Architecture:
- Follows Epic 1 patterns and interfaces
- Integrates with ModularQueryProcessor workflow
- Uses the same DomainRelevanceScorer from add_domain_relevance_scores.py
- Provides clear routing decisions and user feedback
"""

import logging
import re
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Add project paths for imports
project_root = Path(__file__).parent.parent.parent.parent
sys.path.append(str(project_root))

from src.core.interfaces import Answer

logger = logging.getLogger(__name__)


@dataclass
class DomainRelevanceResult:
    """Results from domain relevance analysis."""
    
    query: str
    relevance_score: float
    relevance_tier: str  # high_relevance, medium_relevance, low_relevance
    is_relevant: bool  # True if should continue processing
    reasoning: str
    confidence: float
    processing_time_ms: float
    metadata: Dict[str, Any]


class DomainRelevanceScorer:
    """
    3-tier domain relevance scoring for RISC-V vs general technical queries.
    
    This is the same scorer used in add_domain_relevance_scores.py, extracted
    as a reusable component for the production filter.
    """
    
    def __init__(self) -> None:
        # High relevance indicators - clearly RISC-V specific
        self.high_relevance_keywords: List[str] = [
            'risc-v', 'riscv', 'risc v', 'risc_v',
            'rv32', 'rv64', 'rv128',
            'vector extension', 'rvv', 'risc-v vector',
            'privileged instruction', 'privileged mode',
            'risc-v specification', 'risc-v isa',
            'risc-v assembly', 'risc-v processor',
            'risc-v architecture', 'risc-v implementation',
            'hart', 'risc-v hart',
            'fence instruction', 'fence.i',
            'csr', 'control and status register',
            'mtvec', 'mstatus', 'mcause', 'mtval',
            'satp', 'sstatus', 'scause', 'stval',
        ]
        
        # Clear RISC-V instructions (unambiguous)
        self.riscv_clear_instructions = [
            'lui', 'auipc', 'jal', 'jalr',
            'beq', 'bne', 'blt', 'bge', 'bltu', 'bgeu',
            'lb', 'lh', 'lw', 'ld', 'lbu', 'lhu', 'lwu',
            'sb', 'sh', 'sw', 'sd',
            'addi', 'slti', 'sltiu', 'xori', 'ori', 'andi',
            'slli', 'srli', 'srai', 'slliw', 'srliw', 'sraiw',
            'addw', 'subw', 'sllw', 'srlw', 'sraw',
            'fence', 'fence.i', 'ecall', 'ebreak',
            'csrrw', 'csrrs', 'csrrc', 'csrrwi', 'csrrsi', 'csrrci',
            'mul', 'mulh', 'mulhsu', 'mulhu', 'div', 'divu', 'rem', 'remu',
            'mulw', 'divw', 'divuw', 'remw', 'remuw',
        ]
        
        # Ambiguous instructions (only count with architectural context)
        self.riscv_ambiguous_instructions = [
            'add', 'sub', 'sll', 'slt', 'sltu', 'xor', 'srl', 'sra', 'or', 'and'
        ]
        
        # Medium relevance - general architecture terms
        self.medium_relevance_keywords = [
            'instruction set', 'isa ', ' isa',
            'processor architecture', 'cpu architecture',
            'assembly language', 'assembly programming',
            'instruction format', 'instruction encoding',
            'memory management unit', 'mmu',
            'virtual memory', 'page table',
            'cache coherence', 'cache hierarchy',
            'pipeline', 'out-of-order execution',
            'branch prediction', 'branch predictor',
            'exception handling', 'interrupt handling',
            'system call', 'syscall',
            'privilege level', 'supervisor mode', 'user mode',
            'atomic operation', 'memory ordering',
            'simd', 'vector processing',
            'floating point unit', 'fpu',
        ]
        
        # Low relevance - other technical domains
        self.low_relevance_domains = [
            'web development', 'frontend', 'backend', 'full stack',
            'database', 'sql', 'nosql', 'mysql', 'postgresql', 'mongodb',
            'api', 'rest api', 'graphql', 'microservices',
            'cloud computing', 'aws', 'azure', 'gcp', 'kubernetes',
            'machine learning', 'ai', 'neural network', 'deep learning',
            'blockchain', 'cryptocurrency', 'smart contract',
            'mobile development', 'android', 'ios', 'react native',
            'cybersecurity', 'penetration testing', 'vulnerability',
            'data science', 'data analysis', 'big data',
            'devops', 'ci/cd', 'docker', 'containerization',
            'network security', 'firewall', 'vpn',
            'software testing', 'unit testing', 'integration testing',
        ]
        
        # Compile regex patterns for efficiency
        self.high_patterns = [re.compile(r'\b' + re.escape(kw) + r'\b', re.IGNORECASE) 
                             for kw in self.high_relevance_keywords]
        self.medium_patterns = [re.compile(r'\b' + re.escape(kw) + r'\b', re.IGNORECASE) 
                               for kw in self.medium_relevance_keywords]
        self.low_patterns = [re.compile(r'\b' + re.escape(kw) + r'\b', re.IGNORECASE) 
                            for kw in self.low_relevance_domains]
        self.clear_instruction_patterns = [re.compile(r'\b' + re.escape(inst) + r'\b', re.IGNORECASE) 
                                         for inst in self.riscv_clear_instructions]
        self.ambiguous_instruction_patterns = [re.compile(r'\b' + re.escape(inst) + r'\b', re.IGNORECASE) 
                                             for inst in self.riscv_ambiguous_instructions]
    
    def score_query(self, query_text: str) -> Tuple[float, str, Dict]:
        """
        Score a query for RISC-V domain relevance.
        
        Args:
            query_text: The query string to analyze
            
        Returns:
            Tuple of (score, tier, details)
        """
        query_lower = query_text.lower()
        details = {
            'high_matches': [],
            'medium_matches': [],
            'low_matches': [],
            'instruction_matches': [],
            'reasoning': ''
        }
        
        # Check for high relevance patterns
        high_matches = []
        for pattern, keyword in zip(self.high_patterns, self.high_relevance_keywords):
            if pattern.search(query_text):
                high_matches.append(keyword)
        details['high_matches'] = high_matches
        
        # Check for clear RISC-V instructions
        clear_instruction_matches = []
        for pattern, instruction in zip(self.clear_instruction_patterns, self.riscv_clear_instructions):
            if pattern.search(query_text):
                clear_instruction_matches.append(instruction)
        
        # Check for ambiguous instructions (only count if in architectural context)
        ambiguous_instruction_matches = []
        has_arch_context = any(word in query_lower for word in 
                              ['instruction', 'assembly', 'processor', 'architecture', 'isa', 'risc'])
        
        if has_arch_context:
            for pattern, instruction in zip(self.ambiguous_instruction_patterns, self.riscv_ambiguous_instructions):
                if pattern.search(query_text):
                    ambiguous_instruction_matches.append(instruction)
        
        # Combine instruction matches
        instruction_matches = clear_instruction_matches + ambiguous_instruction_matches
        details['instruction_matches'] = instruction_matches
        
        # Check for medium relevance patterns
        medium_matches = []
        for pattern, keyword in zip(self.medium_patterns, self.medium_relevance_keywords):
            if pattern.search(query_text):
                medium_matches.append(keyword)
        details['medium_matches'] = medium_matches
        
        # Check for low relevance patterns
        low_matches = []
        for pattern, keyword in zip(self.low_patterns, self.low_relevance_domains):
            if pattern.search(query_text):
                low_matches.append(keyword)
        details['low_matches'] = low_matches
        
        # Scoring logic
        if high_matches:
            # Clear RISC-V indicators -> High relevance
            score = 0.9 + min(0.1, len(high_matches) * 0.02)
            tier = "high_relevance"
            details['reasoning'] = f"Clear RISC-V indicators: {', '.join(high_matches[:3])}"
        
        elif instruction_matches and len(instruction_matches) >= 2:
            # Multiple RISC-V instructions -> High relevance
            score = 0.85 + min(0.15, len(instruction_matches) * 0.03)
            tier = "high_relevance"
            details['reasoning'] = f"Multiple RISC-V instructions: {', '.join(instruction_matches[:3])}"
        
        elif instruction_matches and any(arch_word in query_lower for arch_word in ['instruction', 'assembly', 'processor', 'architecture']):
            # Single instruction with architectural context -> High relevance
            score = 0.8 + min(0.1, len(instruction_matches) * 0.05)
            tier = "high_relevance"
            details['reasoning'] = f"RISC-V instruction in architectural context: {instruction_matches[0]}"
        
        elif instruction_matches:
            # Single instruction without clear context -> Medium relevance
            score = 0.5 + min(0.2, len(instruction_matches) * 0.1)
            tier = "medium_relevance"
            details['reasoning'] = f"Possible RISC-V instruction: {instruction_matches[0]}"
        
        elif medium_matches and not low_matches:
            # General architecture terms without conflicting domains -> Medium relevance
            score = 0.4 + min(0.3, len(medium_matches) * 0.1)
            tier = "medium_relevance"
            details['reasoning'] = f"General architecture terms: {', '.join(medium_matches[:2])}"
        
        elif medium_matches and low_matches:
            # Architecture terms but also other domain indicators -> Low relevance
            score = 0.1 + min(0.2, len(medium_matches) * 0.05)
            tier = "low_relevance"
            details['reasoning'] = f"Mixed domains: {', '.join(low_matches[:2])}"
        
        elif low_matches:
            # Clear other technical domains -> Low relevance
            score = 0.05 + min(0.15, len(low_matches) * 0.05)
            tier = "low_relevance"
            details['reasoning'] = f"Other technical domains: {', '.join(low_matches[:2])}"
        
        else:
            # No clear indicators -> Low relevance (default)
            score = 0.1
            tier = "low_relevance"
            details['reasoning'] = "No clear domain indicators"
        
        return score, tier, details


class DomainRelevanceFilter:
    """
    Domain relevance filter for Epic 1 Phase 1 implementation.
    
    This filter implements early domain detection to route queries appropriately:
    - High relevance queries continue to full RISC-V processing pipeline
    - Medium relevance queries use conservative processing with general models
    - Low relevance queries are handled with early exit and clear explanations
    
    The filter follows Epic 1 architectural patterns and integrates seamlessly
    with the existing ModularQueryProcessor workflow.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize domain relevance filter.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self.scorer = DomainRelevanceScorer()
        
        # Thresholds for routing decisions
        self.high_threshold = self.config.get('high_threshold', 0.8)
        self.medium_threshold = self.config.get('medium_threshold', 0.3)
        
        # Performance tracking
        self.analysis_count = 0
        self.total_analysis_time = 0.0
        
        logger.info(f"DomainRelevanceFilter initialized with thresholds: "
                   f"high={self.high_threshold}, medium={self.medium_threshold}")
    
    def analyze_domain_relevance(self, query: str) -> DomainRelevanceResult:
        """
        Analyze query for RISC-V domain relevance.
        
        Args:
            query: User query string
            
        Returns:
            DomainRelevanceResult with scoring and routing decision
        """
        start_time = time.time()
        self.analysis_count += 1
        
        try:
            # Get domain relevance score
            score, tier, details = self.scorer.score_query(query)
            
            # Determine routing decision
            is_relevant = score >= self.medium_threshold
            confidence = self._calculate_confidence(score, tier, details)
            
            # Calculate processing time
            processing_time_ms = (time.time() - start_time) * 1000
            self.total_analysis_time += processing_time_ms
            
            # Create result
            result = DomainRelevanceResult(
                query=query,
                relevance_score=score,
                relevance_tier=tier,
                is_relevant=is_relevant,
                reasoning=details['reasoning'],
                confidence=confidence,
                processing_time_ms=processing_time_ms,
                metadata={
                    'high_matches': details['high_matches'],
                    'medium_matches': details['medium_matches'],
                    'low_matches': details['low_matches'],
                    'instruction_matches': details['instruction_matches'],
                    'filter_version': '1.0',
                    'analysis_count': self.analysis_count
                }
            )
            
            logger.debug(f"Domain analysis: query='{query[:50]}...', "
                        f"score={score:.3f}, tier={tier}, relevant={is_relevant}")
            
            return result
            
        except Exception as e:
            logger.error(f"Domain relevance analysis failed: {e}")
            # Return conservative fallback - allow processing
            return DomainRelevanceResult(
                query=query,
                relevance_score=0.5,
                relevance_tier="medium_relevance",
                is_relevant=True,
                reasoning=f"Analysis error: {str(e)}",
                confidence=0.3,
                processing_time_ms=(time.time() - start_time) * 1000,
                metadata={'error': str(e), 'fallback': True}
            )
    
    def create_refusal_response(self, domain_result: DomainRelevanceResult) -> Answer:
        """
        Create a polite refusal response for out-of-scope queries.
        
        Args:
            domain_result: Domain relevance analysis result
            
        Returns:
            Answer explaining why the query is out-of-scope
        """
        # Determine the user's domain based on the analysis
        user_domain = "general technical"
        if domain_result.metadata.get('low_matches'):
            low_matches = domain_result.metadata['low_matches']
            if any(term in low_matches for term in ['web', 'api', 'database']):
                user_domain = "web development"
            elif any(term in low_matches for term in ['machine learning', 'ai', 'neural']):
                user_domain = "machine learning"
            elif any(term in low_matches for term in ['cloud', 'aws', 'kubernetes']):
                user_domain = "cloud computing"
            elif any(term in low_matches for term in ['blockchain', 'cryptocurrency']):
                user_domain = "blockchain"
        
        response_text = (
            f"I'm specifically designed to help with RISC-V processor architecture questions. "
            f"Your query appears to be about {user_domain}, which is outside my expertise area.\\n\\n"
            f"I can help you with:\\n"
            f"• RISC-V instruction set architecture\\n"
            f"• RISC-V processor implementations\\n"
            f"• RISC-V assembly programming\\n"
            f"• RISC-V vector extensions\\n"
            f"• RISC-V development tools\\n\\n"
            f"For {user_domain} questions, I'd recommend consulting specialized resources "
            f"or documentation for that domain."
        )
        
        return Answer(
            text=response_text,
            confidence=0.95,  # High confidence in the refusal decision
            sources=[],
            metadata={
                'domain_relevance_score': domain_result.relevance_score,
                'domain_relevance_tier': domain_result.relevance_tier,
                'reasoning': domain_result.reasoning,
                'early_exit': True,
                'filter_decision': 'out_of_scope',
                'user_domain': user_domain,
                'processing_time_ms': domain_result.processing_time_ms
            }
        )
    
    def _calculate_confidence(self, score: float, tier: str, details: Dict) -> float:
        """Calculate confidence in the domain relevance decision."""
        base_confidence = 0.7
        
        # Higher confidence for clear indicators
        if tier == "high_relevance" and details['high_matches']:
            base_confidence = 0.95
        elif tier == "low_relevance" and details['low_matches']:
            base_confidence = 0.90
        elif tier == "medium_relevance":
            base_confidence = 0.60  # Lower confidence for borderline cases
        
        # Adjust based on score distance from thresholds
        if score >= 0.8 or score <= 0.2:
            base_confidence = min(0.95, base_confidence + 0.1)
        
        return base_confidence
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics for monitoring."""
        avg_time = self.total_analysis_time / max(self.analysis_count, 1)
        
        return {
            'total_analyses': self.analysis_count,
            'total_time_ms': self.total_analysis_time,
            'average_time_ms': avg_time,
            'high_threshold': self.high_threshold,
            'medium_threshold': self.medium_threshold
        }