"""
Chain-of-Thought Reasoning Engine for Complex Technical Queries.

This module provides structured reasoning capabilities for complex technical
questions that require multi-step analysis and implementation guidance.
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import re

from .prompt_templates import QueryType, PromptTemplate


class ReasoningStep(Enum):
    """Types of reasoning steps in chain-of-thought."""
    ANALYSIS = "analysis"
    DECOMPOSITION = "decomposition"
    SYNTHESIS = "synthesis"
    VALIDATION = "validation"
    IMPLEMENTATION = "implementation"


@dataclass
class ChainStep:
    """Represents a single step in chain-of-thought reasoning."""
    step_type: ReasoningStep
    description: str
    prompt_addition: str
    requires_context: bool = True


class ChainOfThoughtEngine:
    """
    Engine for generating chain-of-thought reasoning prompts for complex technical queries.
    
    Features:
    - Multi-step reasoning for complex implementations
    - Context-aware step generation
    - Query type specific reasoning chains
    - Validation and error checking steps
    """
    
    def __init__(self):
        """Initialize the chain-of-thought engine."""
        self.reasoning_chains = self._initialize_reasoning_chains()
    
    def _initialize_reasoning_chains(self) -> Dict[QueryType, List[ChainStep]]:
        """Initialize reasoning chains for different query types."""
        return {
            QueryType.IMPLEMENTATION: [
                ChainStep(
                    step_type=ReasoningStep.ANALYSIS,
                    description="Analyze the implementation requirements",
                    prompt_addition="""
First, let me analyze what needs to be implemented:
1. What is the specific goal or functionality required?
2. What are the key components or modules involved?
3. Are there any hardware or software constraints mentioned?"""
                ),
                ChainStep(
                    step_type=ReasoningStep.DECOMPOSITION,
                    description="Break down into implementation steps",
                    prompt_addition="""
Next, let me break this down into logical implementation steps:
1. What are the prerequisites and dependencies?
2. What is the logical sequence of implementation?
3. Which steps are critical and which are optional?"""
                ),
                ChainStep(
                    step_type=ReasoningStep.SYNTHESIS,
                    description="Synthesize the complete solution",
                    prompt_addition="""
Now I'll synthesize the complete solution:
1. How do the individual steps connect together?
2. What code examples or configurations are needed?
3. What are the key integration points?"""
                ),
                ChainStep(
                    step_type=ReasoningStep.VALIDATION,
                    description="Consider validation and error handling",
                    prompt_addition="""
Finally, let me consider validation and potential issues:
1. How can we verify the implementation works?
2. What are common pitfalls or error conditions?
3. What debugging or troubleshooting steps are important?"""
                )
            ],
            
            QueryType.COMPARISON: [
                ChainStep(
                    step_type=ReasoningStep.ANALYSIS,
                    description="Analyze items being compared",
                    prompt_addition="""
Let me start by analyzing what's being compared:
1. What are the specific items or concepts being compared?
2. What aspects or dimensions are relevant for comparison?
3. What context or use case should guide the comparison?"""
                ),
                ChainStep(
                    step_type=ReasoningStep.DECOMPOSITION,
                    description="Break down comparison criteria",
                    prompt_addition="""
Next, let me identify the key comparison criteria:
1. What are the technical specifications or features to compare?
2. What are the performance characteristics?
3. What are the practical considerations (cost, complexity, etc.)?"""
                ),
                ChainStep(
                    step_type=ReasoningStep.SYNTHESIS,
                    description="Synthesize comparison results",
                    prompt_addition="""
Now I'll synthesize the comparison:
1. How do the items compare on each criterion?
2. What are the key trade-offs and differences?
3. What recommendations can be made for different scenarios?"""
                )
            ],
            
            QueryType.TROUBLESHOOTING: [
                ChainStep(
                    step_type=ReasoningStep.ANALYSIS,
                    description="Analyze the problem",
                    prompt_addition="""
Let me start by analyzing the problem:
1. What are the specific symptoms or error conditions?
2. What system or component is affected?
3. What was the expected vs actual behavior?"""
                ),
                ChainStep(
                    step_type=ReasoningStep.DECOMPOSITION,
                    description="Identify potential root causes",
                    prompt_addition="""
