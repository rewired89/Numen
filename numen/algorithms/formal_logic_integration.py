"""
Formal Logic Integration with Lean 4.

Translates mathematical problems to formal proofs and verifies using Lean 4 theorem prover.
This is the cutting edge - used by AlphaProof to solve IMO problems.

Key insight: Formal logic catches errors that symbolic verification misses.
"""

from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass
from enum import Enum
import subprocess
import tempfile
import os


class ProofLanguage(Enum):
    """Supported formal proof languages."""

    LEAN4 = "lean4"
    ISABELLE = "isabelle"
    COQ = "coq"


@dataclass
class FormalProof:
    """Formal proof in a theorem prover language."""

    language: ProofLanguage
    proof_code: str
    theorem_statement: str
    tactics_used: List[str]
    compiled: bool = False
    error_message: Optional[str] = None


class LeanIntegration:
    """
    Integration with Lean 4 theorem prover.

    Provides:
    1. Auto-formalization: Natural language → Lean code
    2. Proof verification: Check if Lean proof compiles
    3. Tactic generation: Generate Lean tactics for proof steps

    This is what AlphaProof uses to solve IMO problems!
    """

    def __init__(self, lean_executable: str = "lean"):
        """
        Initialize Lean integration.

        Args:
            lean_executable: Path to lean executable
        """
        self.lean_executable = lean_executable
        self.check_lean_installed()

    def check_lean_installed(self) -> bool:
        """Check if Lean 4 is installed."""
        try:
            result = subprocess.run(
                [self.lean_executable, "--version"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            print("⚠️ Lean 4 not found. Install from: https://leanprover.github.io/lean4/doc/setup.html")
            return False

    def auto_formalize(
        self,
        natural_language_problem: str,
        model_generator,
    ) -> FormalProof:
        """
        Auto-formalize: Convert natural language to Lean 4 code.

        This is the key step - teach LLM to output Lean, not just English.

        Args:
            natural_language_problem: Problem in natural language
            model_generator: LLM that generates Lean code

        Returns:
            FormalProof with Lean code
        """
        # Prompt for auto-formalization
        formalization_prompt = f"""
Convert the following mathematical problem to Lean 4 code.

Problem: {natural_language_problem}

Generate Lean 4 code with:
1. theorem statement
2. proof using tactics
3. all necessary imports

Example format:
```lean
import Mathlib.Data.Nat.Prime

theorem problem_name : statement := by
  -- proof tactics here
  sorry
```

Lean 4 code:
"""

        # Generate Lean code (would use actual LLM here)
        lean_code = model_generator(formalization_prompt)

        # Extract theorem statement
        theorem_statement = self._extract_theorem_statement(lean_code)

        # Extract tactics
        tactics = self._extract_tactics(lean_code)

        return FormalProof(
            language=ProofLanguage.LEAN4,
            proof_code=lean_code,
            theorem_statement=theorem_statement,
            tactics_used=tactics,
        )

    def verify_proof(self, proof: FormalProof) -> Tuple[bool, Optional[str]]:
        """
        Verify proof by compiling with Lean 4.

        This is MUCH stronger than SymPy verification for proofs!

        Args:
            proof: FormalProof to verify

        Returns:
            Tuple of (success, error_message)
        """
        if proof.language != ProofLanguage.LEAN4:
            return False, "Only Lean 4 supported currently"

        # Write proof to temporary file
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.lean',
            delete=False,
        ) as f:
            f.write(proof.proof_code)
            temp_file = f.name

        try:
            # Compile with Lean
            result = subprocess.run(
                [self.lean_executable, temp_file],
                capture_output=True,
                text=True,
                timeout=30,
            )

            success = result.returncode == 0
            error_message = result.stderr if not success else None

            proof.compiled = success
            proof.error_message = error_message

            return success, error_message

        except subprocess.TimeoutExpired:
            return False, "Lean compilation timeout"

        finally:
            # Cleanup
            if os.path.exists(temp_file):
                os.remove(temp_file)

    def generate_proof_tactics(
        self,
        theorem: str,
        context: List[str],
        model_generator,
    ) -> List[str]:
        """
        Generate Lean tactics for proving theorem.

        This guides the LLM to think in terms of formal tactics,
        not just natural language steps.

        Available Lean 4 tactics:
        - intro: Introduce hypothesis
        - apply: Apply theorem/lemma
        - rewrite: Rewrite using equality
        - induction: Proof by induction
        - cases: Case analysis
        - ring: Solve ring equations
        - exact: Provide exact proof term
        - sorry: Placeholder (proves anything - for testing)

        Args:
            theorem: Theorem statement
            context: Current proof context
            model_generator: LLM for tactic generation

        Returns:
            List of Lean tactics
        """
        tactics_prompt = f"""
Given the theorem and current context, generate the next Lean 4 tactic.

Theorem: {theorem}

Context:
{chr(10).join(context)}

Available tactics:
- intro: Introduce variable/hypothesis
- apply <lemma>: Apply a theorem
- rewrite [<eq>]: Rewrite using equality
- induction <var>: Proof by induction
- cases <var>: Case analysis
- ring: Solve ring equation
- exact <term>: Provide exact proof

Next tactic:
"""

        # Generate tactic (would use actual LLM)
        tactic = model_generator(tactics_prompt)

        return [tactic.strip()]

    def iterative_proof_search(
        self,
        problem: str,
        model_generator,
        max_attempts: int = 10,
    ) -> Optional[FormalProof]:
        """
        Iteratively generate and verify proof.

        Process:
        1. Generate initial formalization
        2. Try to compile
        3. If fails, use error to guide next attempt
        4. Repeat until success or max_attempts

        This is the key loop for learning from verification!
        """
        for attempt in range(max_attempts):
            # Generate formalization
            if attempt == 0:
                proof = self.auto_formalize(problem, model_generator)
            else:
                # Use previous error to guide refinement
                proof = self._refine_proof(proof, model_generator)

            # Verify
            success, error = self.verify_proof(proof)

            if success:
                return proof

            # Store error for next iteration
            proof.error_message = error

        return None

    def _refine_proof(
        self,
        failed_proof: FormalProof,
        model_generator,
    ) -> FormalProof:
        """
        Refine failed proof using error message.

        This implements self-correction based on Lean's feedback!
        """
        refinement_prompt = f"""
The following Lean proof failed to compile:

```lean
{failed_proof.proof_code}
```

Error message:
{failed_proof.error_message}

Fix the proof and provide corrected Lean 4 code:
"""

        refined_code = model_generator(refinement_prompt)

        return FormalProof(
            language=ProofLanguage.LEAN4,
            proof_code=refined_code,
            theorem_statement=failed_proof.theorem_statement,
            tactics_used=self._extract_tactics(refined_code),
        )

    def _extract_theorem_statement(self, lean_code: str) -> str:
        """Extract theorem statement from Lean code."""
        import re

        match = re.search(r'theorem\s+\w+\s*:\s*([^:=]+):=', lean_code)
        if match:
            return match.group(1).strip()
        return ""

    def _extract_tactics(self, lean_code: str) -> List[str]:
        """Extract tactics from Lean proof."""
        import re

        # Find content between 'by' and end
        match = re.search(r':=\s*by\s*(.+)', lean_code, re.DOTALL)
        if match:
            tactics_block = match.group(1)

            # Split by newlines and filter
            tactics = [
                line.strip()
                for line in tactics_block.split('\n')
                if line.strip() and not line.strip().startswith('--')
            ]

            return tactics

        return []


class FormalVerificationPipeline:
    """
    Complete pipeline: Natural language → Lean → Verified proof.

    This is what Numen needs to reach 80%+ on complex proofs!
    """

    def __init__(self, model_generator, symbolic_verifier):
        self.lean = LeanIntegration()
        self.model = model_generator
        self.symbolic_verifier = symbolic_verifier

    def solve_with_formal_verification(
        self,
        problem: str,
        try_symbolic_first: bool = True,
    ) -> Dict[str, Any]:
        """
        Solve problem with formal verification.

        Strategy:
        1. Try symbolic verification first (fast)
        2. If fails or is proof, use Lean (slow but rigorous)

        Args:
            problem: Mathematical problem
            try_symbolic_first: Try SymPy before Lean

        Returns:
            Solution with verification details
        """
        result = {
            "problem": problem,
            "solution": None,
            "verified": False,
            "verification_method": None,
            "proof": None,
        }

        # Detect if problem requires proof
        is_proof_problem = any(
            keyword in problem.lower()
            for keyword in ["prove", "show that", "demonstrate"]
        )

        # Try symbolic first for non-proof problems
        if try_symbolic_first and not is_proof_problem:
            symbolic_result = self.symbolic_verifier.verify_solution(
                problem,
                self.model.generate_solution(problem),
            )

            if symbolic_result.status == "VERIFIED":
                result["solution"] = symbolic_result.solution
                result["verified"] = True
                result["verification_method"] = "symbolic"
                return result

        # Use Lean for proofs or when symbolic fails
        formal_proof = self.lean.iterative_proof_search(
            problem,
            self.model.generate_lean,
        )

        if formal_proof and formal_proof.compiled:
            result["solution"] = formal_proof.theorem_statement
            result["verified"] = True
            result["verification_method"] = "lean4"
            result["proof"] = formal_proof.proof_code

        return result


# Example Lean 4 proof templates for training data
LEAN_PROOF_EXAMPLES = """
# Example 1: Infinitely many primes

theorem infinitely_many_primes : ∀ n, ∃ p ≥ n, Nat.Prime p := by
  intro n
  -- Consider N = n! + 1
  let N := (Nat.factorial n) + 1
  -- N has a prime divisor p
  have ⟨p, hp_prime, hp_dvd⟩ := exists_prime_factor (Nat.factorial_pos n)
  exists p
  constructor
  · -- Show p ≥ n
    by_contra h
    push_neg at h
    -- p divides n! so p divides N - n! = 1, contradiction
    have : p ∣ Nat.factorial n := Nat.Prime.dvd_factorial hp_prime h
    have : p ∣ 1 := (Nat.dvd_add_right this).mp hp_dvd
    exact Nat.Prime.not_dvd_one hp_prime this
  · exact hp_prime


# Example 2: Sum of first n natural numbers

theorem sum_first_n (n : ℕ) : 2 * (Finset.range (n + 1)).sum id = n * (n + 1) := by
  induction n with
  | zero => simp
  | succ n ih =>
    rw [Finset.sum_range_succ, mul_add, ih]
    ring


# Example 3: Derivative of x^2

theorem deriv_sq (x : ℝ) : deriv (fun x => x^2) x = 2 * x := by
  rw [deriv_pow]
  simp
  ring
"""
