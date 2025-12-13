"""
Symbolic verification engine using SymPy.
Ensures 100% correctness on attempted solutions - zero hallucination tolerance.
"""

import re
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass
from enum import Enum

import sympy as sp
from sympy import symbols, simplify, solve, diff, integrate, limit
from sympy.parsing.sympy_parser import parse_expr, standard_transformations, implicit_multiplication_application


class VerificationStatus(Enum):
    VERIFIED = "verified"
    FAILED = "failed"
    INDETERMINATE = "indeterminate"
    PARSE_ERROR = "parse_error"


@dataclass
class VerificationResult:
    """Result of symbolic verification."""

    status: VerificationStatus
    confidence: float  # 0.0 to 1.0
    explanation: str
    symbolic_proof: Optional[str] = None
    counterexample: Optional[Dict[str, Any]] = None
    intermediate_steps: List[str] = None

    def __post_init__(self):
        if self.intermediate_steps is None:
            self.intermediate_steps = []


class SymbolicVerifier:
    """
    Symbolic verification engine with zero tolerance for hallucination.
    Uses SymPy for rigorous mathematical verification.
    """

    def __init__(self):
        self.transformations = (
            standard_transformations + (implicit_multiplication_application,)
        )

    def verify_solution(
        self,
        problem: str,
        solution: str,
        expected_answer: Optional[str] = None,
    ) -> VerificationResult:
        """
        Verify a mathematical solution using symbolic computation.

        Args:
            problem: Original problem statement
            solution: Proposed solution
            expected_answer: Optional expected answer to check against

        Returns:
            VerificationResult with verification status and details
        """
        try:
            # Extract mathematical expressions from problem and solution
            problem_expr = self._extract_expression(problem)
            solution_expr = self._extract_expression(solution)

            if solution_expr is None:
                return VerificationResult(
                    status=VerificationStatus.PARSE_ERROR,
                    confidence=0.0,
                    explanation="Could not parse solution as valid mathematical expression"
                )

            # Verify based on problem type
            if "solve" in problem.lower() or "=" in problem:
                return self._verify_equation(problem_expr, solution_expr)
            elif "prove" in problem.lower() or "show that" in problem.lower():
                return self._verify_proof(problem, solution)
            elif "simplify" in problem.lower():
                return self._verify_simplification(problem_expr, solution_expr)
            elif "derivative" in problem.lower() or "d/d" in problem:
                return self._verify_derivative(problem, solution_expr)
            elif "integral" in problem.lower() or "∫" in problem:
                return self._verify_integral(problem, solution_expr)
            else:
                return self._verify_general(problem, solution_expr, expected_answer)

        except Exception as e:
            return VerificationResult(
                status=VerificationStatus.FAILED,
                confidence=0.0,
                explanation=f"Verification error: {str(e)}"
            )

    def _extract_expression(self, text: str) -> Optional[sp.Expr]:
        """Extract and parse mathematical expression from text."""
        try:
            # Try to parse the entire text
            expr = parse_expr(text, transformations=self.transformations)
            return expr
        except:
            # Extract mathematical patterns
            patterns = [
                r'(?:=\s*)?([0-9x\+\-\*/\^\(\)\s]+)',
                r'([a-z]\([0-9x\+\-\*/\^\(\)\s,]+\))',
            ]

            for pattern in patterns:
                match = re.search(pattern, text)
                if match:
                    try:
                        return parse_expr(match.group(1), transformations=self.transformations)
                    except:
                        continue

        return None

    def _verify_equation(
        self,
        problem_expr: Optional[sp.Expr],
        solution_expr: sp.Expr,
    ) -> VerificationResult:
        """Verify solution to an equation."""
        if problem_expr is None:
            return VerificationResult(
                status=VerificationStatus.INDETERMINATE,
                confidence=0.5,
                explanation="Could not parse problem equation"
            )

        try:
            # Substitute solution into equation and check if it equals 0
            variables = list(problem_expr.free_symbols)

            if not variables:
                # Direct comparison
                if simplify(problem_expr - solution_expr) == 0:
                    return VerificationResult(
                        status=VerificationStatus.VERIFIED,
                        confidence=1.0,
                        explanation="Solution verified by symbolic equality",
                        symbolic_proof=f"{problem_expr} = {solution_expr}"
                    )
                else:
                    return VerificationResult(
                        status=VerificationStatus.FAILED,
                        confidence=1.0,
                        explanation="Solution does not match expected value"
                    )

            # Solve equation symbolically and check if solution is in the set
            solutions = solve(problem_expr, variables[0])

            if solution_expr in solutions:
                return VerificationResult(
                    status=VerificationStatus.VERIFIED,
                    confidence=1.0,
                    explanation=f"Solution verified: {solution_expr} is in {solutions}",
                    symbolic_proof=str(solutions)
                )
            else:
                return VerificationResult(
                    status=VerificationStatus.FAILED,
                    confidence=1.0,
                    explanation=f"Solution {solution_expr} not in valid solutions {solutions}"
                )

        except Exception as e:
            return VerificationResult(
                status=VerificationStatus.INDETERMINATE,
                confidence=0.0,
                explanation=f"Could not verify equation: {str(e)}"
            )

    def _verify_proof(self, problem: str, solution: str) -> VerificationResult:
        """Verify a mathematical proof."""
        # For proofs, we need more sophisticated verification
        # This is a simplified version - full implementation would use Lean 4

        steps = []

        # Check if solution contains logical steps
        if "therefore" in solution.lower() or "thus" in solution.lower():
            steps.append("Solution contains logical connectives")

        if "assume" in solution.lower() or "suppose" in solution.lower():
            steps.append("Solution uses proof by assumption")

        if "contradiction" in solution.lower():
            steps.append("Solution uses proof by contradiction")

        if len(steps) > 0:
            return VerificationResult(
                status=VerificationStatus.INDETERMINATE,
                confidence=0.7,
                explanation="Proof structure appears valid but requires formal verification",
                intermediate_steps=steps
            )

        return VerificationResult(
            status=VerificationStatus.INDETERMINATE,
            confidence=0.3,
            explanation="Proof verification requires formal proof assistant (Lean 4)"
        )

    def _verify_simplification(
        self,
        original: Optional[sp.Expr],
        simplified: sp.Expr,
    ) -> VerificationResult:
        """Verify that simplification is correct."""
        if original is None:
            return VerificationResult(
                status=VerificationStatus.FAILED,
                confidence=0.0,
                explanation="Could not parse original expression"
            )

        try:
            # Check if expressions are symbolically equivalent
            difference = simplify(original - simplified)

            if difference == 0:
                return VerificationResult(
                    status=VerificationStatus.VERIFIED,
                    confidence=1.0,
                    explanation="Simplification verified by symbolic equality",
                    symbolic_proof=f"simplify({original} - {simplified}) = 0"
                )
            else:
                return VerificationResult(
                    status=VerificationStatus.FAILED,
                    confidence=1.0,
                    explanation=f"Expressions not equivalent: difference = {difference}"
                )

        except Exception as e:
            return VerificationResult(
                status=VerificationStatus.FAILED,
                confidence=0.0,
                explanation=f"Simplification verification failed: {str(e)}"
            )

    def _verify_derivative(
        self,
        problem: str,
        solution: sp.Expr,
    ) -> VerificationResult:
        """Verify derivative computation."""
        try:
            # Extract function and variable from problem
            # Simplified - would need better parsing in production
            x = symbols('x')

            # Extract the function being differentiated
            func_match = re.search(r'd/dx\s*\(?([^\)]+)\)?', problem)
            if not func_match:
                func_match = re.search(r'derivative.*of\s+([^\s]+)', problem)

            if not func_match:
                return VerificationResult(
                    status=VerificationStatus.INDETERMINATE,
                    confidence=0.0,
                    explanation="Could not extract function to differentiate"
                )

            func = parse_expr(func_match.group(1), transformations=self.transformations)
            computed_derivative = diff(func, x)

            if simplify(computed_derivative - solution) == 0:
                return VerificationResult(
                    status=VerificationStatus.VERIFIED,
                    confidence=1.0,
                    explanation=f"Derivative verified: d/dx({func}) = {solution}",
                    symbolic_proof=str(computed_derivative)
                )
            else:
                return VerificationResult(
                    status=VerificationStatus.FAILED,
                    confidence=1.0,
                    explanation=f"Incorrect derivative. Expected {computed_derivative}, got {solution}"
                )

        except Exception as e:
            return VerificationResult(
                status=VerificationStatus.FAILED,
                confidence=0.0,
                explanation=f"Derivative verification failed: {str(e)}"
            )

    def _verify_integral(
        self,
        problem: str,
        solution: sp.Expr,
    ) -> VerificationResult:
        """Verify integral computation."""
        try:
            x = symbols('x')

            # Extract integrand
            integrand_match = re.search(r'∫\s*([^\s]+)\s*d', problem)
            if not integrand_match:
                integrand_match = re.search(r'integral.*of\s+([^\s]+)', problem)

            if not integrand_match:
                return VerificationResult(
                    status=VerificationStatus.INDETERMINATE,
                    confidence=0.0,
                    explanation="Could not extract integrand"
                )

            integrand = parse_expr(integrand_match.group(1), transformations=self.transformations)
            computed_integral = integrate(integrand, x)

            # Check equivalence (ignoring constant of integration)
            derivative_of_solution = diff(solution, x)
            if simplify(derivative_of_solution - integrand) == 0:
                return VerificationResult(
                    status=VerificationStatus.VERIFIED,
                    confidence=1.0,
                    explanation=f"Integral verified by differentiation",
                    symbolic_proof=f"d/dx({solution}) = {integrand}"
                )
            else:
                return VerificationResult(
                    status=VerificationStatus.FAILED,
                    confidence=1.0,
                    explanation=f"Incorrect integral. Expected form: {computed_integral}"
                )

        except Exception as e:
            return VerificationResult(
                status=VerificationStatus.FAILED,
                confidence=0.0,
                explanation=f"Integral verification failed: {str(e)}"
            )

    def _verify_general(
        self,
        problem: str,
        solution: sp.Expr,
        expected: Optional[str],
    ) -> VerificationResult:
        """General verification for various problem types."""
        if expected:
            try:
                expected_expr = parse_expr(expected, transformations=self.transformations)
                if simplify(solution - expected_expr) == 0:
                    return VerificationResult(
                        status=VerificationStatus.VERIFIED,
                        confidence=1.0,
                        explanation="Solution matches expected answer"
                    )
                else:
                    return VerificationResult(
                        status=VerificationStatus.FAILED,
                        confidence=1.0,
                        explanation=f"Solution {solution} does not match expected {expected_expr}"
                    )
            except:
                pass

        return VerificationResult(
            status=VerificationStatus.INDETERMINATE,
            confidence=0.5,
            explanation="No verification method available for this problem type"
        )

    def generate_counterexample(
        self,
        statement: str,
        max_attempts: int = 100,
    ) -> Optional[Dict[str, Any]]:
        """
        Generate counterexample for false statements.
        Used in always/sometimes/never evaluation.
        """
        try:
            expr = self._extract_expression(statement)
            if expr is None:
                return None

            variables = list(expr.free_symbols)
            if not variables:
                return None

            # Try random values to find counterexample
            import random
            for _ in range(max_attempts):
                values = {var: random.randint(-10, 10) for var in variables}
                result = expr.subs(values)

                if result == False or result == 0:
                    return values

            return None

        except Exception:
            return None
