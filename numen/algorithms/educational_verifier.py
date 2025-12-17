"""
Educational Verifier - Explains WHY answers are wrong.
Perfect for students learning math and teachers grading homework.

This goes beyond pass/fail - it identifies common mistakes and provides learning hints.
"""

from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import sympy as sp
from sympy import symbols, simplify, solve, diff, integrate, Eq
from sympy.parsing.sympy_parser import parse_expr, standard_transformations, implicit_multiplication_application


class MistakeType(Enum):
    """Common mathematical mistakes students make."""
    SIGN_ERROR = "sign_error"
    ARITHMETIC_ERROR = "arithmetic_error"
    ALGEBRAIC_MANIPULATION = "algebraic_manipulation"
    FORGOT_DISTRIBUTE = "forgot_distribute"
    WRONG_FORMULA = "wrong_formula"
    DOMAIN_ERROR = "domain_error"
    INCOMPLETE_SOLUTION = "incomplete_solution"
    EXTRANEOUS_SOLUTION = "extraneous_solution"
    CONCEPTUAL_ERROR = "conceptual_error"
    CORRECT = "correct"


@dataclass
class EducationalFeedback:
    """Detailed feedback for learning."""
    is_correct: bool
    student_answer: str
    correct_answer: str
    mistake_type: Optional[MistakeType]
    explanation: str
    hint: str
    step_by_step_correction: List[str]
    difficulty_level: str  # "easy", "medium", "hard"
    learning_resources: List[str]