Next, let me identify potential root causes:
1. What are the most likely causes based on the symptoms?
2. What system components could be involved?
3. What external factors might contribute to the issue?"""
                ),
                ChainStep(
                    step_type=ReasoningStep.VALIDATION,
                    description="Develop diagnostic approach",
                    prompt_addition="""
Now I'll develop a diagnostic approach:
1. What tests or checks can isolate the root cause?
2. What is the recommended sequence of diagnostic steps?
3. How can we verify the fix once implemented?"""
                )
            ],
            
            QueryType.HARDWARE_CONSTRAINT: [
                ChainStep(
                    step_type=ReasoningStep.ANALYSIS,
                    description="Analyze hardware requirements",
                    prompt_addition="""
Let me analyze the hardware requirements:
1. What are the specific hardware resources needed?
2. What are the performance requirements?
3. What are the power and size constraints?"""
                ),
                ChainStep(
                    step_type=ReasoningStep.DECOMPOSITION,
                    description="Break down resource utilization",
                    prompt_addition="""
Next, let me break down resource utilization:
1. How much memory (RAM/Flash) is required?
2. What are the processing requirements (CPU/DSP)?
3. What I/O and peripheral requirements exist?"""
                ),
                ChainStep(
                    step_type=ReasoningStep.SYNTHESIS,
                    description="Evaluate feasibility and alternatives",
                    prompt_addition="""
Now I'll evaluate feasibility:
1. Can the requirements be met with the available hardware?
2. What optimizations might be needed?
3. What are alternative approaches if constraints are exceeded?"""
                )
            ]
        }
    
    def generate_chain_of_thought_prompt(
        self,
        query: str,
        query_type: QueryType,
        context: str,
        base_template: PromptTemplate
    ) -> Dict[str, str]:
        """
        Generate a chain-of-thought enhanced prompt.
        
        Args:
            query: User's question
            query_type: Type of query
            context: Retrieved context
            base_template: Base prompt template
            
        Returns:
            Enhanced prompt with chain-of-thought reasoning
        """
        # Get reasoning chain for query type
        reasoning_chain = self.reasoning_chains.get(query_type, [])
        
        if not reasoning_chain:
            # Fall back to generic reasoning for unsupported types
            reasoning_chain = self._generate_generic_reasoning_chain(query)
        
        # Build chain-of-thought prompt
        cot_prompt = self._build_cot_prompt(reasoning_chain, query, context)
        
        # Enhance system prompt
        enhanced_system = base_template.system_prompt + """

CHAIN-OF-THOUGHT REASONING: You will approach this question using structured reasoning.
Work through each step methodically before providing your final answer.
Show your reasoning process clearly, then provide a comprehensive final answer."""
        
        # Enhance user prompt
        enhanced_user = f"""{base_template.context_format.format(context=context)}

{base_template.query_format.format(query=query)}

{cot_prompt}

{base_template.answer_guidelines}

After working through your reasoning, provide your final answer in the requested format."""
        
        return {
            "system": enhanced_system,
            "user": enhanced_user
        }
    
    def _build_cot_prompt(
        self,
        reasoning_chain: List[ChainStep],
        query: str,
        context: str
    ) -> str:
        """
        Build the chain-of-thought prompt section.
        
        Args:
            reasoning_chain: List of reasoning steps
            query: User's question
            context: Retrieved context
            
        Returns:
            Chain-of-thought prompt text
        """
        cot_sections = [
            "REASONING PROCESS:",
            "Work through this step-by-step using the following reasoning framework:",
            ""
        ]
        
        for i, step in enumerate(reasoning_chain, 1):
            cot_sections.append(f"Step {i}: {step.description}")
            cot_sections.append(step.prompt_addition)
            cot_sections.append("")
        
        cot_sections.extend([
            "STRUCTURED REASONING:",
            "Now work through each step above, referencing the provided context where relevant.",
            "Use [chunk_X] citations for your reasoning at each step.",
            ""
        ])
        
        return "\n".join(cot_sections)
    
    def _generate_generic_reasoning_chain(self, query: str) -> List[ChainStep]:
        """
        Generate a generic reasoning chain for unsupported query types.
        
        Args:
            query: User's question
            
        Returns:
            List of generic reasoning steps
        """
        # Analyze query complexity to determine appropriate steps
        complexity_indicators = {
            "multi_part": ["and", "also", "additionally", "furthermore"],
            "causal": ["why", "because", "cause", "reason"],
            "conditional": ["if", "when", "unless", "provided that"],
            "comparative": ["better", "worse", "compare", "versus", "vs"]
        }
        
        query_lower = query.lower()
        steps = []
        
        # Always start with analysis
        steps.append(ChainStep(
            step_type=ReasoningStep.ANALYSIS,
            description="Analyze the question",
            prompt_addition="""
