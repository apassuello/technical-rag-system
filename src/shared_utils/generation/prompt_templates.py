"""
Prompt templates optimized for technical documentation Q&A.

This module provides specialized prompt templates for different types of
technical queries, with a focus on embedded systems and AI documentation.
"""

from enum import Enum
from typing import Dict, List, Optional
from dataclasses import dataclass


class QueryType(Enum):
    """Types of technical queries."""
    DEFINITION = "definition"
    IMPLEMENTATION = "implementation"
    COMPARISON = "comparison"
    TROUBLESHOOTING = "troubleshooting"
    SPECIFICATION = "specification"
    CODE_EXAMPLE = "code_example"
    HARDWARE_CONSTRAINT = "hardware_constraint"
    GENERAL = "general"


@dataclass
class PromptTemplate:
    """Represents a prompt template with its components."""
    system_prompt: str
    context_format: str
    query_format: str
    answer_guidelines: str
    few_shot_examples: Optional[List[str]] = None


class TechnicalPromptTemplates:
    """
    Collection of prompt templates optimized for technical documentation.
    
    Features:
    - Domain-specific templates for embedded systems and AI
    - Structured output formats
    - Citation requirements
    - Technical accuracy emphasis
    """
    
    @staticmethod
    def get_base_system_prompt() -> str:
        """Get the base system prompt for technical documentation."""
        return """You are an expert technical documentation assistant specializing in embedded systems, 
RISC-V architecture, RTOS, and embedded AI/ML. Your role is to provide accurate, detailed 
technical answers based strictly on the provided context.

Key responsibilities:
1. Answer questions using ONLY information from the provided context
2. Include precise citations using [chunk_X] notation for every claim
3. Maintain technical accuracy and use correct terminology
4. Format code snippets and technical specifications properly
5. Clearly state when information is not available in the context
6. Consider hardware constraints and embedded system limitations when relevant

Write naturally and conversationally. Avoid repetitive phrases and numbered lists unless specifically requested. Never make up information. If the context doesn't contain the answer, say so explicitly."""

    @staticmethod
    def get_definition_template() -> PromptTemplate:
        """Template for definition/explanation queries."""
        return PromptTemplate(
            system_prompt=TechnicalPromptTemplates.get_base_system_prompt() + """
            
For definition queries, focus on:
- Clear, concise technical definitions
- Related concepts and terminology
- Technical context and applications
- Any acronym expansions""",
            
            context_format="""Technical Documentation Context:
{context}""",
            
            query_format="""Define or explain: {query}

Provide a comprehensive technical definition with proper citations.""",
            
            answer_guidelines="""Provide a clear, comprehensive answer that directly addresses the question. Include relevant technical details and cite your sources using [chunk_X] notation. Make your response natural and conversational while maintaining technical accuracy.""",
            
            few_shot_examples=[
                """Q: What is RISC-V?
A: RISC-V is an open-source instruction set architecture (ISA) based on established reduced instruction set computing (RISC) principles [chunk_1]. Unlike proprietary ISAs, RISC-V is freely available under open-source licenses, allowing anyone to implement RISC-V processors without licensing fees [chunk_2]. The architecture supports 32-bit, 64-bit, and 128-bit address spaces, with a modular design that includes base integer instruction sets and optional extensions [chunk_3]. RISC-V stands for "RISC-Five" referring to the fifth generation of RISC architecture developed at UC Berkeley.""",
                
                """Q: What is FreeRTOS?
A: FreeRTOS is a real-time operating system kernel for embedded devices that provides multitasking capabilities for microcontrollers and small microprocessors [chunk_1]. It implements a preemptive scheduler with priority-based task scheduling, ensuring deterministic real-time behavior [chunk_2]. FreeRTOS includes core features like task management, semaphores, queues, and memory management while maintaining a small footprint typically under 10KB [chunk_3]. The "Free" in FreeRTOS refers to both its open-source license and the fact that it's free of charge for commercial use."""
            ]
        )
    
    @staticmethod
    def get_implementation_template() -> PromptTemplate:
        """Template for implementation/how-to queries."""
        return PromptTemplate(
            system_prompt=TechnicalPromptTemplates.get_base_system_prompt() + """
            
For implementation queries, focus on:
- Step-by-step instructions
- Required components or dependencies
- Code examples with proper formatting
- Hardware/software requirements
- Common pitfalls or considerations""",
            
            context_format="""Implementation Documentation:
{context}""",
            
            query_format="""Implementation question: {query}

Provide detailed implementation guidance with code examples where available.""",
            
            answer_guidelines="""Structure your answer as:
1. Overview of the implementation approach [chunk_X]
2. Prerequisites and requirements [chunk_Y]
3. Step-by-step implementation:
   - Step 1: Description [chunk_Z]
   - Step 2: Description [chunk_W]
4. Code example (if available):
```language
// Code here
```
5. Important considerations or warnings""",
            
            few_shot_examples=[
                """Q: How do I configure GPIO pins for output in RISC-V?
A: GPIO configuration for output requires setting the pin direction and initial value through memory-mapped registers [chunk_1]. First, identify the GPIO base address for your specific RISC-V implementation (commonly 0x10060000 for SiFive cores) [chunk_2]. 

Steps:
1. Set pin direction to output by writing to GPIO_OUTPUT_EN register [chunk_3]
2. Configure initial output value using GPIO_OUTPUT_VAL register [chunk_4]

```c
#define GPIO_BASE     0x10060000
#define GPIO_OUTPUT_EN (GPIO_BASE + 0x08)
#define GPIO_OUTPUT_VAL (GPIO_BASE + 0x0C)

// Configure pin 5 as output
volatile uint32_t *gpio_en = (uint32_t*)GPIO_OUTPUT_EN;
volatile uint32_t *gpio_val = (uint32_t*)GPIO_OUTPUT_VAL;

*gpio_en |= (1 << 5);   // Enable output on pin 5
*gpio_val |= (1 << 5);  // Set pin 5 high
```

Important: Always check your board's documentation for the correct GPIO base address and pin mapping [chunk_5].""",
                
                """Q: How to implement a basic timer interrupt in RISC-V?
A: Timer interrupts in RISC-V use the machine timer (mtime) and timer compare (mtimecmp) registers for precise timing control [chunk_1]. The implementation requires configuring the timer hardware, setting up the interrupt handler, and enabling machine timer interrupts [chunk_2].

Prerequisites:
- RISC-V processor with timer support
- Access to machine-level CSRs
- Understanding of memory-mapped timer registers [chunk_3]

Implementation steps:
1. Set up timer compare value in mtimecmp register [chunk_4]
2. Enable machine timer interrupt in mie CSR [chunk_5]
3. Configure interrupt handler in mtvec CSR [chunk_6]

```c
#define MTIME_BASE    0x0200bff8
#define MTIMECMP_BASE 0x02004000

void setup_timer_interrupt(uint64_t interval) {
    uint64_t *mtime = (uint64_t*)MTIME_BASE;
    uint64_t *mtimecmp = (uint64_t*)MTIMECMP_BASE;
    
    // Set next interrupt time
    *mtimecmp = *mtime + interval;
    
    // Enable machine timer interrupt
    asm volatile ("csrs mie, %0" : : "r"(0x80));
    
    // Enable global interrupts
    asm volatile ("csrs mstatus, %0" : : "r"(0x8));
}
```

Critical considerations: Timer registers are 64-bit and must be accessed atomically on 32-bit systems [chunk_7]."""
            ]
        )
    
    @staticmethod
    def get_comparison_template() -> PromptTemplate:
        """Template for comparison queries."""
        return PromptTemplate(
            system_prompt=TechnicalPromptTemplates.get_base_system_prompt() + """
            
For comparison queries, focus on:
- Clear distinction between compared items
- Technical specifications and differences
- Use cases for each option
- Performance or resource implications
- Recommendations based on context""",
            
            context_format="""Technical Comparison Context:
{context}""",
            
            query_format="""Compare: {query}

Provide a detailed technical comparison with clear distinctions.""",
            
            answer_guidelines="""Structure your answer as:
1. Overview of items being compared [chunk_X]
2. Key differences:
   - Feature A: Item1 vs Item2 [chunk_Y]
   - Feature B: Item1 vs Item2 [chunk_Z]
3. Technical specifications comparison
4. Use case recommendations
5. Performance/resource considerations"""
        )
    
    @staticmethod
    def get_specification_template() -> PromptTemplate:
        """Template for specification/parameter queries."""
        return PromptTemplate(
            system_prompt=TechnicalPromptTemplates.get_base_system_prompt() + """
            
For specification queries, focus on:
- Exact technical specifications
- Parameter ranges and limits
- Units and measurements
- Compliance with standards
- Version-specific information""",
            
            context_format="""Technical Specifications:
{context}""",
            
            query_format="""Specification query: {query}

Provide precise technical specifications with all relevant parameters.""",
            
            answer_guidelines="""Structure your answer as:
1. Specification overview [chunk_X]
2. Detailed parameters:
   - Parameter 1: value (unit) [chunk_Y]
   - Parameter 2: value (unit) [chunk_Z]
3. Operating conditions or constraints
4. Compliance/standards information
5. Version or variant notes"""
        )
    
    @staticmethod
    def get_code_example_template() -> PromptTemplate:
        """Template for code example queries."""
        return PromptTemplate(
            system_prompt=TechnicalPromptTemplates.get_base_system_prompt() + """
            
For code example queries, focus on:
- Complete, runnable code examples
- Proper syntax highlighting
- Clear comments and documentation
- Error handling
- Best practices for embedded systems""",
            
            context_format="""Code Examples and Documentation:
{context}""",
            
            query_format="""Code example request: {query}

Provide working code examples with explanations.""",
            
            answer_guidelines="""Structure your answer as:
1. Purpose and overview [chunk_X]
2. Required includes/imports [chunk_Y]
3. Complete code example:
```c
// Or appropriate language
#include <necessary_headers.h>

// Function or code implementation
```
4. Key points explained [chunk_Z]
5. Common variations or modifications"""
        )
    
    @staticmethod
    def get_hardware_constraint_template() -> PromptTemplate:
        """Template for hardware constraint queries."""
        return PromptTemplate(
            system_prompt=TechnicalPromptTemplates.get_base_system_prompt() + """
            
For hardware constraint queries, focus on:
- Memory requirements (RAM, Flash)
- Processing power needs (MIPS, frequency)
- Power consumption
- I/O requirements
- Real-time constraints
- Temperature/environmental limits""",
            
            context_format="""Hardware Specifications and Constraints:
{context}""",
            
            query_format="""Hardware constraint question: {query}

Analyze feasibility and constraints for embedded deployment.""",
            
            answer_guidelines="""Structure your answer as:
1. Hardware requirements summary [chunk_X]
2. Detailed constraints:
   - Memory: RAM/Flash requirements [chunk_Y]
   - Processing: CPU/frequency needs [chunk_Z]
   - Power: Consumption estimates [chunk_W]
3. Feasibility assessment
4. Optimization suggestions
5. Alternative approaches if constraints are exceeded"""
        )
    
    @staticmethod
    def get_troubleshooting_template() -> PromptTemplate:
        """Template for troubleshooting queries."""
        return PromptTemplate(
            system_prompt=TechnicalPromptTemplates.get_base_system_prompt() + """
            
For troubleshooting queries, focus on:
- Common error causes
- Diagnostic steps
- Solution procedures
- Preventive measures
- Debug techniques for embedded systems""",
            
            context_format="""Troubleshooting Documentation:
{context}""",
            
            query_format="""Troubleshooting issue: {query}

Provide diagnostic steps and solutions.""",
            
            answer_guidelines="""Structure your answer as:
1. Problem identification [chunk_X]
2. Common causes:
   - Cause 1: Description [chunk_Y]
   - Cause 2: Description [chunk_Z]
3. Diagnostic steps:
   - Step 1: Check... [chunk_W]
   - Step 2: Verify... [chunk_V]
4. Solutions for each cause
5. Prevention recommendations"""
        )
    
    @staticmethod
    def get_general_template() -> PromptTemplate:
        """Default template for general queries."""
        return PromptTemplate(
            system_prompt=TechnicalPromptTemplates.get_base_system_prompt(),
            
            context_format="""Technical Documentation:
{context}""",
            
            query_format="""Question: {query}

Provide a comprehensive technical answer based on the documentation.""",
            
            answer_guidelines="""Provide a clear, comprehensive answer that directly addresses the question. Include relevant technical details and cite your sources using [chunk_X] notation. Write naturally and conversationally while maintaining technical accuracy. Acknowledge any limitations in available information."""
        )
    
    @staticmethod
    def detect_query_type(query: str) -> QueryType:
        """
        Detect the type of query based on keywords and patterns.
        
        Args:
            query: User's question
            
        Returns:
            Detected QueryType
        """
        query_lower = query.lower()
        
        # Definition keywords
        if any(keyword in query_lower for keyword in [
            "what is", "what are", "define", "definition", "meaning of", "explain what"
        ]):
            return QueryType.DEFINITION
        
        # Implementation keywords
        if any(keyword in query_lower for keyword in [
            "how to", "how do i", "implement", "setup", "configure", "install"
        ]):
            return QueryType.IMPLEMENTATION
        
        # Comparison keywords
        if any(keyword in query_lower for keyword in [
            "difference between", "compare", "vs", "versus", "better than", "which is"
        ]):
            return QueryType.COMPARISON
        
        # Specification keywords
        if any(keyword in query_lower for keyword in [
            "specification", "specs", "parameters", "limits", "range", "maximum", "minimum"
        ]):
            return QueryType.SPECIFICATION
        
        # Code example keywords
        if any(keyword in query_lower for keyword in [
            "example", "code", "snippet", "sample", "demo", "show me"
        ]):
            return QueryType.CODE_EXAMPLE
        
        # Hardware constraint keywords
        if any(keyword in query_lower for keyword in [
            "memory", "ram", "flash", "mcu", "constraint", "fit on", "run on", "power consumption"
        ]):
            return QueryType.HARDWARE_CONSTRAINT
        
        # Troubleshooting keywords
        if any(keyword in query_lower for keyword in [
            "error", "problem", "issue", "debug", "troubleshoot", "fix", "solve", "not working"
        ]):
            return QueryType.TROUBLESHOOTING
        
        return QueryType.GENERAL
    
    @staticmethod
    def get_template_for_query(query: str) -> PromptTemplate:
        """
        Get the appropriate template based on query type.
        
        Args:
            query: User's question
            
        Returns:
            Appropriate PromptTemplate
        """
        query_type = TechnicalPromptTemplates.detect_query_type(query)
        
        template_map = {
            QueryType.DEFINITION: TechnicalPromptTemplates.get_definition_template,
            QueryType.IMPLEMENTATION: TechnicalPromptTemplates.get_implementation_template,
            QueryType.COMPARISON: TechnicalPromptTemplates.get_comparison_template,
            QueryType.SPECIFICATION: TechnicalPromptTemplates.get_specification_template,
            QueryType.CODE_EXAMPLE: TechnicalPromptTemplates.get_code_example_template,
            QueryType.HARDWARE_CONSTRAINT: TechnicalPromptTemplates.get_hardware_constraint_template,
            QueryType.TROUBLESHOOTING: TechnicalPromptTemplates.get_troubleshooting_template,
            QueryType.GENERAL: TechnicalPromptTemplates.get_general_template
        }
        
        return template_map[query_type]()
    
    @staticmethod
    def format_prompt_with_template(
        query: str,
        context: str,
        template: Optional[PromptTemplate] = None,
        include_few_shot: bool = True
    ) -> Dict[str, str]:
        """
        Format a complete prompt using the appropriate template.
        
        Args:
            query: User's question
            context: Retrieved context chunks
            template: Optional specific template (auto-detected if None)
            include_few_shot: Whether to include few-shot examples
            
        Returns:
            Dict with 'system' and 'user' prompts
        """
        if template is None:
            template = TechnicalPromptTemplates.get_template_for_query(query)
        
        # Format the context
        formatted_context = template.context_format.format(context=context)
        
        # Format the query
        formatted_query = template.query_format.format(query=query)
        
        # Build user prompt with optional few-shot examples
        user_prompt_parts = []
        
        # Add few-shot examples if available and requested
        if include_few_shot and template.few_shot_examples:
            user_prompt_parts.append("Here are some examples of how to answer similar questions:")
            user_prompt_parts.append("\n\n".join(template.few_shot_examples))
            user_prompt_parts.append("\nNow answer the following question using the same format:")
        
        user_prompt_parts.extend([
            formatted_context,
            formatted_query,
            template.answer_guidelines
        ])
        
        user_prompt = "\n\n".join(user_prompt_parts)
        
        return {
            "system": template.system_prompt,
            "user": user_prompt
        }


# Example usage and testing
if __name__ == "__main__":
    # Test query type detection
    test_queries = [
        "What is RISC-V?",
        "How do I implement a timer interrupt?",
        "What's the difference between FreeRTOS and Zephyr?",
        "What are the memory specifications for STM32F4?",
        "Show me an example of GPIO configuration",
        "Can this model run on an MCU with 256KB RAM?",
        "Debug error: undefined reference to main"
    ]
    
    for query in test_queries:
        query_type = TechnicalPromptTemplates.detect_query_type(query)
        print(f"Query: '{query}' -> Type: {query_type.value}")
    
    # Example prompt formatting
    example_context = "RISC-V is an open instruction set architecture..."
    example_query = "What is RISC-V?"
    
    formatted = TechnicalPromptTemplates.format_prompt_with_template(
        query=example_query,
        context=example_context
    )
    
    print("\nFormatted prompt example:")
    print("System:", formatted["system"][:100], "...")
    print("User:", formatted["user"][:200], "...")