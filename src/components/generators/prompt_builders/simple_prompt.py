"""
Simple prompt builder implementation.

This module provides a basic prompt builder that uses straightforward
templates to construct prompts from queries and context documents.

Architecture Notes:
- Direct implementation (no adapter needed)
- Pure prompt construction algorithm
- Configurable templates for different use cases
"""

import logging
from typing import List, Dict, Any, Optional
from textwrap import dedent

from ..base import PromptBuilder, Document, ConfigurableComponent

logger = logging.getLogger(__name__)


class SimplePromptBuilder(PromptBuilder, ConfigurableComponent):
    """
    Simple template-based prompt builder.
    
    Features:
    - Configurable prompt templates
    - Context length management
    - Citation instruction injection
    - Clear role definitions
    
    Configuration:
    - max_context_length: Maximum characters for context (default: 4000)
    - include_instructions: Include detailed instructions (default: True)
    - citation_style: How to format citations (default: "inline")
    """
    
    # Default prompt template
    DEFAULT_TEMPLATE = dedent("""
    You are a helpful assistant answering questions based on the provided context.
    
    Context Documents:
    {context}
    
    Question: {query}
    
    Instructions:
    - Answer based ONLY on the provided context
    - Be concise and direct
    - If the answer is not in the context, say so
    - Include citations to support your answer
    
    Answer:
    """).strip()
    
    # Minimal template without instructions
    MINIMAL_TEMPLATE = dedent("""
    Context: {context}
    
    Question: {query}
    
    Answer based on the context:
    """).strip()
    
    def __init__(self, 
                 max_context_length: int = 4000,
                 include_instructions: bool = True,
                 citation_style: str = "inline",
                 template: Optional[str] = None,
                 config: Optional[Dict[str, Any]] = None):
        """
        Initialize simple prompt builder.
        
        Args:
            max_context_length: Maximum characters for context
            include_instructions: Include detailed instructions
            citation_style: Citation format ("inline", "footnote", "none")
            template: Custom template (uses default if None)
            config: Additional configuration
        """
        # Merge config
        builder_config = {
            'max_context_length': max_context_length,
            'include_instructions': include_instructions,
            'citation_style': citation_style,
            'template': template,
            **(config or {})
        }
        
        super().__init__(builder_config)
        
        # Set configuration
        self.max_context_length = builder_config['max_context_length']
        self.include_instructions = builder_config['include_instructions']
        self.citation_style = builder_config['citation_style']
        
        # Select template
        if builder_config['template']:
            self.template = builder_config['template']
        elif self.include_instructions:
            self.template = self.DEFAULT_TEMPLATE
        else:
            self.template = self.MINIMAL_TEMPLATE
    
    def build_prompt(self, query: str, context: List[Document]) -> str:
        """
        Build a prompt from query and context documents.
        
        Args:
            query: User query string
            context: List of relevant context documents
            
        Returns:
            Formatted prompt string
            
        Raises:
            ValueError: If query is empty or context is invalid
        """
        if not query.strip():
            raise ValueError("Query cannot be empty")
        
        if not context:
            # Handle empty context gracefully
            context_text = "No relevant context documents found."
        else:
            # Format context documents
            context_text = self._format_context(context)
        
        # Build prompt from template
        prompt = self.template.format(
            context=context_text,
            query=query.strip()
        )
        
        # Add citation instructions if needed
        if self.citation_style != "none" and "citation" not in prompt.lower():
            prompt = self._add_citation_instructions(prompt)
        
        logger.debug(f"Built prompt with {len(context)} documents, length: {len(prompt)}")
        
        return prompt
    
    def get_template(self) -> str:
        """Return the prompt template being used."""
        return self.template
    
    def get_builder_info(self) -> Dict[str, Any]:
        """Get information about the prompt builder."""
        return {
            'type': 'simple',
            'builder_class': self.__class__.__name__,
            'max_context_length': self.max_context_length,
            'include_instructions': self.include_instructions,
            'citation_style': self.citation_style,
            'template_length': len(self.template),
            'template_preview': self.template[:100] + '...' if len(self.template) > 100 else self.template
        }
    
    def _format_context(self, documents: List[Document]) -> str:
        """
        Format context documents into a readable string.
        
        Args:
            documents: List of documents
            
        Returns:
            Formatted context string
        """
        formatted_docs = []
        total_length = 0
        
        for i, doc in enumerate(documents, 1):
            # Format document with citation marker
            doc_header = f"[Document {i}]"
            if doc.metadata.get('source'):
                doc_header += f" Source: {doc.metadata['source']}"
            if doc.metadata.get('page') or doc.metadata.get('start_page'):
                page = doc.metadata.get('page') or doc.metadata.get('start_page')
                doc_header += f" (Page {page})"
            
            # Check if adding this document would exceed limit
            doc_text = f"{doc_header}\n{doc.content}\n"
            if total_length + len(doc_text) > self.max_context_length:
                # Truncate or skip
                remaining = self.max_context_length - total_length
                if remaining > 100:  # Only add if we have reasonable space
                    truncated = doc_text[:remaining] + "\n[Truncated...]"
                    formatted_docs.append(truncated)
                break
            
            formatted_docs.append(doc_text)
            total_length += len(doc_text)
        
        return "\n".join(formatted_docs).strip()
    
    def _add_citation_instructions(self, prompt: str) -> str:
        """
        Add citation instructions to the prompt.
        
        Args:
            prompt: Original prompt
            
        Returns:
            Prompt with citation instructions
        """
        citation_instructions = {
            "inline": "\nWhen referencing information, include inline citations like [Document 1].",
            "footnote": "\nInclude footnote-style citations at the end of your answer.",
            "none": ""
        }
        
        instruction = citation_instructions.get(self.citation_style, "")
        if instruction:
            # Add before the final "Answer:" line if present
            if "\nAnswer:" in prompt:
                prompt = prompt.replace("\nAnswer:", f"{instruction}\n\nAnswer:")
            else:
                prompt += instruction
        
        return prompt
    
    def set_template(self, template: str) -> None:
        """
        Set a custom prompt template.
        
        Args:
            template: New template with {context} and {query} placeholders
            
        Raises:
            ValueError: If template is missing required placeholders
        """
        if "{context}" not in template or "{query}" not in template:
            raise ValueError("Template must contain {context} and {query} placeholders")
        
        self.template = template
        self.config['template'] = template
        logger.info("Updated prompt template")