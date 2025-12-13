"""
Data pipeline for training Numen on mathematical reasoning.

Data sources:
- arXiv papers (mathematics, cryptography, neuroscience)
- OpenWebMath
- MATH benchmark
- Formal proof libraries (Lean 4, Isabelle)
- Custom cross-domain datasets
"""

from typing import List, Dict, Any, Iterator, Optional
from dataclasses import dataclass
import json
import random
from pathlib import Path


@dataclass
class MathProblem:
    """Mathematical problem for training."""

    problem: str
    solution: str
    verification: Optional[str] = None
    domain: str = "general"
    difficulty: int = 5  # 1-10
    requires_proof: bool = False
    cross_domain: bool = False
    source: str = "unknown"


class MathDataPipeline:
    """
    Data pipeline for mathematical reasoning training.

    Handles data loading, preprocessing, and augmentation.
    """

    def __init__(self, data_dir: Optional[Path] = None):
        self.data_dir = data_dir or Path("data")
        self.problems: List[MathProblem] = []

    def load_math_benchmark(self) -> List[MathProblem]:
        """
        Load MATH benchmark dataset.

        MATH contains 12,500 competition math problems with step-by-step solutions.
        """
        problems = []

        # Would load actual MATH dataset
        # For now, return synthetic examples

        examples = [
            MathProblem(
                problem="Solve for x: 2x + 5 = 13",
                solution="x = 4",
                verification="2(4) + 5 = 8 + 5 = 13 ✓",
                domain="algebra",
                difficulty=2,
                source="math_benchmark"
            ),
            MathProblem(
                problem="Find the derivative of f(x) = x³ + 2x² - 5x + 1",
                solution="f'(x) = 3x² + 4x - 5",
                verification="Apply power rule to each term",
                domain="calculus",
                difficulty=4,
                source="math_benchmark"
            ),
            MathProblem(
                problem="Prove that there are infinitely many prime numbers",
                solution="Proof by contradiction: Assume finite primes p₁,...,pₙ. Consider N = p₁×...×pₙ + 1. N is not divisible by any pᵢ, so either N is prime or has a prime factor not in our list. Contradiction.",
                domain="number_theory",
                difficulty=7,
                requires_proof=True,
                source="math_benchmark"
            ),
        ]

        return examples

    def load_openwebmath(self) -> List[MathProblem]:
        """
        Load OpenWebMath corpus.

        Contains mathematical content from web including solutions.
        """
        # Would load actual OpenWebMath dataset
        return []

    def load_arxiv_papers(self, domains: List[str]) -> List[MathProblem]:
        """
        Load and extract problems from arXiv papers.

        Args:
            domains: List of arXiv categories (math.NT, cs.CR, q-bio.NC, etc.)
        """
        # Would use arXiv API to fetch papers
        # Extract theorems, proofs, and problems
        return []

    def load_cryptography_problems(self) -> List[MathProblem]:
        """
        Load cryptography-specific problems for Nyx use case.

        Focuses on:
        - Number theory problems relevant to crypto
        - Protocol analysis scenarios
        - Attack vector discovery
        """
        problems = [
            MathProblem(
                problem="Analyze RSA with modulus n=77, e=7. Is this secure?",
                solution="No. n=77 = 7×11, easily factored. φ(n)=60, d=43. Completely broken.",
                verification="Factor n to find p=7, q=11",
                domain="cryptography",
                difficulty=5,
                cross_domain=True,
                source="nyx_crypto_dataset"
            ),
            MathProblem(
                problem="An elliptic curve has order equal to the field size p. What attack applies?",
                solution="Smart's attack - anomalous curve. Discrete log can be solved in polynomial time by lifting to p-adic numbers.",
                domain="cryptography",
                difficulty=8,
                cross_domain=True,
                source="nyx_crypto_dataset"
            ),
        ]

        return problems

    def load_neuroscience_problems(self) -> List[MathProblem]:
        """
        Load neuroscience problems for NeuroCompass integration.

        Focuses on:
        - Dynamical systems modeling
        - Signal analysis
        - Cognitive state prediction
        """
        problems = [
            MathProblem(
                problem="Given neural oscillator dV/dt = V - V³/3 - W, dW/dt = 0.08(V + 0.7), find equilibrium points",
                solution="At equilibrium: V - V³/3 - W = 0 and V + 0.7 = 0 → V = -0.7, W = -0.7 + 0.7³/3 ≈ -0.586",
                domain="neural_dynamics",
                difficulty=6,
                cross_domain=True,
                source="neurocompass_dataset"
            ),
        ]

        return problems

    def create_cross_domain_problems(self) -> List[MathProblem]:
        """
        Create problems requiring cross-domain translation.

        This is Numen's unique capability - bridging disparate fields.
        """
        problems = [
            MathProblem(
                problem="Apply topological connectedness concept to analyze if a key exchange protocol has unique paths",
                solution="Model protocol as graph. Connected components represent key derivation paths. Multiple components indicate potential ambiguity in key agreement.",
                domain="cross_domain",
                difficulty=9,
                cross_domain=True,
                source="numen_synthetic"
            ),
            MathProblem(
                problem="Use Lyapunov stability analysis to predict if a cognitive state is stable",
                solution="Compute Jacobian of neural dynamics at equilibrium. Negative eigenvalues → stable state. Positive → unstable (transitioning).",
                domain="cross_domain",
                difficulty=8,
                cross_domain=True,
                source="numen_synthetic"
            ),
        ]

        return problems

    def load_all_datasets(self) -> List[MathProblem]:
        """Load all available datasets."""
        all_problems = []

        all_problems.extend(self.load_math_benchmark())
        all_problems.extend(self.load_cryptography_problems())
        all_problems.extend(self.load_neuroscience_problems())
        all_problems.extend(self.create_cross_domain_problems())

        # Would also load OpenWebMath and arXiv
        # all_problems.extend(self.load_openwebmath())
        # all_problems.extend(self.load_arxiv_papers(['math.NT', 'cs.CR', 'q-bio.NC']))

        self.problems = all_problems
        return all_problems

    def augment_problem(self, problem: MathProblem) -> List[MathProblem]:
        """
        Augment problem with variations.

        Techniques:
        - Rephrase question
        - Change numerical values
        - Request different solution methods
        - Add verification requirement
        """
        augmented = [problem]

        # Add verification variant
        if not problem.requires_proof:
            augmented.append(MathProblem(
                problem=f"{problem.problem} (verify your answer)",
                solution=f"{problem.solution}\nVerification: {problem.verification or 'Checked symbolically'}",
                verification=problem.verification,
                domain=problem.domain,
                difficulty=problem.difficulty,
                requires_proof=False,
                cross_domain=problem.cross_domain,
                source=f"{problem.source}_augmented"
            ))

        return augmented

    def format_for_training(
        self,
        problem: MathProblem,
        include_reasoning: bool = True,
    ) -> Dict[str, str]:
        """
        Format problem for training in conversation format.

        Returns:
            Dictionary with 'prompt' and 'completion' keys
        """
        prompt = f"""Solve the following mathematical problem. Provide a complete solution with verification.

Problem: {problem.problem}

Domain: {problem.domain}
"""

        if problem.requires_proof:
            prompt += "\nNote: This requires a rigorous proof.\n"

        completion = f"""Solution: {problem.solution}"""

        if problem.verification:
            completion += f"\n\nVerification: {problem.verification}"

        return {
            "prompt": prompt,
            "completion": completion,
            "domain": problem.domain,
            "difficulty": problem.difficulty,
        }

    def create_verification_examples(self) -> List[Dict[str, str]]:
        """
        Create training examples specifically for verification.

        Trains the model to verify solutions using symbolic methods.
        """
        examples = []

        # Correct verification examples
        examples.append({
            "prompt": "Verify: Does x=4 solve 2x+5=13?",
            "completion": "Substitute x=4: 2(4)+5 = 8+5 = 13 ✓ VERIFIED",
        })

        # Incorrect examples (teach to reject)
        examples.append({
            "prompt": "Verify: Does x=3 solve 2x+5=13?",
            "completion": "Substitute x=3: 2(3)+5 = 6+5 = 11 ≠ 13 ✗ FAILED",
        })

        return examples

    def get_training_iterator(
        self,
        batch_size: int = 32,
        shuffle: bool = True,
    ) -> Iterator[List[Dict[str, str]]]:
        """
        Get iterator over training batches.

        Yields:
            Batches of formatted training examples
        """
        if not self.problems:
            self.load_all_datasets()

        problems = self.problems.copy()

        if shuffle:
            random.shuffle(problems)

        batch = []
        for problem in problems:
            formatted = self.format_for_training(problem)
            batch.append(formatted)

            if len(batch) >= batch_size:
                yield batch
                batch = []

        if batch:
            yield batch

    def get_difficulty_stratified_split(
        self,
        train_ratio: float = 0.8,
    ) -> tuple[List[MathProblem], List[MathProblem]]:
        """
        Split data into train/test with stratification by difficulty.

        Ensures both sets have similar difficulty distributions.
        """
        if not self.problems:
            self.load_all_datasets()

        # Group by difficulty
        by_difficulty = {}
        for problem in self.problems:
            if problem.difficulty not in by_difficulty:
                by_difficulty[problem.difficulty] = []
            by_difficulty[problem.difficulty].append(problem)

        train_problems = []
        test_problems = []

        # Split each difficulty level
        for difficulty, problems in by_difficulty.items():
            random.shuffle(problems)
            split_idx = int(len(problems) * train_ratio)
            train_problems.extend(problems[:split_idx])
            test_problems.extend(problems[split_idx:])

        return train_problems, test_problems