Let me start by analyzing the question:
1. What is the core question being asked?
2. What context or domain knowledge is needed?
3. Are there multiple parts to this question?"""
        ))
        
        # Add decomposition for complex queries
        if any(indicator in query_lower for indicators in complexity_indicators.values() for indicator in indicators):
            steps.append(ChainStep(
                step_type=ReasoningStep.DECOMPOSITION,
                description="Break down the question",
                prompt_addition="""
Let me break this down into components:
1. What are the key concepts or elements involved?
2. How do these elements relate to each other?
3. What information do I need to address each part?"""
            ))
        
        # Always end with synthesis
        steps.append(ChainStep(
            step_type=ReasoningStep.SYNTHESIS,
            description="Synthesize the answer",
            prompt_addition="""
Now I'll synthesize a comprehensive answer:
1. How do all the pieces fit together?
2. What is the most complete and accurate response?
3. Are there any important caveats or limitations?"""
        ))
        
        return steps
    
    def create_reasoning_validation_prompt(
        self,
        query: str,
        proposed_answer: str,
        context: str
    ) -> str:
        """
        Create a prompt for validating chain-of-thought reasoning.
        
        Args:
            query: Original query
            proposed_answer: Generated answer to validate
            context: Context used for the answer
            
        Returns:
            Validation prompt
        """
        return f"""
REASONING VALIDATION TASK:

Original Query: {query}

Proposed Answer: {proposed_answer}

Context Used: {context}

Please validate the reasoning in the proposed answer by checking:

1. LOGICAL CONSISTENCY:
   - Are the reasoning steps logically connected?
   - Are there any contradictions or gaps in logic?
   - Does the conclusion follow from the premises?

2. FACTUAL ACCURACY:
   - Are the facts and technical details correct?
   - Are the citations appropriate and accurate?
   - Is the information consistent with the provided context?

3. COMPLETENESS:
   - Does the answer address all parts of the question?
   - Are important considerations or caveats mentioned?
   - Is the level of detail appropriate for the question?

4. CLARITY:
   - Is the reasoning easy to follow?
   - Are technical terms used correctly?
   - Is the structure logical and well-organized?

