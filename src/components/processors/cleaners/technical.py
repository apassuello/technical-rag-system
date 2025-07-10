"""
Technical Content Cleaner Implementation.

This cleaner implements text normalization and cleaning specifically
optimized for technical documentation. It preserves important technical
content while removing artifacts and normalizing formatting.

Key Features:
- Technical content preservation (code blocks, equations, specifications)
- Whitespace normalization without losing structure
- Artifact removal (headers, footers, navigation elements)
- PII detection placeholder for future implementation
- Configurable cleaning strategies

Architecture Notes:
- Direct implementation (no adapter pattern) as per MASTER-ARCHITECTURE.md
- Focuses on technical documentation requirements
- Preserves formatting critical for technical understanding
"""

import re
from typing import List, Dict, Any, Tuple
from pathlib import Path
import sys

# Add project paths for imports
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.append(str(project_root))

from ..base import ContentCleaner, ConfigurableComponent, QualityAssessment


class TechnicalContentCleaner(ContentCleaner, ConfigurableComponent, QualityAssessment):
    """
    Technical documentation content cleaner.
    
    This cleaner is specifically designed for technical documentation,
    preserving important technical content while removing artifacts
    and normalizing formatting for better retrieval and generation.
    
    Features:
    - Preserve code blocks, equations, and technical specifications
    - Remove common document artifacts (headers, footers, TOCs)
    - Normalize whitespace while preserving structure
    - Handle technical formatting (bullet points, numbered lists)
    - Basic PII detection (placeholder for future enhancement)
    
    Configuration Options:
    - normalize_whitespace: Enable whitespace normalization (default: True)
    - remove_artifacts: Remove document artifacts (default: True)
    - preserve_code_blocks: Preserve code block formatting (default: True)
    - preserve_equations: Preserve mathematical equations (default: True)
    - detect_pii: Enable PII detection (default: False)
    - pii_action: Action for PII ('redact', 'remove', 'flag') (default: 'flag')
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the technical content cleaner.
        
        Args:
            config: Configuration dictionary with cleaner settings
        """
        # Default configuration
        self.config = {
            'normalize_whitespace': True,
            'remove_artifacts': True,
            'preserve_code_blocks': True,
            'preserve_equations': True,
            'detect_pii': False,
            'pii_action': 'flag',
            'min_line_length': 10,
            'max_consecutive_newlines': 2,
            'preserve_technical_formatting': True
        }
        
        # Apply provided configuration
        if config:
            self.config.update(config)
        
        # Cleaning metrics
        self.metrics = {
            'texts_processed': 0,
            'artifacts_removed': 0,
            'pii_detected': 0,
            'bytes_cleaned': 0,
            'cleaning_operations': {
                'whitespace_normalized': 0,
                'artifacts_removed': 0,
                'code_blocks_preserved': 0,
                'equations_preserved': 0
            }
        }
        
        # Quality assessment factors
        self.quality_factors = [
            'technical_content_preservation',
            'formatting_consistency',
            'artifact_removal',
            'content_completeness',
            'readability_improvement'
        ]
        
        # Compile regex patterns for performance
        self._compile_patterns()
    
    def clean(self, text: str) -> str:
        """
        Clean and normalize text content.
        
        Args:
            text: Input text to be cleaned
            
        Returns:
            Cleaned text with normalized formatting
            
        Raises:
            ValueError: If text is None or invalid
        """
        if text is None:
            raise ValueError("Text cannot be None")
        
        if not isinstance(text, str):
            raise ValueError("Text must be a string")
        
        if not text.strip():
            return ""
        
        original_length = len(text)
        cleaned_text = text
        
        # Step 1: Preserve important technical content
        protected_content = self._protect_technical_content(cleaned_text)
        
        # Step 2: Remove document artifacts
        if self.config['remove_artifacts']:
            cleaned_text = self._remove_artifacts(protected_content['text'])
            self.metrics['cleaning_operations']['artifacts_removed'] += 1
        
        # Step 3: Normalize whitespace
        if self.config['normalize_whitespace']:
            cleaned_text = self._normalize_whitespace(cleaned_text)
            self.metrics['cleaning_operations']['whitespace_normalized'] += 1
        
        # Step 4: Restore protected content
        cleaned_text = self._restore_protected_content(cleaned_text, protected_content)
        
        # Update metrics
        self.metrics['texts_processed'] += 1
        self.metrics['bytes_cleaned'] += abs(len(cleaned_text) - original_length)
        
        return cleaned_text
    
    def normalize(self, text: str) -> str:
        """
        Normalize text formatting and structure.
        
        Args:
            text: Input text to normalize
            
        Returns:
            Normalized text with consistent formatting
        """
        if not text:
            return ""
        
        normalized = text
        
        # Normalize line endings
        normalized = re.sub(r'\r\n|\r', '\n', normalized)
        
        # Normalize quotation marks
        normalized = re.sub(r'[""„"«»]', '"', normalized)
        normalized = re.sub(r"[''‚'‹›]", "'", normalized)
        
        # Normalize dashes
        normalized = re.sub(r'[–—]', '-', normalized)
        
        # Normalize ellipsis
        normalized = re.sub(r'\.{3,}', '...', normalized)
        
        # Normalize multiple spaces (but preserve intentional spacing)
        normalized = re.sub(r' {2,}', ' ', normalized)
        
        # Normalize bullet points
        normalized = re.sub(r'[•·‧▪▫]', '•', normalized)
        
        return normalized
    
    def remove_pii(self, text: str) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Remove personally identifiable information from text.
        
        Args:
            text: Input text potentially containing PII
            
        Returns:
            Tuple of (cleaned_text, detected_pii_entities)
            
        Note:
            This is a basic implementation that can be enhanced
            with more sophisticated PII detection in the future.
        """
        if not self.config['detect_pii']:
            return text, []
        
        detected_pii = []
        cleaned_text = text
        
        # Basic PII patterns
        pii_patterns = {
            'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            'phone': r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
            'ssn': r'\b\d{3}-\d{2}-\d{4}\b',
            'credit_card': r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',
            'ip_address': r'\b(?:\d{1,3}\.){3}\d{1,3}\b'
        }
        
        for pii_type, pattern in pii_patterns.items():
            matches = re.finditer(pattern, cleaned_text)
            for match in matches:
                detected_pii.append({
                    'type': pii_type,
                    'value': match.group(),
                    'start': match.start(),
                    'end': match.end()
                })
                
                # Apply PII action
                if self.config['pii_action'] == 'redact':
                    cleaned_text = cleaned_text.replace(match.group(), '[REDACTED]')
                elif self.config['pii_action'] == 'remove':
                    cleaned_text = cleaned_text.replace(match.group(), '')
                # 'flag' action just detects without modifying
        
        self.metrics['pii_detected'] += len(detected_pii)
        
        return cleaned_text, detected_pii
    
    def configure(self, config: Dict[str, Any]) -> None:
        """
        Configure the cleaner with provided settings.
        
        Args:
            config: Configuration dictionary
            
        Raises:
            ValueError: If configuration is invalid
        """
        # Validate configuration
        self._validate_config(config)
        
        # Update configuration
        self.config.update(config)
        
        # Recompile patterns if needed
        self._compile_patterns()
    
    def get_config(self) -> Dict[str, Any]:
        """
        Get current configuration.
        
        Returns:
            Current configuration dictionary
        """
        return self.config.copy()
    
    def assess_quality(self, content: str) -> float:
        """
        Assess the quality of cleaned content.
        
        Args:
            content: Content to assess
            
        Returns:
            Quality score between 0.0 and 1.0
        """
        if not content:
            return 0.0
        
        quality_score = 0.0
        
        # Factor 1: Technical content preservation (30% weight)
        tech_score = self._assess_technical_preservation(content)
        quality_score += tech_score * 0.3
        
        # Factor 2: Formatting consistency (25% weight)
        format_score = self._assess_formatting_consistency(content)
        quality_score += format_score * 0.25
        
        # Factor 3: Artifact removal (20% weight)
        artifact_score = self._assess_artifact_removal(content)
        quality_score += artifact_score * 0.2
        
        # Factor 4: Content completeness (15% weight)
        completeness_score = self._assess_content_completeness(content)
        quality_score += completeness_score * 0.15
        
        # Factor 5: Readability improvement (10% weight)
        readability_score = self._assess_readability_improvement(content)
        quality_score += readability_score * 0.1
        
        return min(1.0, quality_score)
    
    def get_quality_factors(self) -> List[str]:
        """
        Get list of quality factors considered.
        
        Returns:
            List of quality factor names
        """
        return self.quality_factors.copy()
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get cleaning metrics.
        
        Returns:
            Dictionary with cleaning metrics and statistics
        """
        return self.metrics.copy()
    
    def _compile_patterns(self) -> None:
        """Compile regex patterns for performance."""
        # Common artifacts to remove
        self.artifact_patterns = [
            # Headers and footers
            r'^\s*page \d+\s*$',
            r'^\s*\d+\s*$',
            r'^\s*chapter \d+\s*$',
            r'^\s*section \d+\s*$',
            
            # Table of contents patterns
            r'^\s*\d+\..*\.\.\.\.\.\d+\s*$',
            r'^\s*contents?\s*$',
            r'^\s*table of contents\s*$',
            
            # Navigation elements
            r'^\s*next\s*$',
            r'^\s*previous\s*$',
            r'^\s*back to top\s*$',
            
            # Copyright and legal
            r'^\s*copyright \d{4}',
            r'^\s*©\s*\d{4}',
            r'^\s*all rights reserved',
            
            # Document metadata
            r'^\s*document id:',
            r'^\s*version:',
            r'^\s*last updated:',
            r'^\s*created:',
        ]
        
        # Compile patterns
        self.compiled_artifact_patterns = [
            re.compile(pattern, re.IGNORECASE | re.MULTILINE) 
            for pattern in self.artifact_patterns
        ]
        
        # Code block patterns
        self.code_block_patterns = [
            re.compile(r'```.*?```', re.DOTALL),
            re.compile(r'`[^`]+`'),
            re.compile(r'^\s{4,}.*$', re.MULTILINE),  # Indented code
            re.compile(r'^\t+.*$', re.MULTILINE),     # Tab-indented code
        ]
        
        # Equation patterns
        self.equation_patterns = [
            re.compile(r'\$\$.*?\$\$', re.DOTALL),
            re.compile(r'\$[^$]+\$'),
            re.compile(r'\\begin\{.*?\}.*?\\end\{.*?\}', re.DOTALL),
        ]
    
    def _protect_technical_content(self, text: str) -> Dict[str, Any]:
        """
        Protect technical content from cleaning operations.
        
        Args:
            text: Input text
            
        Returns:
            Dictionary with protected content and placeholders
        """
        protected = {
            'text': text,
            'code_blocks': [],
            'equations': [],
            'placeholders': {}
        }
        
        placeholder_counter = 0
        
        # Protect code blocks
        if self.config['preserve_code_blocks']:
            for pattern in self.code_block_patterns:
                matches = pattern.finditer(text)
                for match in matches:
                    placeholder = f"__PROTECTED_CODE_{placeholder_counter}__"
                    protected['code_blocks'].append(match.group())
                    protected['placeholders'][placeholder] = match.group()
                    protected['text'] = protected['text'].replace(match.group(), placeholder)
                    placeholder_counter += 1
                    self.metrics['cleaning_operations']['code_blocks_preserved'] += 1
        
        # Protect equations
        if self.config['preserve_equations']:
            for pattern in self.equation_patterns:
                matches = pattern.finditer(protected['text'])
                for match in matches:
                    placeholder = f"__PROTECTED_EQUATION_{placeholder_counter}__"
                    protected['equations'].append(match.group())
                    protected['placeholders'][placeholder] = match.group()
                    protected['text'] = protected['text'].replace(match.group(), placeholder)
                    placeholder_counter += 1
                    self.metrics['cleaning_operations']['equations_preserved'] += 1
        
        return protected
    
    def _remove_artifacts(self, text: str) -> str:
        """
        Remove document artifacts.
        
        Args:
            text: Input text
            
        Returns:
            Text with artifacts removed
        """
        cleaned = text
        artifacts_removed = 0
        
        # Remove common artifacts
        for pattern in self.compiled_artifact_patterns:
            matches = pattern.findall(cleaned)
            artifacts_removed += len(matches)
            cleaned = pattern.sub('', cleaned)
        
        # Remove short lines that are likely artifacts
        lines = cleaned.split('\n')
        cleaned_lines = []
        
        for line in lines:
            line_stripped = line.strip()
            
            # Keep line if it meets criteria
            if (len(line_stripped) >= self.config['min_line_length'] or 
                not line_stripped or  # Keep empty lines for structure
                any(pattern in line_stripped.lower() for pattern in ['algorithm', 'equation', 'figure', 'table'])):
                cleaned_lines.append(line)
            else:
                artifacts_removed += 1
        
        self.metrics['artifacts_removed'] += artifacts_removed
        
        return '\n'.join(cleaned_lines)
    
    def _normalize_whitespace(self, text: str) -> str:
        """
        Normalize whitespace while preserving structure.
        
        Args:
            text: Input text
            
        Returns:
            Text with normalized whitespace
        """
        # Remove trailing whitespace from lines
        text = re.sub(r'[ \t]+$', '', text, flags=re.MULTILINE)
        
        # Normalize multiple consecutive newlines
        max_newlines = self.config['max_consecutive_newlines']
        text = re.sub(f'\n{{{max_newlines+1},}}', '\n' * max_newlines, text)
        
        # Remove leading/trailing whitespace from entire text
        text = text.strip()
        
        return text
    
    def _restore_protected_content(self, text: str, protected: Dict[str, Any]) -> str:
        """
        Restore protected technical content.
        
        Args:
            text: Cleaned text with placeholders
            protected: Protected content dictionary
            
        Returns:
            Text with protected content restored
        """
        restored = text
        
        # Restore all protected content
        for placeholder, original in protected['placeholders'].items():
            restored = restored.replace(placeholder, original)
        
        return restored
    
    def _validate_config(self, config: Dict[str, Any]) -> None:
        """
        Validate configuration parameters.
        
        Args:
            config: Configuration to validate
            
        Raises:
            ValueError: If configuration is invalid
        """
        valid_keys = {
            'normalize_whitespace', 'remove_artifacts', 'preserve_code_blocks',
            'preserve_equations', 'detect_pii', 'pii_action', 'min_line_length',
            'max_consecutive_newlines', 'preserve_technical_formatting'
        }
        
        invalid_keys = set(config.keys()) - valid_keys
        if invalid_keys:
            raise ValueError(f"Invalid configuration keys: {invalid_keys}")
        
        # Validate specific values
        if 'pii_action' in config and config['pii_action'] not in ['redact', 'remove', 'flag']:
            raise ValueError("pii_action must be 'redact', 'remove', or 'flag'")
        
        if 'min_line_length' in config and (not isinstance(config['min_line_length'], int) or config['min_line_length'] < 0):
            raise ValueError("min_line_length must be a non-negative integer")
        
        if 'max_consecutive_newlines' in config and (not isinstance(config['max_consecutive_newlines'], int) or config['max_consecutive_newlines'] < 1):
            raise ValueError("max_consecutive_newlines must be a positive integer")
    
    def _assess_technical_preservation(self, content: str) -> float:
        """
        Assess how well technical content is preserved.
        
        Args:
            content: Content to assess
            
        Returns:
            Technical preservation score (0.0 to 1.0)
        """
        # Look for technical indicators
        technical_indicators = [
            'algorithm', 'function', 'variable', 'parameter', 'return',
            'struct', 'class', 'interface', 'implementation', 'specification',
            'register', 'memory', 'processor', 'instruction', 'operation',
            'equation', 'formula', 'calculation', 'value', 'result'
        ]
        
        content_lower = content.lower()
        found_indicators = sum(1 for indicator in technical_indicators if indicator in content_lower)
        
        return min(1.0, found_indicators / 10.0)
    
    def _assess_formatting_consistency(self, content: str) -> float:
        """
        Assess formatting consistency.
        
        Args:
            content: Content to assess
            
        Returns:
            Formatting consistency score (0.0 to 1.0)
        """
        lines = content.split('\n')
        if not lines:
            return 0.0
        
        # Check for consistent indentation
        indentation_levels = set()
        for line in lines:
            if line.strip():
                leading_spaces = len(line) - len(line.lstrip())
                indentation_levels.add(leading_spaces)
        
        # Consistent indentation suggests good formatting
        consistency_score = 1.0 - min(0.5, len(indentation_levels) / 10.0)
        
        return consistency_score
    
    def _assess_artifact_removal(self, content: str) -> float:
        """
        Assess how well artifacts were removed.
        
        Args:
            content: Content to assess
            
        Returns:
            Artifact removal score (0.0 to 1.0)
        """
        # Look for common artifacts that should be removed
        artifact_indicators = [
            'page ', 'chapter ', 'section ', 'contents', 'copyright',
            'next', 'previous', 'back to top', 'document id', 'version:'
        ]
        
        content_lower = content.lower()
        found_artifacts = sum(1 for indicator in artifact_indicators if indicator in content_lower)
        
        # Fewer artifacts = better score
        return max(0.0, 1.0 - (found_artifacts / 10.0))
    
    def _assess_content_completeness(self, content: str) -> float:
        """
        Assess content completeness.
        
        Args:
            content: Content to assess
            
        Returns:
            Content completeness score (0.0 to 1.0)
        """
        # Check for sentence completeness
        sentences = re.split(r'[.!?]+', content)
        complete_sentences = [s.strip() for s in sentences if len(s.strip()) > 5]
        
        if not sentences:
            return 0.0
        
        completeness_ratio = len(complete_sentences) / len(sentences)
        
        return min(1.0, completeness_ratio)
    
    def _assess_readability_improvement(self, content: str) -> float:
        """
        Assess readability improvement.
        
        Args:
            content: Content to assess
            
        Returns:
            Readability improvement score (0.0 to 1.0)
        """
        # Simple readability metrics
        words = content.split()
        if not words:
            return 0.0
        
        # Check for reasonable word lengths
        avg_word_length = sum(len(word) for word in words) / len(words)
        word_length_score = min(1.0, avg_word_length / 8.0)
        
        # Check for reasonable sentence lengths
        sentences = re.split(r'[.!?]+', content)
        if sentences:
            avg_sentence_length = sum(len(sentence.split()) for sentence in sentences) / len(sentences)
            sentence_length_score = min(1.0, avg_sentence_length / 20.0)
        else:
            sentence_length_score = 0.0
        
        return (word_length_score + sentence_length_score) / 2.0