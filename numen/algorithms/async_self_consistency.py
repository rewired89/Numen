"""
Async Self-Consistency - Parallel solution generation for 5x speed boost.
Inspired by Poetiq's async processing architecture.

Instead of generating 5 solutions sequentially (slow),
generate them in parallel (fast)!
"""

import asyncio
from typing import Callable, Dict, Any, List, Tuple, Optional
from collections import Counter
from dataclasses import dataclass
import sympy as sp

from numen.core.verifier import SymbolicVerifier, VerificationStatus


@dataclass
class AsyncSolutionAttempt:
    """Result from one async solution attempt."""
    solution: str
    reasoning: List[str]
    verification_status: VerificationStatus
    time_taken: float
    attempt_number: int


class AsyncSelfConsistency:
    """
    Async Self-Consistency Reasoner.

    Improvement over sequential Self-Consistency:
    - Sequential: 5 attempts × 3 seconds = 15 seconds total
    - Parallel: max(5 attempts) ≈ 3 seconds total
    - Speedup: 5x faster!

    How it works:
    1. Launch multiple solution attempts in parallel (asyncio.gather)
    2. Each attempt runs independently
    3. Collect all results
    4. Find consensus among verified solutions
    5. Return most common correct answer
    """

    def __init__(
        self,
        num_samples: int = 5,
        temperature: float = 0.7,
        verifier: Optional[SymbolicVerifier] = None,
        max_concurrent: int = 10,
    ):
        """
        Initialize Async Self-Consistency.

        Args:
            num_samples: Number of parallel solution attempts
            temperature: Sampling temperature for diversity
            verifier: Symbolic verifier for correctness checking
            max_concurrent: Maximum concurrent async tasks
        """
        self.num_samples = num_samples
        self.temperature = temperature
        self.verifier = verifier or SymbolicVerifier()
        self.max_concurrent = max_concurrent

    async def solve_with_async_self_consistency(
        self,
        problem: str,
        generator_fn: Callable,
        max_attempts_per_sample: int = 3,
    ) -> Tuple[Optional[str], Dict[str, Any]]:
        """
        Solve problem using async self-consistency.

        Args:
            problem: Math problem to solve
            generator_fn: Async function that generates solutions
            max_attempts_per_sample: Retry attempts if generation fails

        Returns:
            (best_solution, metadata)
        """
        import time

        start_time = time.time()

        # Create tasks for parallel execution
        tasks = [
            self._generate_solution_async(
                problem=problem,
                generator_fn=generator_fn,
                attempt_number=i,
                max_attempts=max_attempts_per_sample,
            )
            for i in range(self.num_samples)
        ]

        # Run all attempts in parallel
        solution_attempts = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out failed attempts
        valid_attempts = [
            attempt for attempt in solution_attempts
            if isinstance(attempt, AsyncSolutionAttempt)
        ]

        if not valid_attempts:
            return None, {
                "error": "All solution attempts failed",
                "num_attempts": self.num_samples,
                "time_taken": time.time() - start_time,
            }

        # Find verified solutions
        verified_solutions = [
            attempt for attempt in valid_attempts
            if attempt.verification_status == VerificationStatus.VERIFIED
        ]

        if not verified_solutions:
            # No verified solutions - return most common attempt anyway
            all_solutions = [attempt.solution for attempt in valid_attempts]
            solution_counts = Counter(all_solutions)
            most_common, count = solution_counts.most_common(1)[0]

            return most_common, {
                "consensus_solution": most_common,
                "confidence": count / len(all_solutions),
                "verified": False,
                "num_verified": 0,
                "num_total": len(valid_attempts),
                "time_taken": time.time() - start_time,
                "warning": "No solutions passed verification",
            }

        # Find consensus among verified solutions
        verified_solution_strings = [attempt.solution for attempt in verified_solutions]
        solution_counts = Counter(verified_solution_strings)
        most_common_solution, count = solution_counts.most_common(1)[0]

        # Calculate confidence
        confidence = count / len(verified_solutions)

        # Get best reasoning (from most common solution)
        best_attempt = next(
            attempt for attempt in verified_solutions
            if attempt.solution == most_common_solution
        )

        total_time = time.time() - start_time

        return most_common_solution, {
            "consensus_solution": most_common_solution,
            "confidence": confidence,
            "verified": True,
            "num_verified": len(verified_solutions),
            "num_total": len(valid_attempts),
            "consensus_count": count,
            "reasoning": best_attempt.reasoning,
            "time_taken": total_time,
            "average_time_per_attempt": sum(a.time_taken for a in valid_attempts) / len(valid_attempts),
            "speedup": f"{(sum(a.time_taken for a in valid_attempts) / total_time):.1f}x",
            "all_solutions": solution_counts.most_common(),
        }

    async def _generate_solution_async(
        self,
        problem: str,
        generator_fn: Callable,
        attempt_number: int,
        max_attempts: int = 3,
    ) -> AsyncSolutionAttempt:
        """
        Generate a single solution asynchronously.

        Args:
            problem: Problem to solve
            generator_fn: Solution generator (can be async or sync)
            attempt_number: Which attempt this is (0, 1, 2, ...)
            max_attempts: Retry attempts on failure

        Returns:
            AsyncSolutionAttempt
        """
        import time

        start_time = time.time()

        for retry in range(max_attempts):
            try:
                # Call generator (handle both async and sync)
                if asyncio.iscoroutinefunction(generator_fn):
                    result = await generator_fn(
                        problem,
                        temperature=self.temperature,
                        do_sample=True,
                    )
                else:
                    # Wrap sync function in async
                    result = await asyncio.to_thread(
                        generator_fn,
                        problem,
                        temperature=self.temperature,
                        do_sample=True,
                    )

                # Extract solution and reasoning
                if isinstance(result, dict):
                    solution = result.get("solution", str(result))
                    reasoning = result.get("reasoning", [])
                elif isinstance(result, tuple):
                    solution, reasoning = result[0], result[1] if len(result) > 1 else []
                else:
                    solution = str(result)
                    reasoning = []

                # Verify solution
                verification = self.verifier.verify_solution(problem, solution)

                time_taken = time.time() - start_time

                return AsyncSolutionAttempt(
                    solution=solution,
                    reasoning=reasoning if isinstance(reasoning, list) else [str(reasoning)],
                    verification_status=verification.status,
                    time_taken=time_taken,
                    attempt_number=attempt_number,
                )

            except Exception as e:
                if retry == max_attempts - 1:
                    # Last attempt failed - return error
                    return AsyncSolutionAttempt(
                        solution=f"Error: {str(e)}",
                        reasoning=[f"Failed after {max_attempts} attempts"],
                        verification_status=VerificationStatus.FAILED,
                        time_taken=time.time() - start_time,
                        attempt_number=attempt_number,
                    )

                # Retry
                await asyncio.sleep(0.1 * (retry + 1))  # Exponential backoff

    def solve_sync(
        self,
        problem: str,
        generator_fn: Callable,
        max_attempts_per_sample: int = 3,
    ) -> Tuple[Optional[str], Dict[str, Any]]:
        """
        Synchronous wrapper for async solve.
        Use this if you don't want to deal with asyncio.

        Args:
            problem: Math problem
            generator_fn: Solution generator
            max_attempts_per_sample: Retry attempts

        Returns:
            (solution, metadata)
        """
        return asyncio.run(
            self.solve_with_async_self_consistency(
                problem=problem,
                generator_fn=generator_fn,
                max_attempts_per_sample=max_attempts_per_sample,
            )
        )