class EducationalVerifier:
    """
    Verifier that provides educational feedback.

    Instead of just "wrong", it explains:
    - What type of mistake was made
    - Why it's wrong
    - How to fix it
    - What concept to review
    """

    def __init__(self):
        self.transformations = (
            standard_transformations + (implicit_multiplication_application,)
        )

        # Common mistake patterns
        self.mistake_patterns = {
            "sign_errors": [
                ("-(a+b)", "-a-b", "Distribute negative: -(a+b) = -a - b"),
                ("a-b", "a+b", "Check your signs carefully"),
            ],
            "algebra_rules": [
                ("sqrt(a^2 + b^2)", "a + b", "√(a²+b²) ≠ a+b. Cannot split square roots over addition."),
                ("(a+b)^2", "a^2 + b^2", "(a+b)² = a² + 2ab + b², not a² + b²"),
            ],
        }

    def verify_homework(
        self,
        problem: str,
        student_answer: str,
        expected_answer: Optional[str] = None,
        problem_type: str = "equation",
    ) -> EducationalFeedback:
        """
        Verify student's homework with educational feedback.

        Args:
            problem: The math problem
            student_answer: Student's solution
            expected_answer: Teacher's answer key (optional)
            problem_type: Type of problem (equation, derivative, etc.)

        Returns:
            EducationalFeedback with detailed explanation
        """
        try:
            x = symbols('x')

            # Parse student's answer
            student_expr = self._safe_parse(student_answer)
            if student_expr is None:
                return self._parsing_error_feedback(student_answer)

            # Get correct answer
            if expected_answer:
                correct_expr = self._safe_parse(expected_answer)
            else:
                correct_expr = self._compute_correct_answer(problem, problem_type)

            if correct_expr is None:
                return self._unsolvable_feedback(problem)

            # Check if correct
            if self._are_equivalent(student_expr, correct_expr):
                return self._correct_feedback(student_answer, str(correct_expr))

            # Analyze the mistake
            return self._analyze_mistake(
                problem=problem,
                student_answer=student_answer,
                student_expr=student_expr,
                correct_expr=correct_expr,
                problem_type=problem_type,
            )

        except Exception as e:
            return EducationalFeedback(
                is_correct=False,
                student_answer=student_answer,
                correct_answer="Error",
                mistake_type=None,
                explanation=f"Could not verify: {str(e)}",
                hint="Check that your answer is in the correct format",
                step_by_step_correction=[],
                difficulty_level="unknown",
                learning_resources=[],
            )

    def _safe_parse(self, expr_str: str) -> Optional[sp.Expr]:
        """Safely parse mathematical expression."""
        try:
            # Clean up common student input issues
            cleaned = expr_str.strip()
            cleaned = cleaned.replace("^", "**")  # Convert ^ to **
            cleaned = cleaned.replace("×", "*")
            cleaned = cleaned.replace("÷", "/")

            return parse_expr(cleaned, transformations=self.transformations)
        except:
            return None

    def _are_equivalent(self, expr1: sp.Expr, expr2: sp.Expr) -> bool:
        """Check if two expressions are mathematically equivalent."""
        try:
            diff = simplify(expr1 - expr2)
            return diff == 0
        except:
            return False

    def _compute_correct_answer(self, problem: str, problem_type: str) -> Optional[sp.Expr]:
        """Compute the correct answer for the problem."""
        try:
            x = symbols('x')

            if problem_type == "equation":
                # Extract equation and solve
                if "=" in problem:
                    parts = problem.split("=")
                    lhs = parse_expr(parts[0].replace("solve", "").strip(), transformations=self.transformations)
                    rhs = parse_expr(parts[1].strip(), transformations=self.transformations)
                    equation = lhs - rhs
                else:
                    equation = parse_expr(problem.replace("solve", "").strip(), transformations=self.transformations)

                solutions = solve(equation, x)
                return solutions[0] if solutions else None

            elif problem_type == "derivative":
                expr_text = problem.replace("derivative", "").replace("d/dx", "").replace("of", "").strip()
                expr = parse_expr(expr_text, transformations=self.transformations)
                return diff(expr, x)

            elif problem_type == "integral":
                expr_text = problem.replace("integral", "").replace("∫", "").replace("dx", "").strip()
                expr = parse_expr(expr_text, transformations=self.transformations)
                return integrate(expr, x)

            elif problem_type == "simplify":
                expr = parse_expr(problem.replace("simplify", "").strip(), transformations=self.transformations)
                return simplify(expr)

            return None

        except:
            return None

    def _analyze_mistake(
        self,
        problem: str,
        student_answer: str,
        student_expr: sp.Expr,
        correct_expr: sp.Expr,
        problem_type: str,
    ) -> EducationalFeedback:
        """Analyze what type of mistake the student made."""

        x = symbols('x')

        # Check for sign errors
        if self._are_equivalent(student_expr, -correct_expr):
            return EducationalFeedback(
                is_correct=False,
                student_answer=student_answer,
                correct_answer=str(correct_expr),
                mistake_type=MistakeType.SIGN_ERROR,
                explanation=f"Your answer is {student_expr}, but the correct answer is {correct_expr}. You have a sign error - your answer is negative when it should be positive (or vice versa).",
                hint="Check your signs carefully. Did you distribute a negative correctly? Did you subtract when you should have added?",
                step_by_step_correction=[
                    "1. Review each step where you worked with negative numbers",
                    "2. Check distribution: -(a+b) = -a - b (not -a + b)",
                    "3. Check subtraction: a - (b+c) = a - b - c",
                ],
                difficulty_level="easy",
                learning_resources=[
                    "Review: Working with negative numbers",
                    "Practice: Distributing negative signs",
                ],
            )

        # Check for arithmetic error (off by small amount)
        try:
            if isinstance(student_expr, (int, float, sp.Integer, sp.Float)) and \
               isinstance(correct_expr, (int, float, sp.Integer, sp.Float)):
                student_val = float(student_expr)
                correct_val = float(correct_expr)

                if abs(student_val - correct_val) < 5:
                    return EducationalFeedback(
                        is_correct=False,
                        student_answer=student_answer,
                        correct_answer=str(correct_expr),
                        mistake_type=MistakeType.ARITHMETIC_ERROR,
                        explanation=f"You got {student_expr}, but the correct answer is {correct_expr}. This looks like an arithmetic error - you were close!",
                        hint="Double-check your arithmetic. Try working through the calculation again step by step.",
                        step_by_step_correction=[
                            "1. Write out each arithmetic step clearly",
                            "2. Use a calculator to verify each operation",
                            "3. Check for order of operations (PEMDAS)",
                        ],
                        difficulty_level="easy",
                        learning_resources=[
                            "Review: Order of operations",
                            "Practice: Mental math",
                        ],
                    )
        except:
            pass

        # Check for squared vs not squared
        if self._are_equivalent(student_expr**2, correct_expr) or \
           self._are_equivalent(student_expr, correct_expr**2):
            return EducationalFeedback(
                is_correct=False,
                student_answer=student_answer,
                correct_answer=str(correct_expr),
                mistake_type=MistakeType.ALGEBRAIC_MANIPULATION,
                explanation=f"Your answer {student_expr} is related to the correct answer {correct_expr}, but you either squared when you shouldn't have, or forgot to square.",
                hint="When solving equations with squares, remember to take the square root (or square both sides correctly).",
                step_by_step_correction=[
                    "1. If equation has x², take square root of both sides",
                    "2. Remember: √(x²) = |x|, so you may have ± solutions",
                    "3. If squaring, remember: (a+b)² = a² + 2ab + b²",
                ],
                difficulty_level="medium",
                learning_resources=[
                    "Review: Solving quadratic equations",
                    "Review: Properties of square roots",
                ],
            )

        # Check if student found only one solution to quadratic
        if problem_type == "equation" and "=" in problem:
            try:
                parts = problem.split("=")
                lhs = parse_expr(parts[0].replace("solve", "").strip(), transformations=self.transformations)
                rhs = parse_expr(parts[1].strip(), transformations=self.transformations)
                equation = lhs - rhs
                all_solutions = solve(equation, x)

                if len(all_solutions) > 1 and student_expr in all_solutions:
                    other_solutions = [s for s in all_solutions if s != student_expr]
                    return EducationalFeedback(
                        is_correct=False,
                        student_answer=student_answer,
                        correct_answer=str(all_solutions),
                        mistake_type=MistakeType.INCOMPLETE_SOLUTION,
                        explanation=f"You found x = {student_expr}, which is correct! But this equation has multiple solutions: {all_solutions}. You only found one of them.",
                        hint="Quadratic equations can have 2 solutions. After finding one, check if there are more.",
                        step_by_step_correction=[
                            "1. You correctly found x = " + str(student_expr),
                            f"2. But check: the equation also has solution(s) {other_solutions}",
                            "3. For quadratics, use the quadratic formula to find ALL solutions",
                        ],
                        difficulty_level="medium",
                        learning_resources=[
                            "Review: Quadratic formula",
                            "Review: Factoring to find all roots",
                        ],
                    )
            except:
                pass

        # Generic wrong answer feedback
        return EducationalFeedback(
            is_correct=False,
            student_answer=student_answer,
            correct_answer=str(correct_expr),
            mistake_type=MistakeType.CONCEPTUAL_ERROR,
            explanation=f"Your answer {student_expr} is not correct. The correct answer is {correct_expr}.",
            hint="Review the steps you took. Compare your work to the problem type and see where you might have gone wrong.",
            step_by_step_correction=[
                f"1. The correct answer is {correct_expr}",
                "2. Work backwards: substitute the correct answer into the original problem",
                "3. See how it satisfies the equation",
                "4. Then redo your work to find where you diverged",
            ],
            difficulty_level="medium",
            learning_resources=[
                f"Review: {problem_type} problems",
                "Practice: Similar problems",
            ],
        )

    def _correct_feedback(self, student_answer: str, correct_answer: str) -> EducationalFeedback:
        """Feedback for correct answer."""
        return EducationalFeedback(
            is_correct=True,
            student_answer=student_answer,
            correct_answer=correct_answer,
            mistake_type=MistakeType.CORRECT,
            explanation="✅ Correct! Your answer is mathematically verified.",
            hint="Great job! Try a harder problem next.",
            step_by_step_correction=[],
            difficulty_level="completed",
            learning_resources=[],
        )

    def _parsing_error_feedback(self, student_answer: str) -> EducationalFeedback:
        """Feedback when answer can't be parsed."""
        return EducationalFeedback(
            is_correct=False,
            student_answer=student_answer,
            correct_answer="Unknown",
            mistake_type=None,
            explanation="Could not understand your answer format.",
            hint="Make sure to write your answer using standard math notation (e.g., x=5, not 'x equals 5')",
            step_by_step_correction=[
                "1. Write numbers clearly (use 5, not 'five')",
                "2. Use standard operators: +, -, *, /, ^",
                "3. For equations, write x = value",
            ],
            difficulty_level="unknown",
            learning_resources=["Guide: How to format math answers"],
        )

    def _unsolvable_feedback(self, problem: str) -> EducationalFeedback:
        """Feedback when problem can't be solved."""
        return EducationalFeedback(
            is_correct=False,
            student_answer="N/A",
            correct_answer="Unknown",
            mistake_type=None,
            explanation=f"Could not solve the problem: {problem}",
            hint="Check that the problem is written correctly",
            step_by_step_correction=[],
            difficulty_level="unknown",
            learning_resources=[],
        )

    def batch_verify_homework(
        self,
        problems: List[Dict[str, str]],
    ) -> List[EducationalFeedback]:
        """
        Verify multiple homework problems at once.
        Perfect for teachers grading assignments.

        Args:
            problems: List of {"problem": "...", "student_answer": "...", "type": "..."}

        Returns:
            List of EducationalFeedback for each problem
        """
        results = []
        for prob in problems:
            feedback = self.verify_homework(
                problem=prob["problem"],
                student_answer=prob["student_answer"],
                expected_answer=prob.get("expected_answer"),
                problem_type=prob.get("type", "equation"),
            )
            results.append(feedback)

        return results

    def generate_report_card(
        self,
        feedbacks: List[EducationalFeedback],
        student_name: str = "Student",
    ) -> Dict[str, Any]:
        """
        Generate a report card from homework verification.

        Args:
            feedbacks: List of EducationalFeedback from batch verification
            student_name: Student's name

        Returns:
            Report card with scores, common mistakes, recommendations
        """
        total = len(feedbacks)
        correct = sum(1 for f in feedbacks if f.is_correct)
        score = (correct / total * 100) if total > 0 else 0

        # Identify common mistakes
        mistake_counts = {}
        for feedback in feedbacks:
            if feedback.mistake_type and feedback.mistake_type != MistakeType.CORRECT:
                mistake_type = feedback.mistake_type.value
                mistake_counts[mistake_type] = mistake_counts.get(mistake_type, 0) + 1

        most_common_mistakes = sorted(
            mistake_counts.items(),
            key=lambda x: x[1],
            reverse=True,
        )[:3]

        # Difficulty analysis
        difficulty_counts = {}
        for feedback in feedbacks:
            level = feedback.difficulty_level
            difficulty_counts[level] = difficulty_counts.get(level, 0) + 1

        # Recommendations
        recommendations = []
        if "sign_error" in [m[0] for m in most_common_mistakes]:
            recommendations.append("📚 Review: Distributing negative signs")
        if "arithmetic_error" in [m[0] for m in most_common_mistakes]:
            recommendations.append("🔢 Practice: Mental math and arithmetic")
        if "incomplete_solution" in [m[0] for m in most_common_mistakes]:
            recommendations.append("🎯 Remember: Check for multiple solutions")
        if "algebraic_manipulation" in [m[0] for m in most_common_mistakes]:
            recommendations.append("📐 Review: Algebraic rules and properties")

        return {
            "student_name": student_name,
            "score": f"{score:.1f}%",
            "correct": correct,
            "total": total,
            "incorrect": total - correct,
            "most_common_mistakes": [
                f"{mistake.replace('_', ' ').title()}: {count} times"
                for mistake, count in most_common_mistakes
            ],
            "difficulty_breakdown": difficulty_counts,
            "recommendations": recommendations,
            "summary": self._generate_summary(score, total, correct),
        }

    def _generate_summary(self, score: float, total: int, correct: int) -> str:
        """Generate summary text for report card."""
        if score >= 90:
            return f"🌟 Excellent work! You got {correct}/{total} correct ({score:.1f}%). Keep it up!"
        elif score >= 80:
            return f"👍 Good job! You got {correct}/{total} correct ({score:.1f}%). Review the mistakes to improve."
        elif score >= 70:
            return f"📚 Fair work. You got {correct}/{total} correct ({score:.1f}%). Focus on the common mistakes identified."
        elif score >= 60:
            return f"⚠️ Needs improvement. You got {correct}/{total} correct ({score:.1f}%). Review the concepts and practice more."
        else:
            return f"🔴 Struggling. You got {correct}/{total} correct ({score:.1f}%). Seek help from teacher and review fundamentals."