Provide your validation assessment with specific feedback on any issues found.
"""
    
    def extract_reasoning_steps(self, cot_response: str) -> List[Dict[str, str]]:
        """
        Extract reasoning steps from a chain-of-thought response.
        
        Args:
            cot_response: Response containing chain-of-thought reasoning
            
        Returns:
            List of extracted reasoning steps
        """
        steps = []
        
        # Look for step patterns
        step_patterns = [
            r"Step \d+:?\s*(.+?)(?=Step \d+|$)",
            r"First,?\s*(.+?)(?=Next,?|Second,?|Then,?|Finally,?|$)",
            r"Next,?\s*(.+?)(?=Then,?|Finally,?|Now,?|$)",
            r"Then,?\s*(.+?)(?=Finally,?|Now,?|$)",
            r"Finally,?\s*(.+?)(?=\n\n|$)"
        ]
        
        for pattern in step_patterns:
            matches = re.findall(pattern, cot_response, re.DOTALL | re.IGNORECASE)
            for match in matches:
                if match.strip():
                    steps.append({
                        "step_text": match.strip(),
                        "pattern": pattern
                    })
        
        return steps
    
    def evaluate_reasoning_quality(self, reasoning_steps: List[Dict[str, str]]) -> Dict[str, float]:
        """
        Evaluate the quality of chain-of-thought reasoning.
        
        Args:
            reasoning_steps: List of reasoning steps
            
        Returns:
            Dictionary of quality metrics
        """
        if not reasoning_steps:
            return {"overall_quality": 0.0, "step_count": 0}
        
        # Evaluate different aspects
        metrics = {
            "step_count": len(reasoning_steps),
            "logical_flow": self._evaluate_logical_flow(reasoning_steps),
            "technical_depth": self._evaluate_technical_depth(reasoning_steps),
            "citation_usage": self._evaluate_citation_usage(reasoning_steps),
            "completeness": self._evaluate_completeness(reasoning_steps)
        }
        
        # Calculate overall quality
        quality_weights = {
            "logical_flow": 0.3,
            "technical_depth": 0.3,
            "citation_usage": 0.2,
            "completeness": 0.2
        }
        
        overall_quality = sum(
            metrics[key] * quality_weights[key]
            for key in quality_weights
        )
        
        metrics["overall_quality"] = overall_quality
        
        return metrics
    
    def _evaluate_logical_flow(self, steps: List[Dict[str, str]]) -> float:
        """Evaluate logical flow between reasoning steps."""
        if len(steps) < 2:
            return 0.5
        
        # Check for logical connectors
        connectors = ["therefore", "thus", "because", "since", "as a result", "consequently"]
        connector_count = 0
        
        for step in steps:
            step_text = step["step_text"].lower()
            if any(connector in step_text for connector in connectors):
                connector_count += 1
        
        return min(connector_count / len(steps), 1.0)
    
    def _evaluate_technical_depth(self, steps: List[Dict[str, str]]) -> float:
        """Evaluate technical depth of reasoning."""
        technical_terms = [
            "implementation", "architecture", "algorithm", "protocol", "specification",
            "optimization", "configuration", "register", "memory", "hardware",
            "software", "system", "component", "module", "interface"
        ]
        
        total_terms = 0
        total_words = 0
        
        for step in steps:
            words = step["step_text"].lower().split()
            total_words += len(words)
            
            for term in technical_terms:
                total_terms += words.count(term)
        
        return min(total_terms / max(total_words, 1) * 100, 1.0)
    
    def _evaluate_citation_usage(self, steps: List[Dict[str, str]]) -> float:
        """Evaluate citation usage in reasoning."""
        citation_pattern = r'\[chunk_\d+\]'
        total_citations = 0
        
        for step in steps:
            citations = re.findall(citation_pattern, step["step_text"])
            total_citations += len(citations)
        
        # Good reasoning should have at least one citation per step
        return min(total_citations / len(steps), 1.0)
    
    def _evaluate_completeness(self, steps: List[Dict[str, str]]) -> float:
        """Evaluate completeness of reasoning."""
        # Check for key reasoning elements
        completeness_indicators = [
            "analysis", "consider", "examine", "evaluate",
            "conclusion", "summary", "result", "therefore",
            "requirement", "constraint", "limitation", "important"
        ]
        
        indicator_count = 0
        for step in steps:
            step_text = step["step_text"].lower()
            for indicator in completeness_indicators:
                if indicator in step_text:
                    indicator_count += 1
                    break
        
        return indicator_count / len(steps)


# Example usage
if __name__ == "__main__":
    # Initialize engine
    cot_engine = ChainOfThoughtEngine()
    
    # Example implementation query
    query = "How do I implement a real-time task scheduler in FreeRTOS with priority inheritance?"
    query_type = QueryType.IMPLEMENTATION
    context = "FreeRTOS supports priority-based scheduling with optional priority inheritance..."
    
    # Create a basic template
    base_template = PromptTemplate(
        system_prompt="You are a technical assistant.",
        context_format="Context: {context}",
        query_format="Question: {query}",
        answer_guidelines="Provide a structured answer."
    )
    
    # Generate chain-of-thought prompt
    cot_prompt = cot_engine.generate_chain_of_thought_prompt(
        query=query,
        query_type=query_type,
        context=context,
        base_template=base_template
    )
    
    print("Chain-of-Thought Enhanced Prompt:")
    print("=" * 50)
    print("System:", cot_prompt["system"][:200], "...")
    print("User:", cot_prompt["user"][:300], "...")
    print("=" * 50)
    
    # Example reasoning evaluation
    example_response = """
    Step 1: Let me analyze the requirements
    FreeRTOS provides priority-based scheduling [chunk_1]...
    
    Step 2: Breaking down the implementation
    Priority inheritance requires mutex implementation [chunk_2]...
    
    Step 3: Synthesizing the solution
    Therefore, we need to configure priority inheritance in FreeRTOS [chunk_3]...
    """
    
    steps = cot_engine.extract_reasoning_steps(example_response)
    quality = cot_engine.evaluate_reasoning_quality(steps)
    
    print(f"Reasoning Quality: {quality}")