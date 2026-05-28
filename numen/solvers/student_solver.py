"""
Student Solver - Solves problems and explains the answer step-by-step.
"""

import re
import sympy as sp
from sympy import symbols, solve, diff, integrate, simplify, expand, factor, limit, oo, E, pi, I
from sympy.parsing.sympy_parser import parse_expr, standard_transformations, implicit_multiplication_application
from typing import List, Optional
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


# Unicode superscript → ASCII digit mapping
_SUPERSCRIPT_MAP = {
    '⁰': '0', '¹': '1', '²': '2', '³': '3', '⁴': '4',
    '⁵': '5', '⁶': '6', '⁷': '7', '⁸': '8', '⁹': '9',
}


def _replace_superscripts(text: str) -> str:
    """Convert x² → x**2, x³ → x**3, etc. (handles consecutive digits)."""
    result = []
    i = 0
    while i < len(text):
        if text[i] in _SUPERSCRIPT_MAP:
            digits = []
            while i < len(text) and text[i] in _SUPERSCRIPT_MAP:
                digits.append(_SUPERSCRIPT_MAP[text[i]])
                i += 1
            result.append('**' + ''.join(digits))
        else:
            result.append(text[i])
            i += 1
    return ''.join(result)


class StudentSolver:
    """Solves math problems and explains the solution step-by-step."""

    def __init__(self):
        self.transformations = (
            standard_transformations + (implicit_multiplication_application,)
        )
        self.local_dict = {'e': E, 'pi': pi, 'i': I, 'inf': oo, 'infinity': oo}

    # ------------------------------------------------------------------ #
    # Preprocessing helpers                                                #
    # ------------------------------------------------------------------ #

    def _fix_notation(self, problem: str) -> str:
        """Normalize math notation so the parser handles it correctly."""
        # Unicode superscripts: x² → x**2
        problem = _replace_superscripts(problem)
        # Partial derivative symbol ∂ — convert to plain-English form the solver understands
        # ∂(expr)/∂x  or  ∂expr/∂x  →  derivative of expr with respect to x
        problem = re.sub(
            r'∂\s*\(([^)]+)\)\s*/\s*∂\s*([a-zA-Z])',
            lambda m: f'derivative of {m.group(1)} with respect to {m.group(2)}',
            problem,
        )
        problem = re.sub(
            r'∂\s*([\w][\w\s^*/+-]*?)\s*/\s*∂\s*([a-zA-Z])',
            lambda m: f'derivative of {m.group(1).strip()} with respect to {m.group(2)}',
            problem,
        )
        # ∂/∂x [of] expr  →  derivative with respect to x of expr
        problem = re.sub(
            r'∂\s*/\s*∂\s*([a-zA-Z])\s+(?:of\s+)?',
            lambda m: f'derivative with respect to {m.group(1)} of ',
            problem,
        )
        # Any remaining bare ∂ → 'd' so it doesn't crash the parser
        problem = problem.replace('∂', 'd')
        # d(expr)/dx  →  derivative of expr with respect to x
        problem = re.sub(
            r'\bd\s*\(([^)]+)\)\s*/\s*d([a-zA-Z])\b',
            lambda m: f'derivative of {m.group(1)} with respect to {m.group(2)}',
            problem, flags=re.IGNORECASE,
        )
        # Unicode integral symbol ∫ already handled downstream, leave it
        # Unicode arrows / operators
        problem = problem.replace('→', '->').replace('—>', '->')
        problem = problem.replace('≤', '<=').replace('≥', '>=')
        # Standalone e^ → exp(  )
        problem = re.sub(r'\be\^', 'E^', problem)
        problem = re.sub(r'\be\*\*', 'E**', problem)
        # lim_{x->0} → lim x->0
        problem = re.sub(r'lim_\{([^}]+)\}', r'lim \1', problem, flags=re.IGNORECASE)
        # "x approaches" → "x ->"
        problem = re.sub(r'x\s+approaches\s+', 'x -> ', problem, flags=re.IGNORECASE)
        # Strip trailing period
        problem = problem.rstrip('.')
        return problem

    def _safe_parse(self, expr_str: str) -> sp.Expr:
        """Parse a math expression string into a SymPy expression."""
        cleaned = expr_str.strip().replace('^', '**')
        # Strip leading colon or equals that might remain after keyword removal
        cleaned = re.sub(r'^[\s:=]+', '', cleaned)
        # Auto-balance parentheses
        open_c = cleaned.count('(')
        close_c = cleaned.count(')')
        if open_c > close_c:
            cleaned += ')' * (open_c - close_c)
        elif close_c > open_c:
            cleaned = '(' * (close_c - open_c) + cleaned
        return parse_expr(cleaned, local_dict=self.local_dict,
                          transformations=self.transformations)

    def _split_equations(self, text: str) -> List[str]:
        """Split on 'and' or top-level commas or newlines (respects paren depth)."""
        parts: List[str] = []
        depth = 0
        current: List[str] = []
        i = 0
        while i < len(text):
            c = text[i]
            if c == '(':
                depth += 1
                current.append(c)
            elif c == ')':
                depth = max(0, depth - 1)
                current.append(c)
            elif depth == 0:
                m = re.match(r'[\s\n]+and[\s\n]+', text[i:], re.IGNORECASE)
                if m:
                    parts.append(''.join(current).strip())
                    current = []
                    i += len(m.group(0))
                    continue
                elif c in (',', '\n', ';'):
                    tok = ''.join(current).strip()
                    if tok:
                        parts.append(tok)
                    current = []
                else:
                    current.append(c)
            else:
                current.append(c)
            i += 1
        tok = ''.join(current).strip()
        if tok:
            parts.append(tok)
        return [p for p in parts if p]

    def _strip_noise_words(self, text: str) -> str:
        """Remove common English words that are not part of the math expression."""
        noise = [
            'find', 'compute', 'calculate', 'evaluate',
            'what is', 'determine', 'please', 'me',
        ]
        result = text
        for w in noise:
            result = re.sub(r'\b' + re.escape(w) + r'\b', ' ', result, flags=re.IGNORECASE)
        return re.sub(r'\s+', ' ', result).strip()

    def _has_top_level_separator(self, problem: str) -> bool:
        """True if 'and', comma, newline, or semicolon appears outside parentheses."""
        depth = 0
        i = 0
        while i < len(problem):
            c = problem[i]
            if c == '(':
                depth += 1
            elif c == ')':
                depth = max(0, depth - 1)
            elif depth == 0:
                if re.match(r'[\s\n]+and[\s\n]+', problem[i:], re.IGNORECASE):
                    return True
                if c in (',', '\n', ';'):
                    return True
            i += 1
        return False

    # ------------------------------------------------------------------ #
    # Problem type detection                                               #
    # ------------------------------------------------------------------ #

    def _detect_problem_type(self, problem: str) -> str:
        """Return the problem category string."""
        p = problem.lower()

        # antiderivative must come before derivative (it contains the word)
        if 'antiderivative' in p:
            return 'integral'

        # Second derivative
        if re.search(r"second\s+derivative|d[²2]\s*/\s*dx[²2]|d\^2\s*/\s*dx\^2", p):
            return 'second_derivative'

        # Derivatives / differentiation (∂ checked on original problem before _fix_notation)
        if ('derivative' in p or 'd/dx' in p or 'd/dy' in p or 'd/dz' in p
                or 'differentiate' in p or 'partial' in p
                or '∂' in problem  # raw unicode partial symbol
                or re.search(r'\bd\s*\(', p)):
            return 'derivative'

        # Integrals
        if 'integral' in p or 'integrate' in p or '∫' in problem:
            return 'integral'

        # Limits – accept "limit", "lim" with any -> or "approaches"
        if re.search(r'\b(limit|lim)\b', p) and (
            '->' in problem or '→' in problem or 'approaches' in p
        ):
            return 'limit'

        # System of equations
        if ('solve' in p or '=' in problem) and self._has_top_level_separator(problem):
            if any(v in p for v in ['y', 'z']):
                return 'system'

        # Simplify / expand / factor
        if 'simplify' in p:
            return 'simplify'
        if 'expand' in p:
            return 'expand'
        if 'factor' in p and 'factorint' not in p:
            return 'factor'

        # Default: single equation
        return 'equation'

    # ------------------------------------------------------------------ #
    # Solvers                                                              #
    # ------------------------------------------------------------------ #

    def solve_problem(self, problem: str) -> Solution:
        """Solve a math problem and return an explained Solution."""
        problem = problem.strip()
        problem = self._fix_notation(problem)
        ptype = self._detect_problem_type(problem)
        dispatch = {
            'limit':             self._solve_limit,
            'system':            self._solve_system,
            'equation':          self._solve_equation,
            'derivative':        self._solve_derivative,
            'second_derivative': self._solve_second_derivative,
            'integral':          self._solve_integral,
            'simplify':          self._solve_simplify,
            'expand':            self._solve_expand,
            'factor':            self._solve_factor,
        }
        return dispatch.get(ptype, self._solve_equation)(problem)

    # ---- Equation ---------------------------------------------------- #

    def _solve_equation(self, problem: str) -> Solution:
        """Solve a single equation for its unknown variable."""
        try:
            steps = []

            # Strip common prefixes: "solve", "find x", "for x:", etc.
            clean = problem
            clean = re.sub(r'\bsolve\b', '', clean, flags=re.IGNORECASE)
            clean = re.sub(r'\bfor\s+\w+\s*:', '', clean, flags=re.IGNORECASE)
            clean = re.sub(r'\bfor\s+\w+\b', '', clean, flags=re.IGNORECASE)
            clean = self._strip_noise_words(clean).strip()

            if '=' in clean:
                lhs_text, rhs_text = clean.split('=', 1)
                steps.append(f"📝 **Original equation:** {lhs_text.strip()} = {rhs_text.strip()}")
                lhs = self._safe_parse(lhs_text)
                rhs = self._safe_parse(rhs_text)
                equation = lhs - rhs
            else:
                steps.append(f"📝 **Original expression:** {clean} = 0")
                equation = self._safe_parse(clean)

            steps.append(f"🔧 **Standard form:** {equation} = 0")

            # Pick the variable to solve for from the equation's own symbols
            # (IMPORTANT: never create a separate symbol — it would be a different object)
            free_syms = sorted(equation.free_symbols, key=str)
            priority = ['x', 'y', 'z', 't', 'n']
            solve_var = next(
                (s for name in priority for s in free_syms if str(s) == name),
                free_syms[0] if free_syms else symbols('x'),
            )

            # Absolute-value equations need a real-domain solve
            if equation.has(sp.Abs):
                real_var = sp.Symbol(str(solve_var), real=True)
                eq_real = equation.xreplace({solve_var: real_var})
                solutions = list(sp.solveset(eq_real, real_var, domain=sp.S.Reals))
            else:
                solutions = solve(equation, solve_var)

            if not solutions:
                return Solution(
                    answer="No solution exists",
                    steps=steps,
                    explanation="This equation has no solution.",
                    problem_type="equation", difficulty="unknown", confidence=1.0,
                )

            vname = str(solve_var)

            # Determine equation type (safe — won't crash on transcendental)
            try:
                degree = int(sp.degree(equation, solve_var))
            except Exception:
                degree = -1  # transcendental / rational

            if degree == 1:
                steps.append("📊 **Type:** Linear equation")
                steps.append(f"🔍 **Isolating {vname}...**")
                try:
                    coeffs = sp.Poly(equation, solve_var).all_coeffs()
                    if len(coeffs) == 2:
                        a, b = coeffs
                        steps.append(f"   {a}·{vname} + {b} = 0")
                        steps.append(f"   {vname} = {simplify(-b/a)}")
                except Exception:
                    pass
            elif degree == 2:
                steps.append("📊 **Type:** Quadratic equation")
                steps.append("🔍 **Factoring or using quadratic formula...**")
                try:
                    factored = factor(equation)
                    if factored != equation:
                        steps.append(f"   Factored: {factored} = 0")
                except Exception:
                    steps.append(f"   {vname} = (−b ± √(b²−4ac)) / 2a")
            elif degree > 2:
                steps.append(f"📊 **Type:** Polynomial (degree {degree})")
                steps.append("🔍 **Solving symbolically...**")
            else:
                if equation.has(sp.exp) or equation.has(sp.log):
                    steps.append("📊 **Type:** Exponential / logarithmic equation")
                    steps.append("🔍 **Applying inverse functions...**")
                elif equation.has(sp.sin) or equation.has(sp.cos) or equation.has(sp.tan):
                    steps.append("📊 **Type:** Trigonometric equation")
                    steps.append("🔍 **Solving trigonometric equation...**")
                elif equation.has(sp.Abs):
                    steps.append("📊 **Type:** Absolute value equation")
                    steps.append("🔍 **Splitting into cases...**")
                else:
                    steps.append("📊 **Type:** Rational / general equation")
                    steps.append("🔍 **Solving symbolically...**")

            # Format answer
            sol_list = list(solutions)
            if len(sol_list) == 1:
                answer = f"{vname} = {sol_list[0]}"
                steps.append(f"\n✅ **Answer:** {answer}")
            else:
                sol_str = ', '.join(str(s) for s in sol_list)
                answer = f"{vname} = {sol_str}"
                steps.append(f"\n✅ **Answers:** {answer}")

            # Verification
            steps.append("\n🔍 **Verification:**")
            for sol in sol_list[:4]:
                try:
                    check = simplify(equation.subs(solve_var, sol))
                    steps.append(f"   {vname} = {sol} → {check} ✓")
                except Exception:
                    pass

            n = len(sol_list)
            explanation = (
                f"The equation has {'one solution' if n == 1 else f'{n} solutions'}: {answer}."
            )
            return Solution(
                answer=answer, steps=steps, explanation=explanation,
                problem_type="equation",
                difficulty="easy" if degree == 1 else "medium",
                confidence=1.0,
            )

        except Exception as e:
            return Solution(
                answer=f"Could not solve: {str(e)}",
                steps=["❌ Error solving the equation",
                       "💡 Make sure variables and operators are clear, e.g. 'solve 2x + 3 = 7'"],
                explanation=str(e), problem_type="equation",
                difficulty="unknown", confidence=0.0,
            )

    # ---- Derivative -------------------------------------------------- #

    def _solve_derivative(self, problem: str) -> Solution:
        """Compute the first derivative of a function."""
        try:
            steps = []

            # Detect "with respect to <var>"
            wrt = re.search(r'with\s+respect\s+to\s+(\w+)', problem, re.IGNORECASE)
            var_name = wrt.group(1) if wrt else 'x'
            var = symbols(var_name)

            # Strip all derivative keywords
            expr_text = problem
            expr_text = re.sub(r'\bpartial\s+derivative\b', '', expr_text, flags=re.IGNORECASE)
            expr_text = re.sub(r'\bderivative\b', '', expr_text, flags=re.IGNORECASE)
            expr_text = re.sub(r'\bdifferentiate\b', '', expr_text, flags=re.IGNORECASE)
            expr_text = re.sub(r'\bd/d[a-z]\b', '', expr_text, flags=re.IGNORECASE)
            expr_text = re.sub(r'\bwith\s+respect\s+to\s+\w+\b', '', expr_text, flags=re.IGNORECASE)
            expr_text = re.sub(r'\bof\b', '', expr_text, flags=re.IGNORECASE)
            expr_text = self._strip_noise_words(expr_text).strip()

            steps.append(f"📝 **Function:** f({var_name}) = {expr_text}")
            expr = self._safe_parse(expr_text)
            steps.append(f"🔧 **Parsed:** {expr}")
            steps.append(f"🔍 **Differentiating with respect to {var_name}...**")

            result = diff(expr, var)

            steps.append("\n📚 **Rules applied:**")
            if expr.is_polynomial(var):
                steps.append(f"   • Power rule: d/d{var_name}(x^n) = n·x^(n−1)")
            if expr.has(sp.sin) or expr.has(sp.cos):
                steps.append("   • Trig: d/dx(sin x) = cos x,  d/dx(cos x) = −sin x")
            if expr.has(sp.exp):
                steps.append("   • Exponential: d/dx(eˣ) = eˣ")
            if expr.has(sp.log):
                steps.append("   • Logarithm: d/dx(ln x) = 1/x")

            simplified = simplify(result)
            display = simplified if simplified != result else result
            steps.append(f"\n✅ **f'({var_name}) = {display}**")

            return Solution(
                answer=f"f'({var_name}) = {display}",
                steps=steps,
                explanation=f"The derivative of {expr} with respect to {var_name} is {display}.",
                problem_type="derivative", difficulty="medium", confidence=1.0,
            )

        except Exception as e:
            return Solution(
                answer=f"Could not differentiate: {str(e)}",
                steps=["❌ Error computing derivative",
                       "💡 Try: 'derivative of x^3 + 2x' or 'derivative of sin(x)*cos(x)'"],
                explanation=str(e), problem_type="derivative",
                difficulty="unknown", confidence=0.0,
            )

    # ---- Second derivative ------------------------------------------- #

    def _solve_second_derivative(self, problem: str) -> Solution:
        """Compute the second derivative of a function."""
        try:
            steps = []
            var_name = 'x'
            var = symbols(var_name)

            # Strip all second-derivative keywords
            expr_text = problem
            expr_text = re.sub(r'\bsecond\s+derivative\b', '', expr_text, flags=re.IGNORECASE)
            expr_text = re.sub(r'd[²2]\s*/\s*dx[²2]', '', expr_text, flags=re.IGNORECASE)
            expr_text = re.sub(r'd\^2\s*/\s*dx\^2', '', expr_text, flags=re.IGNORECASE)
            expr_text = re.sub(r'\bderivative\b', '', expr_text, flags=re.IGNORECASE)
            expr_text = re.sub(r'\bof\b', '', expr_text, flags=re.IGNORECASE)
            expr_text = self._strip_noise_words(expr_text).strip()

            steps.append(f"📝 **Function:** f(x) = {expr_text}")
            expr = self._safe_parse(expr_text)
            steps.append(f"🔧 **Parsed:** {expr}")

            first = diff(expr, var)
            steps.append(f"🔍 **First derivative:** f'(x) = {first}")
            second = diff(first, var)
            simplified = simplify(second)
            steps.append(f"🔍 **Second derivative:** f''(x) = {simplified}")
            steps.append(f"\n✅ **f''(x) = {simplified}**")

            return Solution(
                answer=f"f''(x) = {simplified}",
                steps=steps,
                explanation=f"The second derivative of {expr} is {simplified}.",
                problem_type="derivative", difficulty="medium", confidence=1.0,
            )

        except Exception as e:
            return Solution(
                answer=f"Could not compute second derivative: {str(e)}",
                steps=["❌ Error", "💡 Try: 'second derivative of x^4'"],
                explanation=str(e), problem_type="derivative",
                difficulty="unknown", confidence=0.0,
            )

    # ---- Integral ---------------------------------------------------- #

    def _solve_integral(self, problem: str) -> Solution:
        """Compute an indefinite or definite integral."""
        try:
            steps = []

            # Integration variable
            wrt = re.search(r'with\s+respect\s+to\s+(\w+)', problem, re.IGNORECASE)
            var_name = wrt.group(1) if wrt else 'x'
            var = symbols(var_name)

            # Definite integral bounds: "from a to b"
            bounds = re.search(
                r'\bfrom\s+(.+?)\s+to\s+([^\s,;]+(?:\s[^\s,;]+)*?)\s*$',
                problem, re.IGNORECASE,
            )
            lower = upper = None
            if bounds:
                lower, upper = bounds.group(1).strip(), bounds.group(2).strip()

            # Strip keywords
            expr_text = problem
            if bounds:
                expr_text = expr_text[:bounds.start()]
            expr_text = re.sub(r'\bwith\s+respect\s+to\s+\w+\b', '', expr_text, flags=re.IGNORECASE)
            expr_text = re.sub(r'\bantiderivative\b', '', expr_text, flags=re.IGNORECASE)
            for kw in ['integral', 'integrate', 'indefinite', 'definite']:
                expr_text = re.sub(r'\b' + kw + r'\b', '', expr_text, flags=re.IGNORECASE)
            expr_text = re.sub(r'\bof\b', '', expr_text, flags=re.IGNORECASE)
            expr_text = re.sub(r'\bd' + var_name + r'\b', '', expr_text, flags=re.IGNORECASE)
            expr_text = re.sub(r'∫', '', expr_text)
            expr_text = self._strip_noise_words(expr_text).strip()

            if lower and upper:
                steps.append(f"📝 **Definite integral:** ∫[{lower} to {upper}] {expr_text} d{var_name}")
            else:
                steps.append(f"📝 **Indefinite integral:** ∫ {expr_text} d{var_name}")

            expr = self._safe_parse(expr_text)
            steps.append(f"🔧 **Parsed:** {expr}")

            steps.append("\n📚 **Rules applied:**")
            if expr.is_polynomial(var):
                steps.append("   • Power rule: ∫ xⁿ dx = x^(n+1)/(n+1) + C")
            if expr.has(sp.sin) or expr.has(sp.cos):
                steps.append("   • Trig: ∫ sin x dx = −cos x + C")
            if expr.has(sp.exp):
                steps.append("   • Exponential: ∫ eˣ dx = eˣ + C")
            if expr.has(sp.log):
                steps.append("   • Logarithm: ∫ 1/x dx = ln|x| + C")

            if lower and upper:
                steps.append(f"🔍 **Evaluating from {lower} to {upper}...**")
                a_val = self._safe_parse(lower)
                b_val = self._safe_parse(upper)
                result = simplify(integrate(expr, (var, a_val, b_val)))
                steps.append(f"\n✅ **Answer:** ∫[{lower} to {upper}] {expr} d{var_name} = {result}")
                answer = f"∫[{lower} to {upper}] {expr} d{var_name} = {result}"
                explanation = (
                    f"The definite integral of {expr} from {lower} to {upper} equals {result}."
                )
            else:
                steps.append(f"🔍 **Integrating with respect to {var_name}...**")
                result = integrate(expr, var)
                steps.append(f"\n✅ **Answer:** ∫ {expr} d{var_name} = {result} + C")
                answer = f"∫ {expr} d{var_name} = {result} + C"
                explanation = f"The integral of {expr} is {result} + C."

            return Solution(
                answer=answer, steps=steps, explanation=explanation,
                problem_type="integral", difficulty="medium", confidence=1.0,
            )

        except Exception as e:
            return Solution(
                answer=f"Could not integrate: {str(e)}",
                steps=["❌ Error computing integral",
                       "💡 Try: 'integral of x^2' or 'integral of sin(x) from 0 to pi'"],
                explanation=str(e), problem_type="integral",
                difficulty="unknown", confidence=0.0,
            )

    # ---- Limit ------------------------------------------------------- #

    def _solve_limit(self, problem: str) -> Solution:
        """Compute a limit."""
        try:
            x = symbols('x')
            steps = []
            steps.append(f"📝 **Problem:** {problem}")

            expr_text, point_text = None, None

            # Pattern 1: "lim x->a f(x)"  or  "lim x->a of f(x)"
            m = re.search(
                r'\blim\w*\s+x\s*->\s*(\S+)\s+(?:of\s+)?(.+)',
                problem, re.IGNORECASE,
            )
            if m:
                point_text = m.group(1)
                expr_text = m.group(2)

            # Pattern 2: "limit as x->a of f(x)"  (note: 'as' comes before 'of')
            if not expr_text:
                m = re.search(
                    r'\b(?:limit|lim)\w*\s+as\s+x\s*->\s*(\S+)\s+of\s+(.+)',
                    problem, re.IGNORECASE,
                )
                if m:
                    point_text = m.group(1)
                    expr_text = m.group(2)

            # Pattern 3: "limit/lim [of] f(x) as x->a"
            if not expr_text:
                m = re.search(
                    r'\b(?:limit|lim)\w*\s+(?:of\s+)?(.+?)\s+as\s+x\s*->\s*(.+)',
                    problem, re.IGNORECASE,
                )
                if m:
                    expr_text = m.group(1)
                    point_text = m.group(2)

            # Pattern 4: anything remaining with "as x ->" in it
            if not expr_text:
                rest = re.sub(r'\b(?:limit|lim)\w*\s+(?:of\s+)?', '', problem, flags=re.IGNORECASE)
                m = re.search(r'(.+?)\s+as\s+x\s*->\s*(.+)', rest, re.IGNORECASE)
                if m:
                    expr_text = m.group(1)
                    point_text = m.group(2)

            if not expr_text or not point_text:
                raise ValueError(
                    "Could not parse limit. Try: 'limit of sin(x)/x as x->0' "
                    "or 'lim x->0 sin(x)/x'"
                )

            expr_text = expr_text.strip()
            point_text = point_text.strip()
            steps.append(f"🔧 **Expression:** {expr_text}")
            steps.append(f"🔧 **Point:** x → {point_text}")

            expr = self._safe_parse(expr_text)
            pt_lower = point_text.lower()
            if pt_lower in ('inf', 'infinity', '+inf', '+infinity', 'oo'):
                point = oo
            elif pt_lower in ('-inf', '-infinity', '-oo'):
                point = -oo
            else:
                point = self._safe_parse(point_text)

            steps.append(f"🔍 **Computing lim(x→{point}) {expr}...**")
            result = limit(expr, x, point)
            result = simplify(result)
            steps.append(f"\n✅ **Answer:** lim(x→{point}) {expr} = {result}")

            return Solution(
                answer=f"lim(x→{point}) = {result}",
                steps=steps,
                explanation=(
                    f"The limit of {expr} as x approaches {point} is {result}."
                ),
                problem_type="limit", difficulty="medium", confidence=1.0,
            )

        except Exception as e:
            return Solution(
                answer=f"Could not compute limit: {str(e)}",
                steps=["❌ Error computing limit",
                       "💡 Formats: 'limit of sin(x)/x as x->0'  or  'lim x->0 sin(x)/x'"],
                explanation=str(e), problem_type="limit",
                difficulty="unknown", confidence=0.0,
            )

    # ---- System of equations ----------------------------------------- #

    def _solve_system(self, problem: str) -> Solution:
        """Solve a system of two or more equations."""
        try:
            steps = []
            steps.append(f"📝 **System:** {problem.strip()}")

            raw = re.sub(r'^\s*solve\s*', '', problem, flags=re.IGNORECASE).strip()
            parts = self._split_equations(raw)

            if len(parts) < 2:
                raise ValueError(
                    "Need at least 2 equations. Separate them with 'and', comma, or newline."
                )

            equations = []
            all_syms: set = set()

            for part in parts:
                part = part.strip()
                if '=' in part:
                    lhs_t, rhs_t = part.split('=', 1)
                    eq = self._safe_parse(lhs_t) - self._safe_parse(rhs_t)
                else:
                    eq = self._safe_parse(part)
                equations.append(eq)
                all_syms.update(eq.free_symbols)
                steps.append(f"   {eq} = 0")

            sym_list = sorted(list(all_syms), key=str)
            steps.append(f"🔍 **Solving for:** {', '.join(str(s) for s in sym_list)}")

            solution = solve(equations, sym_list, dict=True)

            if not solution:
                return Solution(
                    answer="No solution (inconsistent or dependent system)",
                    steps=steps,
                    explanation="The system of equations has no unique solution.",
                    problem_type="system", difficulty="medium", confidence=1.0,
                )

            sol = solution[0]
            answer_parts = [f"{var} = {val}" for var, val in sol.items()]
            answer = ", ".join(answer_parts)
            steps.append(f"\n✅ **Solution:** {answer}")

            explanation = (
                f"Solved {len(equations)} simultaneous equations: {answer}."
            )
            return Solution(
                answer=answer, steps=steps, explanation=explanation,
                problem_type="system", difficulty="medium", confidence=1.0,
            )

        except Exception as e:
            return Solution(
                answer=f"Could not solve system: {str(e)}",
                steps=[f"❌ Error: {str(e)}",
                       "💡 Format: 'solve 2x + y = 5 and x - y = 1'"],
                explanation=str(e), problem_type="system",
                difficulty="unknown", confidence=0.0,
            )

    # ---- Simplify / Expand / Factor ---------------------------------- #

    def _solve_simplify(self, problem: str) -> Solution:
        try:
            expr_text = re.sub(r'\bsimplify\b', '', problem, flags=re.IGNORECASE).strip()
            steps = [f"📝 **Expression:** {expr_text}"]
            expr = self._safe_parse(expr_text)
            result = simplify(expr)
            steps.append(f"\n✅ **Simplified:** {result}")
            return Solution(
                answer=str(result), steps=steps,
                explanation=f"Simplified form: {result}",
                problem_type="simplify", difficulty="easy", confidence=1.0,
            )
        except Exception as e:
            return Solution(
                answer=f"Could not simplify: {str(e)}", steps=["❌ Error"],
                explanation=str(e), problem_type="simplify",
                difficulty="unknown", confidence=0.0,
            )

    def _solve_expand(self, problem: str) -> Solution:
        try:
            expr_text = re.sub(r'\bexpand\b', '', problem, flags=re.IGNORECASE).strip()
            steps = [f"📝 **Expression:** {expr_text}"]
            expr = self._safe_parse(expr_text)
            result = expand(expr)
            steps.append(f"\n✅ **Expanded:** {result}")
            return Solution(
                answer=str(result), steps=steps,
                explanation=f"Expanded form: {result}",
                problem_type="expand", difficulty="easy", confidence=1.0,
            )
        except Exception as e:
            return Solution(
                answer=f"Could not expand: {str(e)}", steps=["❌ Error"],
                explanation=str(e), problem_type="expand",
                difficulty="unknown", confidence=0.0,
            )

    def _solve_factor(self, problem: str) -> Solution:
        try:
            expr_text = re.sub(r'\bfactor\b', '', problem, flags=re.IGNORECASE).strip()
            steps = [f"📝 **Expression:** {expr_text}"]
            expr = self._safe_parse(expr_text)
            result = factor(expr)
            steps.append(f"\n✅ **Factored:** {result}")
            return Solution(
                answer=str(result), steps=steps,
                explanation=f"Factored form: {result}",
                problem_type="factor", difficulty="medium", confidence=1.0,
            )
        except Exception as e:
            return Solution(
                answer=f"Could not factor: {str(e)}", steps=["❌ Error"],
                explanation=str(e), problem_type="factor",
                difficulty="unknown", confidence=0.0,
            )
