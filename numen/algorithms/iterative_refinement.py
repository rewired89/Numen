"""
Iterative Refinement / Reflection (R*-based).

The model critiques its own work and refines it iteratively.
Used by OpenAI's O1 model with "thinking tokens".

Key insight: Let the LLM be its own skeptical peer reviewer.
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class CritiqueType(Enum):
    """Types of critiques the model can make."""

    LOGICAL_GAP = "logical_gap"
    UNSTATED_ASSUMPTION = "unstated_assumption"
    INCORRECT_STEP = "incorrect_step"
    UNCLEAR_REASONING = "unclear_reasoning"
    MISSING_CASE = "missing_case"
    BOUNDARY_CONDITION = "boundary_condition"


@dataclass
class Critique:
    """A critique of a reasoning step or solution."""

    type: CritiqueType
    step_number: Optional[int]  # Which step is problematic
    description: str
    suggestion: str
    severity: float  # 0.0 to 1.0


@dataclass
class RefinementAttempt:
    """Single refinement iteration."""

    iteration: int
    solution: str
    reasoning_chain: List[str]
    critiques: List[Critique]
    verification_result: Any
    improved: bool = False


class IterativeRefinement:
    """
    Iterative refinement with self-critique.

    Process:
    1. Generate initial solution
    2. Critique own work
    3. Refine based on critique
    4. Verify refinement
    5. Repeat until verified or max iterations
    """

    def __init__(
        self,
        max_iterations: int = 5,
        critique_temperature: float = 0.3,  # Lower temp for critique (more critical)
        refinement_temperature: float = 0.7,  # Higher for refinement (more creative)
    ):
        self.max_iterations = max_iterations
        self.critique_temperature = critique_temperature
        self.refinement_temperature = refinement_temperature

    def solve_with_refinement(
        self,
        problem: str,
        model_generator,
        verifier,
    ) -> Tuple[Optional[str], List[RefinementAttempt]]:
        """
        Solve problem with iterative self-refinement.

        Args:
            problem: Mathematical problem
            model_generator: Function that generates solutions
            verifier: Verification function

        Returns:
            Tuple of (final_solution, refinement_history)
        """
        attempts = []
        current_solution = None
        current_reasoning = []

        for iteration in range(self.max_iterations):
            # Generate or refine solution
            if iteration == 0:
                # Initial generation
                solution, reasoning = self._generate_initial(
                    problem,
                    model_generator,
                )
            else:
                # Refinement based on previous critiques
                solution, reasoning = self._refine_solution(
                    problem,
                    attempts[-1],  # Previous attempt
                    model_generator,
                )

            # Verify
            verification = verifier(solution)

            # Generate self-critique
            critiques = self._generate_critique(
                problem,
                solution,
                reasoning,
                verification,
                model_generator,
            )

            # Record attempt
            attempt = RefinementAttempt(
                iteration=iteration + 1,
                solution=solution,
                reasoning_chain=reasoning,
                critiques=critiques,
                verification_result=verification,
                improved=len(critiques) < len(attempts[-1].critiques) if attempts else False,
            )
            attempts.append(attempt)

            # Check if verified
            if verification.get("verified", False):
                return solution, attempts

            # Check if stuck (no improvement)
            if iteration > 0 and not attempt.improved:
                # Try different approach
                pass

        # Return best attempt even if not verified
        best = max(attempts, key=lambda a: a.verification_result.get("confidence", 0))
        return best.solution, attempts

    def _generate_initial(
        self,
        problem: str,
        model_generator,
    ) -> Tuple[str, List[str]]:
        """Generate initial solution attempt."""

        prompt = f"""
Solve the following mathematical problem step-by-step.

Problem: {problem}

Think carefully and show your work. Be explicit about:
- What assumptions you're making
- Why each step is valid
- Edge cases or boundary conditions

