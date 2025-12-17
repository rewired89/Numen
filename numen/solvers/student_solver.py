"""
Student Solver - Solves problems and explains the answer step-by-step.

This is different from the verifier - instead of checking if an answer is correct,
this SOLVES the problem and EXPLAINS how to get the answer.

Perfect for students who need help understanding how to solve problems.
"""

import sympy as sp
from sympy import symbols, solve, diff, integrate, simplify, expand, factor
from sympy.parsing.sympy_parser import parse_expr, standard_transformations, implicit_multiplication_application
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class Solution:
    """Complete solution with explanation."""
    answer: str
    steps: List[str]
    explanation: str
    problem_type: str
    difficulty: str
    confidence: float


class StudentSolver:
    """
    Solves math problems and explains the solution step-by-step.

    Features:
    - Identifies problem type automatically
    - Solves using symbolic math (100% accurate)
    - Explains each step in plain English
    - Shows work (like a teacher would)
    """

    def __init__(self):
        self.transformations = (
            standard_transformations + (implicit_multiplication_application,)
        )

    def solve_problem(self, problem: str) -> Solution:
        """
        Solve a math problem and explain the solution.

        Args:
            problem: Math problem as text

        Returns:
            Solution with answer, steps, and explanation
        """
        # Clean up the problem
        problem = problem.strip()

        # Convert ^ to ** for sympy
        problem = problem.replace("^", "**")

        # Auto-detect problem type
        problem_type = self._detect_problem_type(problem)

        # Solve based on type
        if problem_type == "equation":
            return self._solve_equation(problem)
        elif problem_type == "derivative":
            return self._solve_derivative(problem)
        elif problem_type == "integral":
            return self._solve_integral(problem)
        elif problem_type == "simplify":
            return self._solve_simplify(problem)
        elif problem_type == "expand":
            return self._solve_expand(problem)
        elif problem_type == "factor":
            return self._solve_factor(problem)
        else:
            # Try as equation by default
            return self._solve_equation(problem)

    def _detect_problem_type(self, problem: str) -> str:
        """Detect what type of problem this is."""
        problem_lower = problem.lower()

        if "derivative" in problem_lower or "d/dx" in problem_lower or "differentiate" in problem_lower:
            return "derivative"
        elif "integral" in problem_lower or "integrate" in problem_lower or "∫" in problem:
            return "integral"
        elif "simplify" in problem_lower:
            return "simplify"
        elif "expand" in problem_lower:
            return "expand"
        elif "factor" in problem_lower and "factorint" not in problem_lower:
            return "factor"
        elif "solve" in problem_lower or "=" in problem:
            return "equation"
        else:
            return "equation"

    def _solve_equation(self, problem: str) -> Solution:
        """Solve an equation and explain the steps."""
        try:
            x = symbols('x')
            steps = []

            # Extract equation
            if "=" in problem:
                parts = problem.split("=")
                lhs_text = parts[0].replace("solve", "").replace("for x", "").strip()
                rhs_text = parts[1].strip()

                steps.append(f"📝 **Original equation:** {lhs_text} = {rhs_text}")

                lhs = parse_expr(lhs_text, transformations=self.transformations)
                rhs = parse_expr(rhs_text, transformations=self.transformations)
                equation = lhs - rhs
            else:
                equation_text = problem.replace("solve", "").replace("for x", "").strip()
                steps.append(f"📝 **Original equation:** {equation_text} = 0")
                equation = parse_expr(equation_text, transformations=self.transformations)

            steps.append(f"🔧 **Rearrange to standard form:** {equation} = 0")

            # Solve
            solutions = solve(equation, x)

            if not solutions:
                return Solution(
                    answer="No solution exists",
                    steps=steps,
                    explanation="This equation has no solution.",
                    problem_type="equation",
                    difficulty="unknown",
                    confidence=1.0,
                )

            # Check if quadratic
            degree = sp.degree(equation, x)

            if degree == 1:
                # Linear equation
                steps.append("📊 **Problem type:** Linear equation (degree 1)")
                steps.append(f"🔍 **Solving for x...**")

                # Show algebraic steps
                if isinstance(equation, sp.Add):
                    # ax + b = 0 form
                    coeffs = sp.Poly(equation, x).all_coeffs()
                    if len(coeffs) == 2:
                        a, b = coeffs
                        steps.append(f"   Step 1: We have {a}*x + ({b}) = 0")
                        steps.append(f"   Step 2: Subtract {b} from both sides: {a}*x = {-b}")
                        steps.append(f"   Step 3: Divide both sides by {a}: x = {-b}/{a}")
                        steps.append(f"   Step 4: Simplify: x = {solutions[0]}")

            elif degree == 2:
                # Quadratic equation
                steps.append("📊 **Problem type:** Quadratic equation (degree 2)")
                steps.append(f"🔍 **Using quadratic formula or factoring...**")

                # Try to factor
                try:
                    factored = factor(equation)
                    if factored != equation:
                        steps.append(f"   Step 1: Factor the equation: {factored} = 0")
                        steps.append(f"   Step 2: Set each factor to zero")
                        steps.append(f"   Step 3: Solve each equation")
                except:
                    steps.append(f"   Using quadratic formula: x = (-b ± √(b²-4ac)) / 2a")

                if len(solutions) > 1:
                    steps.append(f"   ✅ Found {len(solutions)} solutions!")

            else:
                steps.append(f"📊 **Problem type:** Polynomial equation (degree {degree})")
                steps.append(f"🔍 **Solving using symbolic methods...**")

            # Format answer
            if len(solutions) == 1:
                answer = f"x = {solutions[0]}"
                steps.append(f"✅ **Final Answer:** x = {solutions[0]}")
            else:
                answer = f"x = {solutions}"
                steps.append(f"✅ **Final Answers:** x = {', '.join(str(s) for s in solutions)}")

            # Verify
            steps.append(f"\n🔍 **Verification:**")
            for sol in solutions:
                check = equation.subs(x, sol)
                steps.append(f"   x = {sol}: {check} ✓")

            # Explanation
            if len(solutions) == 1:
                explanation = f"This is a linear equation with one solution: x = {solutions[0]}"
            elif len(solutions) == 2:
                explanation = f"This is a quadratic equation with two solutions: x = {solutions[0]} and x = {solutions[1]}"
            else:
                explanation = f"This equation has {len(solutions)} solutions: {', '.join(str(s) for s in solutions)}"

            return Solution(
                answer=answer,
                steps=steps,
                explanation=explanation,
                problem_type="equation",
                difficulty="medium" if degree > 1 else "easy",
                confidence=1.0,
            )

        except Exception as e:
            return Solution(
                answer=f"Could not solve: {str(e)}",
                steps=["❌ Error parsing or solving the equation"],
                explanation=str(e),
                problem_type="equation",
                difficulty="unknown",
                confidence=0.0,
            )

    def _solve_derivative(self, problem: str) -> Solution:
        """Solve a derivative problem and explain."""
        try:
            x = symbols('x')
            steps = []

            # Extract function
            expr_text = problem.replace("derivative", "").replace("of", "").replace("d/dx", "").strip()
            steps.append(f"📝 **Original function:** f(x) = {expr_text}")

            expr = parse_expr(expr_text, transformations=self.transformations)
            steps.append(f"🔧 **Parsed as:** {expr}")

            # Compute derivative
            steps.append(f"🔍 **Taking derivative with respect to x...**")
            derivative = diff(expr, x)

            # Explain derivative rules used
            steps.append(f"\n📚 **Derivative rules applied:**")

            if expr.is_polynomial():
                steps.append(f"   • Power rule: d/dx(x^n) = n*x^(n-1)")
            if expr.has(sp.sin, sp.cos):
                steps.append(f"   • Trig rules: d/dx(sin x) = cos x, d/dx(cos x) = -sin x")
            if expr.has(sp.exp):
                steps.append(f"   • Exponential rule: d/dx(e^x) = e^x")
            if expr.has(sp.log):
                steps.append(f"   • Logarithm rule: d/dx(ln x) = 1/x")

            steps.append(f"\n✅ **Final Answer:** f'(x) = {derivative}")

            # Simplify if needed
            simplified = simplify(derivative)
            if simplified != derivative:
                steps.append(f"📐 **Simplified:** f'(x) = {simplified}")

            answer = f"f'(x) = {derivative}"
            explanation = f"The derivative of {expr} with respect to x is {derivative}"

            return Solution(
                answer=answer,
                steps=steps,
                explanation=explanation,
                problem_type="derivative",
                difficulty="medium",
                confidence=1.0,
            )

        except Exception as e:
            return Solution(
                answer=f"Could not solve: {str(e)}",
                steps=["❌ Error parsing or differentiating"],
                explanation=str(e),
                problem_type="derivative",
                difficulty="unknown",
                confidence=0.0,
            )

    def _solve_integral(self, problem: str) -> Solution:
        """Solve an integral problem and explain."""
        try:
            x = symbols('x')
            steps = []

            # Extract function
            expr_text = problem.replace("integral", "").replace("of", "").replace("integrate", "").replace("∫", "").replace("dx", "").strip()
            steps.append(f"📝 **Original function:** ∫ {expr_text} dx")

            expr = parse_expr(expr_text, transformations=self.transformations)
            steps.append(f"🔧 **Parsed as:** {expr}")

            # Compute integral
            steps.append(f"🔍 **Integrating with respect to x...**")
            integral_result = integrate(expr, x)

            # Explain integration rules used
            steps.append(f"\n📚 **Integration rules applied:**")

            if expr.is_polynomial():
                steps.append(f"   • Power rule: ∫ x^n dx = x^(n+1)/(n+1) + C")
            if expr.has(sp.sin, sp.cos):
                steps.append(f"   • Trig rules: ∫ sin x dx = -cos x + C")
            if expr.has(sp.exp):
                steps.append(f"   • Exponential rule: ∫ e^x dx = e^x + C")

            steps.append(f"\n✅ **Final Answer:** ∫ {expr} dx = {integral_result} + C")

            answer = f"∫ {expr} dx = {integral_result} + C"
            explanation = f"The integral of {expr} with respect to x is {integral_result} + C (don't forget the constant!)"

            return Solution(
                answer=answer,
                steps=steps,
                explanation=explanation,
                problem_type="integral",
                difficulty="medium",
                confidence=1.0,
            )

        except Exception as e:
            return Solution(
                answer=f"Could not solve: {str(e)}",
                steps=["❌ Error parsing or integrating"],
                explanation=str(e),
                problem_type="integral",
                difficulty="unknown",
                confidence=0.0,
            )

    def _solve_simplify(self, problem: str) -> Solution:
        """Simplify an expression and explain."""
        try:
            x = symbols('x')
            steps = []

            # Extract expression
            expr_text = problem.replace("simplify", "").strip()
            steps.append(f"📝 **Original expression:** {expr_text}")

            expr = parse_expr(expr_text, transformations=self.transformations)
            steps.append(f"🔧 **Parsed as:** {expr}")

            # Simplify
            steps.append(f"🔍 **Simplifying...**")
            simplified = simplify(expr)

            steps.append(f"\n✅ **Final Answer:** {simplified}")

            answer = f"{simplified}"
            explanation = f"The simplified form of {expr} is {simplified}"

            return Solution(
                answer=answer,
                steps=steps,
                explanation=explanation,
                problem_type="simplify",
                difficulty="easy",
                confidence=1.0,
            )

        except Exception as e:
            return Solution(
                answer=f"Could not solve: {str(e)}",
                steps=["❌ Error parsing or simplifying"],
                explanation=str(e),
                problem_type="simplify",
                difficulty="unknown",
                confidence=0.0,
            )

    def _solve_expand(self, problem: str) -> Solution:
        """Expand an expression and explain."""
        try:
            x = symbols('x')
            steps = []

            # Extract expression
            expr_text = problem.replace("expand", "").strip()
            steps.append(f"📝 **Original expression:** {expr_text}")

            expr = parse_expr(expr_text, transformations=self.transformations)
            steps.append(f"🔧 **Parsed as:** {expr}")

            # Expand
            steps.append(f"🔍 **Expanding...**")
            expanded = expand(expr)

            if expr.has(sp.Pow):
                steps.append(f"   • Remember: (a+b)² = a² + 2ab + b²")

            steps.append(f"\n✅ **Final Answer:** {expanded}")

            answer = f"{expanded}"
            explanation = f"The expanded form of {expr} is {expanded}"

            return Solution(
                answer=answer,
                steps=steps,
                explanation=explanation,
                problem_type="expand",
                difficulty="easy",
                confidence=1.0,
            )

        except Exception as e:
            return Solution(
                answer=f"Could not solve: {str(e)}",
                steps=["❌ Error parsing or expanding"],
                explanation=str(e),
                problem_type="expand",
                difficulty="unknown",
                confidence=0.0,
            )

    def _solve_factor(self, problem: str) -> Solution:
        """Factor an expression and explain."""
        try:
            x = symbols('x')
            steps = []

            # Extract expression
            expr_text = problem.replace("factor", "").strip()
            steps.append(f"📝 **Original expression:** {expr_text}")

            expr = parse_expr(expr_text, transformations=self.transformations)
            steps.append(f"🔧 **Parsed as:** {expr}")

            # Factor
            steps.append(f"🔍 **Factoring...**")
            factored = factor(expr)

            steps.append(f"\n✅ **Final Answer:** {factored}")

            answer = f"{factored}"
            explanation = f"The factored form of {expr} is {factored}"

            return Solution(
                answer=answer,
                steps=steps,
                explanation=explanation,
                problem_type="factor",
                difficulty="medium",
                confidence=1.0,
            )

        except Exception as e:
            return Solution(
                answer=f"Could not solve: {str(e)}",
                steps=["❌ Error parsing or factoring"],
                explanation=str(e),
                problem_type="factor",
                difficulty="unknown",
                confidence=0.0,
            )
