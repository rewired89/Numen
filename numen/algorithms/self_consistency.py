"""
Self-Consistency: Generate multiple solutions and find consensus.

Key paper: "Self-Consistency Improves Chain of Thought Reasoning in Language Models"
(Wang et al., 2022)

Improves accuracy by 10-30% on math problems by generating diverse reasoning paths
and selecting the most consistent verified answer.
"""

from typing import List, Dict, Any, Optional, Tuple
from collections import Counter
import numpy as np

from numen.core.verifier import SymbolicVerifier, VerificationResult, VerificationStatus


class SelfConsistencyReasoner:
    """
    Self-consistency reasoning for mathematical problems.

    Generates multiple independent solution attempts and selects the
    most frequently occurring VERIFIED answer.

    Key insight: Random errors are inconsistent, correct reasoning converges.
    """

    def __init__(
        self,
        num_samples: int = 10,
        temperature: float = 0.8,
        min_verified: int = 2,
    ):
        """
        Args:
            num_samples: Number of independent solutions to generate
            temperature: Sampling temperature (higher = more diversity)
            min_verified: Minimum verified answers required to be confident
        """
        self.num_samples = num_samples
        self.temperature = temperature
        self.min_verified = min_verified
        self.verifier = SymbolicVerifier()

    def solve_with_self_consistency(
        self,
        problem: str,
        generator_fn,  # Function that generates solutions
        max_attempts_per_sample: int = 3,
    ) -> Tuple[Optional[str], Dict[str, Any]]:
        """
        Solve problem using self-consistency.

        Args:
            problem: Mathematical problem
            generator_fn: Function that generates solution given problem
            max_attempts_per_sample: Retries if generation fails

        Returns:
            Tuple of (best_solution, statistics)
        """
        verified_solutions = []
        all_attempts = []

        # Generate multiple independent solutions
        for i in range(self.num_samples):
            for attempt in range(max_attempts_per_sample):
                try:
                    # Generate solution with sampling
                    solution = generator_fn(
                        problem,
                        temperature=self.temperature,
                        do_sample=True,
                    )

                    # Verify solution
                    verification = self.verifier.verify_solution(problem, solution)

                    all_attempts.append({
                        "sample": i + 1,
                        "attempt": attempt + 1,
                        "solution": solution,
                        "verified": verification.status == VerificationStatus.VERIFIED,
                        "confidence": verification.confidence,
                    })

                    # If verified, add to candidates
                    if verification.status == VerificationStatus.VERIFIED:
                        verified_solutions.append(solution)
                        break  # Got verified answer, move to next sample

                except Exception as e:
                    all_attempts.append({
                        "sample": i + 1,
                        "attempt": attempt + 1,
                        "error": str(e),
                        "verified": False,
                    })

        # Find most consistent verified solution
        if not verified_solutions:
            return None, {
                "total_attempts": len(all_attempts),
                "verified_count": 0,
                "consensus": None,
                "confidence": 0.0,
            }

        # Normalize solutions (handle equivalent forms)
        normalized = [self._normalize_solution(s) for s in verified_solutions]

        # Count occurrences
        solution_counts = Counter(normalized)
        most_common_normalized, count = solution_counts.most_common(1)[0]

        # Get original form of most common solution
        best_solution = verified_solutions[
            normalized.index(most_common_normalized)
        ]

        # Calculate consensus confidence
        consensus_rate = count / len(verified_solutions)
        verification_rate = len(verified_solutions) / len(all_attempts)

        # Combined confidence score
        confidence = (
            0.5 * consensus_rate +  # How often solutions agree
            0.5 * verification_rate  # How often we found verified solutions
        )

        statistics = {
            "total_attempts": len(all_attempts),
            "verified_count": len(verified_solutions),
            "unique_verified_solutions": len(solution_counts),
            "consensus_count": count,
            "consensus_rate": consensus_rate,
            "verification_rate": verification_rate,
            "confidence": confidence,
            "all_verified_solutions": verified_solutions,
            "solution_distribution": dict(solution_counts),
        }

        # Only return if we have enough consensus
        if count >= self.min_verified:
            return best_solution, statistics
        else:
            return None, {
                **statistics,
                "error": f"Insufficient consensus (need {self.min_verified}, got {count})",
            }

    def _normalize_solution(self, solution: str) -> str:
        """
        Normalize solution to canonical form for comparison.

        Examples:
        - "x = 4" and "4" → "4"
        - "1/2" and "0.5" → "0.5"
        """
        import sympy as sp

        try:
            # Try to parse as sympy expression
            expr = sp.sympify(solution)
            # Convert to canonical form
            return str(sp.simplify(expr))
        except:
            # If parsing fails, use string normalization
            normalized = solution.strip().lower()
            # Remove common variations
            normalized = normalized.replace("x =", "").replace("=", "")
            normalized = normalized.strip()
            return normalized

    def explain_consensus(self, statistics: Dict[str, Any]) -> str:
        """Generate human-readable explanation of consensus."""
        if statistics["verified_count"] == 0:
            return "❌ No verified solutions found across all attempts."

        verified = statistics["verified_count"]
        total = statistics["total_attempts"]
        consensus = statistics.get("consensus_count", 0)

        explanation = f"""
## Self-Consistency Results

**Generation Success:**
- {verified}/{total} attempts produced verified solutions ({statistics['verification_rate']:.1%})
- {statistics['unique_verified_solutions']} unique verified answers found

**Consensus Analysis:**
- {consensus}/{verified} verified solutions agree ({statistics['consensus_rate']:.1%})
- Final confidence: {statistics['confidence']:.1%}

**Interpretation:**
"""

        if statistics['confidence'] >= 0.8:
            explanation += "- ✅ **HIGH CONFIDENCE**: Strong consensus on correct answer\n"
        elif statistics['confidence'] >= 0.5:
            explanation += "- ⚠️ **MEDIUM CONFIDENCE**: Some agreement, but variations exist\n"
        else:
            explanation += "- ❌ **LOW CONFIDENCE**: Inconsistent answers, uncertain solution\n"

        if statistics['unique_verified_solutions'] > 1:
            explanation += f"- Multiple valid solutions exist (or equivalent forms)\n"
            explanation += f"- Distribution: {statistics['solution_distribution']}\n"

        return explanation


# Example usage integration with Numen
class EnhancedNumenSolver:
    """Numen solver enhanced with self-consistency."""

    def __init__(self, base_solver, model):
        self.base_solver = base_solver
        self.model = model
        self.self_consistency = SelfConsistencyReasoner(num_samples=10)

    def solve_with_self_consistency(self, problem: str):
        """Solve using self-consistency."""

        def generator(prob, temperature, do_sample):
            # Generate solution using base model
            solutions = self.model.generate_solution(
                prob,
                temperature=temperature,
                num_return_sequences=1,
            )
            return solutions[0]

        solution, stats = self.self_consistency.solve_with_self_consistency(
            problem,
            generator,
        )

        return {
            "solution": solution,
            "confidence": stats.get("confidence", 0.0),
            "statistics": stats,
            "explanation": self.self_consistency.explain_consensus(stats),
        }