Solution:
"""

        response = model_generator(prompt, temperature=0.7)

        # Parse into solution and reasoning
        solution, reasoning = self._parse_response(response)

        return solution, reasoning

    def _generate_critique(
        self,
        problem: str,
        solution: str,
        reasoning: List[str],
        verification: Dict[str, Any],
        model_generator,
    ) -> List[Critique]:
        """
        Generate self-critique of the solution.

        This is the key: the model critiques its OWN work!
        """

        critique_prompt = f"""
You are a rigorous mathematical reviewer. Critique the following solution.

Problem: {problem}

Proposed Solution: {solution}

Reasoning Steps:
{chr(10).join(f"{i+1}. {step}" for i, step in enumerate(reasoning))}

Verification Result: {verification.get("explanation", "Unknown")}

As a skeptical peer reviewer, identify any:
1. Logical gaps or leaps
2. Unstated assumptions
3. Incorrect steps
4. Missing edge cases
5. Boundary condition errors

Be specific about which step is problematic and why.

Critique:
"""

        critique_response = model_generator(
            critique_prompt,
            temperature=self.critique_temperature,
        )

        # Parse critique into structured format
        critiques = self._parse_critique(critique_response)

        return critiques

    def _refine_solution(
        self,
        problem: str,
        previous_attempt: RefinementAttempt,
        model_generator,
    ) -> Tuple[str, List[str]]:
        """
        Refine solution based on critique.

        This is where the model learns from its mistakes!
        """

        refinement_prompt = f"""
Your previous solution had issues. Refine it based on the critique.

Problem: {problem}

Previous Solution: {previous_attempt.solution}

Previous Reasoning:
{chr(10).join(f"{i+1}. {step}" for i, step in enumerate(previous_attempt.reasoning_chain))}

Critiques:
{chr(10).join(f"- {c.description} (Suggestion: {c.suggestion})" for c in previous_attempt.critiques)}

Verification Error: {previous_attempt.verification_result.get("explanation", "")}