class ThreeTierSolver:
    """
    3-Tier Escalating Prompt Strategy (inspired by Poetiq).

    Tier 1 (Basic): Simple, fast prompt
    Tier 2 (Enhanced): More detailed reasoning
    Tier 3 (Advanced): Full analysis with failure feedback

    Strategy:
    1. Try Tier 1 (fast, works for easy problems)
    2. If fails verification, try Tier 2 (more careful)
    3. If still fails, try Tier 3 (maximum reasoning power)

    This saves time on easy problems while still solving hard ones.
    """

    def __init__(self, verifier: Optional[SymbolicVerifier] = None):
        self.verifier = verifier or SymbolicVerifier()

        # Define 3 tiers of prompts
        self.tier1_prompt = """Solve this math problem:

{problem}

Give a concise answer."""

        self.tier2_prompt = """Solve this math problem carefully:

{problem}

Show your reasoning step-by-step:
1. Identify what type of problem this is
2. Choose the appropriate method
3. Apply the method carefully
4. Verify your answer

Answer:"""

        self.tier3_prompt = """Solve this challenging math problem with maximum rigor:

{problem}

Previous attempt failed verification. Analyze carefully:

1. **Problem Analysis**: What type of problem is this? What concepts are involved?
2. **Strategy Selection**: What's the best approach? Why?
3. **Step-by-Step Solution**: Show every step clearly
4. **Common Pitfalls**: What mistakes should you avoid?
5. **Verification**: Check your answer by substitution
6. **Alternative Approaches**: Is there another way to verify?

Take your time and be thorough.

Answer:"""

    async def solve_with_escalation(
        self,
        problem: str,
        generator_fn: Callable,
    ) -> Tuple[Optional[str], Dict[str, Any]]:
        """
        Solve using 3-tier escalation strategy.

        Args:
            problem: Math problem
            generator_fn: LLM generator function

        Returns:
            (solution, metadata with tier info)
        """
        tiers = [
            ("Tier 1 (Basic)", self.tier1_prompt),
            ("Tier 2 (Enhanced)", self.tier2_prompt),
            ("Tier 3 (Advanced)", self.tier3_prompt),
        ]

        for tier_name, prompt_template in tiers:
            # Format prompt
            prompt = prompt_template.format(problem=problem)

            # Generate solution
            if asyncio.iscoroutinefunction(generator_fn):
                solution = await generator_fn(prompt)
            else:
                solution = await asyncio.to_thread(generator_fn, prompt)

            # Extract solution string
            if isinstance(solution, dict):
                solution_str = solution.get("solution", str(solution))
            else:
                solution_str = str(solution)

            # Verify
            verification = self.verifier.verify_solution(problem, solution_str)

            if verification.status == VerificationStatus.VERIFIED:
                # Success!
                return solution_str, {
                    "tier_used": tier_name,
                    "escalation_needed": tier_name != "Tier 1 (Basic)",
                    "verification": verification,
                    "message": f"✅ Solved using {tier_name}",
                }

        # All tiers failed
        return None, {
            "tier_used": "Tier 3 (Advanced)",
            "escalation_needed": True,
            "verification": verification,
            "message": "❌ All tiers failed verification",
            "suggestion": "Problem may be unsolvable or incorrectly stated",
        }

    def solve_sync(
        self,
        problem: str,
        generator_fn: Callable,
    ) -> Tuple[Optional[str], Dict[str, Any]]:
        """Synchronous wrapper."""
        return asyncio.run(self.solve_with_escalation(problem, generator_fn))