Address each critique and provide a refined solution:
"""

        response = model_generator(
            refinement_prompt,
            temperature=self.refinement_temperature,
        )

        solution, reasoning = self._parse_response(response)

        return solution, reasoning

    def _parse_response(self, response: str) -> Tuple[str, List[str]]:
        """Parse model response into solution and reasoning."""

        # Simple parsing - would be more sophisticated in practice
        lines = response.split('\n')

        reasoning_steps = []
        solution = ""

        for line in lines:
            line = line.strip()
            if line.startswith(('1.', '2.', '3.', 'Step', '-')):
                reasoning_steps.append(line)
            elif "solution" in line.lower() or "answer" in line.lower():
                solution = line

        if not solution and lines:
            solution = lines[-1]  # Last line as solution

        return solution, reasoning_steps

    def _parse_critique(self, critique_text: str) -> List[Critique]:
        """Parse critique text into structured critiques."""

        critiques = []

        # Simple parsing - look for common patterns
        lines = critique_text.split('\n')

        for line in lines:
            line = line.strip()

            # Detect critique type
            if "logical gap" in line.lower() or "leap" in line.lower():
                critique_type = CritiqueType.LOGICAL_GAP
            elif "assumption" in line.lower():
                critique_type = CritiqueType.UNSTATED_ASSUMPTION
            elif "incorrect" in line.lower() or "wrong" in line.lower():
                critique_type = CritiqueType.INCORRECT_STEP
            elif "unclear" in line.lower():
                critique_type = CritiqueType.UNCLEAR_REASONING
            elif "missing" in line.lower() or "edge case" in line.lower():
                critique_type = CritiqueType.MISSING_CASE
            else:
                continue  # Not a critique

            critiques.append(Critique(
                type=critique_type,
                step_number=None,  # Would extract from text
                description=line,
                suggestion="",  # Would extract from text
                severity=0.7,
            ))

        return critiques

    def format_refinement_history(
        self,
        attempts: List[RefinementAttempt],
    ) -> str:
        """Format refinement history for display."""

        output = "## Iterative Refinement History\n\n"

        for attempt in attempts:
            status = "✅ VERIFIED" if attempt.verification_result.get("verified") else "❌ FAILED"

            output += f"### Iteration {attempt.iteration} - {status}\n\n"
            output += f"**Solution:** {attempt.solution}\n\n"

            if attempt.critiques:
                output += "**Self-Critique:**\n"
                for i, critique in enumerate(attempt.critiques, 1):
                    output += f"{i}. [{critique.type.value}] {critique.description}\n"
                output += "\n"

            if attempt.improved:
                output += "✓ **Improved from previous iteration**\n\n"

            output += "---\n\n"

        return output


class ReflectionLoop:
    """
    Reflection-based reasoning (R* algorithm).

    Even more sophisticated than simple refinement:
    - Maintains working memory of attempts
    - Strategically backtracks
    - Learns which strategies work for which problems
    """

    def __init__(self):
        self.refinement = IterativeRefinement()
        self.memory: List[Dict[str, Any]] = []

    def solve_with_reflection(
        self,
        problem: str,
        model_generator,
        verifier,
    ) -> Dict[str, Any]:
        """
        Solve with reflection and learning.

        The model "thinks" about the problem, tries approaches,
        reflects on what worked, and adapts.
        """

        # Generate initial thoughts
        thoughts = self._generate_initial_thoughts(problem, model_generator)

        # Try most promising thought
        for thought in thoughts:
            # Attempt solution with this approach
            solution, attempts = self.refinement.solve_with_refinement(
                problem,
                model_generator,
                verifier,
            )

            # Reflect on this attempt
            reflection = self._reflect_on_attempt(
                problem,
                thought,
                attempts,
                model_generator,
            )

            # Store in memory
            self.memory.append({
                "problem": problem,
                "approach": thought,
                "attempts": attempts,
                "reflection": reflection,
                "success": attempts[-1].verification_result.get("verified", False),
            })

            # If successful, return
            if attempts[-1].verification_result.get("verified"):
                return {
                    "solution": solution,
                    "attempts": attempts,
                    "reflection": reflection,
                    "verified": True,
                }

        # If all failed, return best attempt
        best_memory = max(
            self.memory,
            key=lambda m: m["attempts"][-1].verification_result.get("confidence", 0),
        )

        return {
            "solution": best_memory["attempts"][-1].solution,
            "attempts": best_memory["attempts"],
            "reflection": best_memory["reflection"],
            "verified": False,
        }

    def _generate_initial_thoughts(
        self,
        problem: str,
        model_generator,
    ) -> List[str]:
        """Generate initial strategic thoughts about the problem."""

        prompt = f"""
Analyze this problem and suggest 3-5 different approaches to solve it.

Problem: {problem}

For each approach, briefly explain:
1. The strategy (e.g., "direct calculation", "proof by contradiction", "use symmetry")
2. Why it might work
3. Potential challenges

Approaches:
"""

        response = model_generator(prompt, temperature=0.8)

        # Parse into list of approaches
        approaches = [
            line.strip()
            for line in response.split('\n')
            if line.strip() and any(c.isalnum() for c in line)
        ]

        return approaches[:5]  # Top 5

    def _reflect_on_attempt(
        self,
        problem: str,
        approach: str,
        attempts: List[RefinementAttempt],
        model_generator,
    ) -> str:
        """
        Reflect on what was learned from this attempt.

        This builds the model's "intuition" over time.
        """

        reflection_prompt = f"""
Reflect on this solution attempt.

Problem: {problem}
Approach: {approach}
Number of iterations: {len(attempts)}
Final result: {attempts[-1].verification_result.get("verified", False)}

What did you learn?
- What worked well?
- What didn't work?
- What would you do differently next time?
- What mathematical insight did you gain?

Reflection:
"""

        reflection = model_generator(reflection_prompt, temperature=0.5)

        return reflection
