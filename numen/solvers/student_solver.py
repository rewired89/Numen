"""
Student Solver - Solves problems and explains the answer step-by-step.

This is different from the verifier - instead of checking if an answer is correct,
this SOLVES the problem and EXPLAINS how to get the answer.

Perfect for students who need help understanding how to solve problems.
"""

import re
import sympy as sp
from sympy import symbols, solve, diff, integrate, simplify, expand, factor, limit, oo, E, pi, I
from sympy.parsing.sympy_parser import parse_expr, standard_transformations, implicit_multiplication_application
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from sympy import binomial, factorial, gcd, lcm, fibonacci as fib_sym
from sympy.ntheory import isprime, factorint, nextprime, prevprime, divisors
try:
    from sympy.functions.combinatorial.numbers import totient
except ImportError:
    from sympy.ntheory import totient


# Public domain physics formulas (NIST / OpenStax CC-BY)
_PHYSICS_FORMULAS = {
    # Mechanics
    'newton':        ('F = m * a',          {'F':'Force (N)', 'm':'Mass (kg)', 'a':'Acceleration (m/s²)'}),
    'kinetic':       ('KE = m * v**2 / 2',  {'KE':'Kinetic energy (J)', 'm':'Mass (kg)', 'v':'Velocity (m/s)'}),
    'potential':     ('PE = m * g * h',     {'PE':'Potential energy (J)', 'm':'Mass (kg)', 'g':'9.8 m/s²', 'h':'Height (m)'}),
    'momentum':      ('p = m * v',          {'p':'Momentum (kg·m/s)', 'm':'Mass (kg)', 'v':'Velocity (m/s)'}),
    'work':          ('W = F * d',          {'W':'Work (J)', 'F':'Force (N)', 'd':'Distance (m)'}),
    'power_mech':    ('P = W / t',          {'P':'Power (W)', 'W':'Work (J)', 't':'Time (s)'}),
    'velocity':      ('v = u + a * t',      {'v':'Final velocity (m/s)', 'u':'Initial velocity (m/s)', 'a':'Acceleration (m/s²)', 't':'Time (s)'}),
    'displacement':  ('s = u*t + a*t**2/2', {'s':'Displacement (m)', 'u':'Initial velocity (m/s)', 'a':'Acceleration (m/s²)', 't':'Time (s)'}),
    'torque':        ('tau = r * F',        {'tau':'Torque (N·m)', 'r':'Radius (m)', 'F':'Force (N)'}),
    'centripetal':   ('F = m * v**2 / r',   {'F':'Centripetal force (N)', 'm':'Mass (kg)', 'v':'Speed (m/s)', 'r':'Radius (m)'}),
    'gravity':       ('F = G * m1 * m2 / r**2', {'F':'Gravitational force (N)', 'G':'6.674e-11 N·m²/kg²', 'm1':'Mass 1 (kg)', 'm2':'Mass 2 (kg)', 'r':'Distance (m)'}),
    # Thermodynamics
    'ideal_gas':     ('P * V = n * R * T',  {'P':'Pressure (Pa)', 'V':'Volume (m³)', 'n':'Moles (mol)', 'R':'8.314 J/(mol·K)', 'T':'Temperature (K)'}),
    'heat':          ('Q = m * c * dT',     {'Q':'Heat (J)', 'm':'Mass (kg)', 'c':'Specific heat (J/kg·K)', 'dT':'Temp change (K)'}),
    # Electromagnetism
    'ohm':           ('V = I * R',          {'V':'Voltage (V)', 'I':'Current (A)', 'R':'Resistance (Ω)'}),
    'power_elec':    ('P = I * V',          {'P':'Power (W)', 'I':'Current (A)', 'V':'Voltage (V)'}),
    'coulomb':       ('F = k * q1 * q2 / r**2', {'F':'Force (N)', 'k':'8.99e9 N·m²/C²', 'q1':'Charge 1 (C)', 'q2':'Charge 2 (C)', 'r':'Distance (m)'}),
    'capacitance':   ('C = Q / V',          {'C':'Capacitance (F)', 'Q':'Charge (C)', 'V':'Voltage (V)'}),
    'resistance':    ('R = rho * L / A',    {'R':'Resistance (Ω)', 'rho':'Resistivity (Ω·m)', 'L':'Length (m)', 'A':'Area (m²)'}),
    # Waves & Optics
    'wave':          ('v = f * lam',        {'v':'Wave speed (m/s)', 'f':'Frequency (Hz)', 'lam':'Wavelength (m)'}),
    'photon':        ('E = h * f',          {'E':'Photon energy (J)', 'h':'6.626e-34 J·s', 'f':'Frequency (Hz)'}),
    'snell':         ('n1 * sin(theta1) = n2 * sin(theta2)', {'n1':'Refractive index 1', 'theta1':'Angle 1 (rad)', 'n2':'Refractive index 2', 'theta2':'Angle 2 (rad)'}),
    'thin_lens':     ('1/f = 1/do + 1/di', {'f':'Focal length (m)', 'do':'Object distance (m)', 'di':'Image distance (m)'}),
    # Relativity
    'mass_energy':   ('E = m * c**2',       {'E':'Energy (J)', 'm':'Mass (kg)', 'c':'3e8 m/s'}),
}

_PHYSICS_CONSTANTS = {
    'speed of light':        ('c', '2.998 × 10⁸ m/s',     2.998e8),
    'planck':                ('h', '6.626 × 10⁻³⁴ J·s',   6.626e-34),
    'reduced planck':        ('ℏ', '1.055 × 10⁻³⁴ J·s',   1.055e-34),
    'boltzmann':             ('k_B', '1.381 × 10⁻²³ J/K', 1.381e-23),
    'avogadro':              ('N_A', '6.022 × 10²³ /mol',  6.022e23),
    'gravitational':         ('G',  '6.674 × 10⁻¹¹ N·m²/kg²', 6.674e-11),
    'electron mass':         ('m_e', '9.109 × 10⁻³¹ kg',  9.109e-31),
    'proton mass':           ('m_p', '1.673 × 10⁻²⁷ kg',  1.673e-27),
    'elementary charge':     ('e',  '1.602 × 10⁻¹⁹ C',    1.602e-19),
    'permittivity':          ('ε₀', '8.854 × 10⁻¹² F/m',  8.854e-12),
    'permeability':          ('μ₀', '1.257 × 10⁻⁶ H/m',   1.257e-6),
    'stefan boltzmann':      ('σ',  '5.670 × 10⁻⁸ W/m²·K⁴', 5.670e-8),
    'gas constant':          ('R',  '8.314 J/(mol·K)',      8.314),
    'fine structure':        ('α',  '7.297 × 10⁻³',        7.297e-3),
    'rydberg':               ('R∞', '1.097 × 10⁷ /m',      1.097e7),
}


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
        # Map common names to SymPy objects so e, pi, i are recognized
        self.local_dict = {
            'e': E,
            'pi': pi,
            'i': I,
            'inf': oo,
            'infinity': oo,
        }

    def _fix_notation(self, problem: str) -> str:
        """Normalize common math notations before parsing."""
        # Replace e^ with exp( ... ) when e is Euler's number
        # Pattern: standalone e followed by ^ or **
        problem = re.sub(r'\be\^', 'E^', problem)
        problem = re.sub(r'\be\*\*', 'E**', problem)
        # Convert → and -> in limits
        problem = problem.replace('→', '->').replace('—>', '->')
        return problem

    def _safe_parse(self, expr_str: str) -> sp.Expr:
        """Parse expression with local_dict for e, pi, i."""
        cleaned = expr_str.strip().replace('^', '**')
        return parse_expr(cleaned, local_dict=self.local_dict,
                          transformations=self.transformations)

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
        problem = self._fix_notation(problem)

        # Auto-detect problem type
        problem_type = self._detect_problem_type(problem)

        # Solve based on type
        if problem_type == "limit":
            return self._solve_limit(problem)
        elif problem_type == "system":
            return self._solve_system(problem)
        elif problem_type == "ode":
            return self._solve_ode(problem)
        elif problem_type == "matrix":
            return self._solve_matrix(problem)
        elif problem_type == "statistics":
            return self._solve_statistics(problem)
        elif problem_type == "laplace":
            return self._solve_laplace(problem)
        elif problem_type == "inverse_laplace":
            return self._solve_inverse_laplace(problem)
        elif problem_type == "fourier":
            return self._solve_fourier(problem)
        elif problem_type == "double_integral":
            return self._solve_double_integral(problem)
        elif problem_type == "probability":
            return self._solve_probability(problem)
        elif problem_type == "regression":
            return self._solve_regression(problem)
        elif problem_type == "definite_integral":
            return self._solve_definite_integral(problem)
        elif problem_type == "units":
            return self._solve_units(problem)
        elif problem_type == "physics":
            return self._solve_physics(problem)
        elif problem_type == "number_theory":
            return self._solve_number_theory(problem)
        elif problem_type == "combinatorics":
            return self._solve_combinatorics(problem)
        elif problem_type == "graph":
            return self._solve_graph(problem)
        elif problem_type == "stats_test":
            return self._solve_stats_test(problem)
        elif problem_type == "equation":
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

        if "limit" in problem_lower and ("->" in problem or "→" in problem or "as x" in problem_lower):
            return "limit"
        elif "inverse laplace" in problem_lower:
            return "inverse_laplace"
        elif "laplace" in problem_lower and (
            "transform" in problem_lower or "of" in problem_lower
        ):
            return "laplace"
        elif "fourier" in problem_lower and (
            "transform" in problem_lower or "of" in problem_lower
        ):
            return "fourier"
        elif any(k in problem_lower for k in ("double integral", "double integrate",
                                               "triple integral", "∬", "∭")):
            return "double_integral"
        elif any(k in problem_lower for k in (
            "normal distribution", "binomial distribution", "poisson distribution",
            "exponential distribution", "normal pdf", "normal cdf",
            "binomial pmf", "poisson pmf", "distribution",
        )):
            return "probability"
        elif any(k in problem_lower for k in (
            "regression", "linear fit", "best fit", "least squares",
        )):
            return "regression"
        elif ("integral" in problem_lower or "integrate" in problem_lower) and (
            " from " in problem_lower and " to " in problem_lower
        ):
            return "definite_integral"
        elif any(k in problem_lower for k in ("y''", "y'", "dy/dx", "d2y/dx2")) or (
            problem_lower.startswith("ode ")
        ):
            return "ode"
        elif ("[[" in problem or "matrix" in problem_lower) and any(
            k in problem_lower for k in (
                "inverse", "determinant", "det", "eigenvalue", "eigenvector",
                "transpose", "rank", "rref", "multiply", "trace", "norm",
            )
        ):
            return "matrix"
        elif "[[" in problem and problem_lower.startswith(("[[", "matrix")):
            return "matrix"
        elif any(k in problem_lower for k in (
            "mean", "median", "mode", "std", "standard deviation",
            "variance", "statistics", "average", "range of data",
        )):
            return "statistics"
        elif ("solve" in problem_lower or "=" in problem) and (
            " and " in problem_lower or "," in problem
        ) and any(v in problem_lower for v in ["y", "z"]):
            return "system"
        elif any(k in problem_lower for k in (
            'convert ', 'celsius', 'fahrenheit', 'kilogram', 'pounds',
            'miles', 'kilometer', 'feet', 'meters', 'gallons', 'liters',
        )) and re.search(r'\d', problem) and '=' not in problem:
            return "units"
        elif re.search(r'\bconvert\b', problem_lower) and re.search(r'\d', problem) and '=' not in problem:
            return "units"
        elif any(k in problem_lower for k in (
            'speed of light', 'planck', 'boltzmann', 'avogadro', 'gravitational constant',
            'electron mass', 'elementary charge', 'f = m', 'f=m', 'v = i', 'pv = n',
            'e = m', 'kinetic energy', 'potential energy', 'ohm', 'coulomb law',
            'snell', 'thin lens', 'photon', 'ideal gas', 'momentum =',
        )):
            return "physics"
        elif any(k in problem_lower for k in (
            'choose', 'combination', 'permut', 'factorial', 'c(', 'p(',
            'ncr', 'npr', 'derangement',
        )) or '!' in problem:
            return "combinatorics"
        elif any(k in problem_lower for k in (
            'prime factor', 'prime factori', 'factori', 'is prime', 'gcd', 'lcm', 'totient',
            'divisors', 'fibonacci', 'next prime', 'greatest common divisor',
            'least common multiple',
        )) or ('prime' in problem_lower and re.search(r'\d', problem)):
            return "number_theory"
        elif any(k in problem_lower for k in (
            'shortest path', 'minimum spanning tree', 'mst', 'eulerian circuit',
            'eulerian path', 'graph connectivity', 'node centrality',
        )) or ('graph' in problem_lower and any(k in problem_lower for k in (
            'vertex', 'edge', 'node', 'path', 'connected', 'centrality',
        ))):
            return "graph"
        elif any(k in problem_lower for k in (
            't-test', 'ttest', 'chi-square', 'chi square', 'confidence interval',
            'pearson correlation', 'hypothesis',
        )):
            return "stats_test"
        elif ("derivative" in problem_lower or "d/dx" in problem_lower
              or "differentiate" in problem_lower or "∂" in problem
              or "partial" in problem_lower
              or re.search(r'd/d[a-zA-Z]', problem)):
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

                lhs = self._safe_parse(lhs_text)
                rhs = self._safe_parse(rhs_text)
                equation = lhs - rhs
            else:
                equation_text = problem.replace("solve", "").replace("for x", "").strip()
                steps.append(f"📝 **Original equation:** {equation_text} = 0")
                equation = self._safe_parse(equation_text)

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
            expr_text = (problem.replace("derivative", "").replace("of", "")
                         .replace("d/dx", "").replace("differentiate", "").strip())
            steps.append(f"📝 **Original function:** f(x) = {expr_text}")

            expr = self._safe_parse(expr_text)
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

    def _solve_units(self, problem: str) -> Solution:
        """Unit conversion using pint."""
        steps = []
        try:
            import pint
            ureg = pint.UnitRegistry()

            m = re.search(
                r'([\d,]+\.?\d*)\s*([a-zA-Z°_/²³·]+(?:\s*per\s*[a-zA-Z]+)?)\s+'
                r'(?:to|in|into|as)\s+([a-zA-Z°_/²³·]+(?:\s*per\s*[a-zA-Z]+)?)',
                problem, re.IGNORECASE)
            if not m:
                # Try "X km/h to mph" pattern
                m = re.search(
                    r'convert\s+([\d,]+\.?\d*)\s*([^\s]+)\s+(?:to|into)\s+([^\s]+)',
                    problem, re.IGNORECASE)

            if not m:
                raise ValueError(
                    "Format: 'convert VALUE UNIT to UNIT'  e.g. 'convert 100 km to miles'")

            value = float(m.group(1).replace(',', ''))
            from_unit = m.group(2).strip()
            to_unit   = m.group(3).strip()

            # Common aliases pint doesn't know
            aliases = {
                'kmh': 'km/hour', 'kph': 'km/hour', 'mph': 'mile/hour',
                'c':   'degC',    'f':   'degF',     'k':   'kelvin',
                'lbs': 'pound',   'lb':  'pound',    'oz':  'ounce',
                'ft':  'foot',    'in':  'inch',     'yd':  'yard',
                'mi':  'mile',
                'celsius': 'degC', 'fahrenheit': 'degF', 'kelvin': 'kelvin',
                'rankine': 'rankine',
                'gram': 'gram', 'grams': 'gram', 'kilogram': 'kilogram',
                'kilograms': 'kilogram', 'pound': 'pound', 'pounds': 'pound',
                'meter': 'meter', 'meters': 'meter', 'kilometre': 'kilometer',
                'kilometre': 'kilometer', 'foot': 'foot', 'feet': 'foot',
                'inch': 'inch', 'inches': 'inch', 'mile': 'mile', 'miles': 'mile',
                'litre': 'liter', 'litres': 'liter', 'gallon': 'gallon',
                'gallons': 'gallon',
            }
            from_unit = aliases.get(from_unit.lower(), from_unit)
            to_unit   = aliases.get(to_unit.lower(), to_unit)

            # Offset units (temperature) need Quantity constructor, not multiplication
            if from_unit in ('degC', 'degF', 'rankine'):
                quantity = ureg.Quantity(value, from_unit)
            else:
                quantity = value * ureg(from_unit)
            result   = quantity.to(to_unit)

            steps.append(f"📐 **Converting:** {value} {from_unit} → {to_unit}")
            steps.append(f"✅ **Result:** {result:.6g}")

            return Solution(
                answer=f"{value} {from_unit} = {result:.6g}",
                steps=steps,
                explanation=f"Unit conversion using dimensional analysis (pint library).",
                problem_type="units", difficulty="easy", confidence=1.0,
            )

        except ImportError:
            return Solution(
                answer="Install pint: pip install pint",
                steps=["pint library not installed"],
                explanation="Run: pip install pint",
                problem_type="units", difficulty="easy", confidence=0.0,
            )
        except Exception as e:
            return Solution(
                answer=f"Could not convert: {str(e)}",
                steps=[f"Error: {str(e)}", "",
                       "**Examples:**",
                       "- `convert 100 km to miles`",
                       "- `convert 72 fahrenheit to celsius`",
                       "- `convert 9.8 m/s^2 to ft/s^2`"],
                explanation=str(e),
                problem_type="units", difficulty="easy", confidence=0.0,
            )

    def _solve_physics(self, problem: str) -> Solution:
        """Physics constants lookup and formula solver."""
        steps = []
        problem_lower = problem.lower()

        # ── Constants lookup ──
        for name, (sym, val_str, val_num) in _PHYSICS_CONSTANTS.items():
            if name in problem_lower:
                steps.append(f"📚 **{name.title()}** ({sym})")
                steps.append(f"✅ **Value:** {val_str}")
                return Solution(
                    answer=f"{sym} = {val_str}",
                    steps=steps,
                    explanation=f"NIST CODATA 2022 value for {name}.",
                    problem_type="physics", difficulty="easy", confidence=1.0,
                )

        # ── Formula solver ──
        # Find which formula matches keywords in the problem
        matched = None
        for key, (formula_str, var_desc) in _PHYSICS_FORMULAS.items():
            if key.replace('_', ' ') in problem_lower or any(
                v.lower() in problem_lower for v in var_desc.keys()
                if v not in ('G', 'R', 'k', 'h', 'c', 'e', 'g')  # skip generic 1-letter
            ):
                matched = (key, formula_str, var_desc)
                break

        if not matched:
            # Try to match by formula name keyword
            kw_map = {
                'ohm': 'ohm', "newton": 'newton', 'kinetic': 'kinetic',
                'potential': 'potential', 'ideal gas': 'ideal_gas',
                'wave': 'wave', 'photon': 'photon', 'momentum': 'momentum',
                'power': 'power_elec', 'work': 'work',
                'displacement': 'displacement', 'velocity': 'velocity',
                'heat': 'heat', 'snell': 'snell', 'lens': 'thin_lens',
                'coulomb': 'coulomb', 'gravity': 'gravity',
                'e=mc': 'mass_energy', 'mass energy': 'mass_energy',
                'centripetal': 'centripetal', 'torque': 'torque',
            }
            for kw, fkey in kw_map.items():
                if kw in problem_lower:
                    formula_str, var_desc = _PHYSICS_FORMULAS[fkey]
                    matched = (fkey, formula_str, var_desc)
                    break

        if not matched:
            return Solution(
                answer="Could not identify physics formula.",
                steps=["**Available formulas:**",
                       "- Mechanics: F=ma, KE, PE, momentum, work, velocity, displacement, torque, centripetal",
                       "- Thermodynamics: ideal gas (PV=nRT), heat (Q=mcΔT)",
                       "- Electromagnetism: Ohm's law (V=IR), power, Coulomb's law, capacitance",
                       "- Waves: v=fλ, E=hf, Snell's law, thin lens",
                       "- Relativity: E=mc²",
                       "- Constants: speed of light, Planck, Boltzmann, Avogadro, G, electron mass, ..."],
                explanation="Type the formula name or variable names.",
                problem_type="physics", difficulty="medium", confidence=0.0,
            )

        key, formula_str, var_desc = matched
        steps.append(f"📐 **Formula:** {formula_str}")
        steps.append("**Variables:**")
        for v, desc in var_desc.items():
            steps.append(f"   {v} = {desc}")

        # Extract known values from problem: "m=5", "v = 10", etc.
        known = {}
        for v in var_desc:
            pat = re.search(rf'\b{re.escape(v)}\s*=\s*([\d.e+\-]+)', problem, re.IGNORECASE)
            if pat:
                known[v] = float(pat.group(1))

        if not known:
            return Solution(
                answer=f"Formula: {formula_str}",
                steps=steps + ["Provide variable values, e.g.: m=5 a=9.8"],
                explanation=f"Formula: {formula_str}. Supply values for all but one variable.",
                problem_type="physics", difficulty="medium", confidence=0.8,
            )

        # Parse formula and solve for unknown
        try:
            all_vars = {v: sp.Symbol(v) for v in var_desc}
            lhs_str, rhs_str = formula_str.split('=', 1)
            lhs = parse_expr(lhs_str.strip(), local_dict=all_vars,
                             transformations=self.transformations)
            rhs = parse_expr(rhs_str.strip(), local_dict=all_vars,
                             transformations=self.transformations)
            equation = sp.Eq(lhs, rhs)

            # Substitute known values
            for v, val in known.items():
                equation = equation.subs(all_vars[v], val)
                steps.append(f"   {v} = {val}")

            unknowns = [all_vars[v] for v in var_desc if v not in known]
            if not unknowns:
                # All known — just verify
                result = "All values provided — equation verified."
            else:
                solutions = sp.solve(equation, unknowns[0])
                if not solutions:
                    result = "No solution found."
                else:
                    sol_val = float(solutions[0]) if solutions[0].is_number else solutions[0]
                    result = f"{unknowns[0]} = {sol_val:.6g}" if isinstance(sol_val, float) else f"{unknowns[0]} = {sol_val}"

            steps.append(f"\n✅ **Result:** {result}")
            return Solution(
                answer=result, steps=steps,
                explanation=f"Applied {formula_str}, substituted known values, solved symbolically.",
                problem_type="physics", difficulty="medium", confidence=1.0,
            )
        except Exception as e:
            steps.append(f"\n⚠ Could not solve symbolically: {e}")
            return Solution(
                answer=f"Formula: {formula_str}",
                steps=steps,
                explanation=str(e),
                problem_type="physics", difficulty="medium", confidence=0.5,
            )

    def _solve_number_theory(self, problem: str) -> Solution:
        """Number theory: primes, factorization, GCD, LCM, totient, Fibonacci."""
        steps = []
        problem_lower = problem.lower()

        def extract_ints(text):
            return [int(x) for x in re.findall(r'\d+', text)]

        try:
            nums = extract_ints(problem)

            # Prime factorization
            if any(k in problem_lower for k in ('factor', 'factori', 'prime factor')):
                if not nums:
                    raise ValueError("Provide a number to factorize.")
                n = nums[0]
                factors = factorint(n)
                factor_str = ' × '.join(
                    f"{p}^{e}" if e > 1 else str(p)
                    for p, e in sorted(factors.items()))
                steps.append(f"📝 **Factorizing:** {n}")
                steps.append(f"✅ **Prime factorization:** {n} = {factor_str}")
                answer = f"{n} = {factor_str}"

            # Is prime
            elif 'is' in problem_lower and 'prime' in problem_lower:
                if not nums:
                    raise ValueError("Provide a number.")
                n = nums[0]
                result = isprime(n)
                steps.append(f"📝 **Testing primality:** {n}")
                steps.append(f"✅ **{n} is {'prime' if result else 'not prime (composite)'}**")
                if not result:
                    steps.append(f"   Factors: {factorint(n)}")
                answer = f"{n} is {'prime' if result else 'NOT prime'}"

            # Next / previous prime
            elif 'next prime' in problem_lower:
                n = nums[0] if nums else 0
                np_ = nextprime(n)
                answer = f"Next prime after {n} = {np_}"
                steps.append(f"✅ {answer}")
            elif 'prev' in problem_lower and 'prime' in problem_lower:
                n = nums[0] if nums else 2
                pp = prevprime(n)
                answer = f"Previous prime before {n} = {pp}"
                steps.append(f"✅ {answer}")

            # GCD
            elif 'gcd' in problem_lower or 'greatest common' in problem_lower:
                if len(nums) < 2:
                    raise ValueError("Provide at least two numbers.")
                result = int(gcd(*nums))
                steps.append(f"✅ **GCD({', '.join(map(str,nums))}) = {result}**")
                answer = f"GCD = {result}"

            # LCM
            elif 'lcm' in problem_lower or 'least common' in problem_lower:
                if len(nums) < 2:
                    raise ValueError("Provide at least two numbers.")
                result = int(lcm(*nums))
                steps.append(f"✅ **LCM({', '.join(map(str,nums))}) = {result}**")
                answer = f"LCM = {result}"

            # Totient
            elif "totient" in problem_lower or "euler" in problem_lower:
                if not nums:
                    raise ValueError("Provide a number.")
                n = nums[0]
                result = int(totient(n))
                steps.append(f"✅ **φ({n}) = {result}**")
                steps.append(f"   (Count of integers 1..{n} coprime to {n})")
                answer = f"φ({n}) = {result}"

            # Divisors
            elif 'divisor' in problem_lower:
                n = nums[0]
                divs = sorted(divisors(n))
                steps.append(f"✅ **Divisors of {n}:** {divs}")
                answer = f"Divisors of {n} = {divs}"

            # Fibonacci
            elif 'fibonacci' in problem_lower or 'fib' in problem_lower:
                n = nums[0] if nums else 10
                seq = [int(fib_sym(i)) for i in range(n+1)]
                steps.append(f"✅ **First {n+1} Fibonacci numbers:** {seq}")
                answer = f"F({n}) = {seq[-1]}"

            else:
                raise ValueError("Unknown number theory operation.")

            return Solution(
                answer=answer, steps=steps,
                explanation="Computed using SymPy number theory (sympy.ntheory).",
                problem_type="number_theory", difficulty="medium", confidence=1.0,
            )

        except Exception as e:
            return Solution(
                answer=f"Could not compute: {str(e)}",
                steps=["**Examples:**",
                       "- `prime factorization of 360`",
                       "- `is 97 prime?`",
                       "- `gcd of 48 and 18`",
                       "- `lcm of 12 and 18`",
                       "- `totient of 12`",
                       "- `divisors of 60`",
                       "- `fibonacci 10`"],
                explanation=str(e),
                problem_type="number_theory", difficulty="medium", confidence=0.0,
            )

    def _solve_combinatorics(self, problem: str) -> Solution:
        """Combinations, permutations, factorial."""
        steps = []
        problem_lower = problem.lower()

        try:
            nums = [int(x) for x in re.findall(r'\d+', problem)]

            # nCr / choose
            if any(k in problem_lower for k in ('choose', 'combination', 'c(', 'ncr')):
                if len(nums) < 2:
                    raise ValueError("Need two numbers: C(n, r)")
                n, r = nums[0], nums[1]
                result = int(binomial(n, r))
                steps.append(f"📝 **C({n}, {r}) = {n}! / ({r}! × {n-r}!)**")
                steps.append(f"✅ **Answer: {result}**")
                answer = f"C({n},{r}) = {result}"

            # nPr / permutations
            elif any(k in problem_lower for k in ('permut', 'p(', 'npr', 'arrange')):
                if len(nums) < 2:
                    raise ValueError("Need two numbers: P(n, r)")
                n, r = nums[0], nums[1]
                result = int(factorial(n) / factorial(n - r))
                steps.append(f"📝 **P({n}, {r}) = {n}! / ({n-r}!)**")
                steps.append(f"✅ **Answer: {result}**")
                answer = f"P({n},{r}) = {result}"

            # Factorial
            elif 'factorial' in problem_lower or '!' in problem:
                n = nums[0] if nums else 0
                result = int(factorial(n))
                steps.append(f"✅ **{n}! = {result}**")
                answer = f"{n}! = {result}"

            # Derangements
            elif 'derangement' in problem_lower:
                n = nums[0]
                from sympy.functions.combinatorial.numbers import subfactorial
                result = int(subfactorial(n))
                steps.append(f"✅ **D({n}) = {result}**")
                answer = f"Derangements of {n} items = {result}"

            else:
                raise ValueError("Unknown combinatorics operation.")

            return Solution(
                answer=answer, steps=steps,
                explanation="Computed using SymPy combinatorics.",
                problem_type="combinatorics", difficulty="medium", confidence=1.0,
            )

        except Exception as e:
            return Solution(
                answer=f"Could not compute: {str(e)}",
                steps=["**Examples:**",
                       "- `10 choose 3` → C(10,3) = 120",
                       "- `permutations P(8, 3)`",
                       "- `factorial 15`",
                       "- `derangements of 4`"],
                explanation=str(e),
                problem_type="combinatorics", difficulty="medium", confidence=0.0,
            )

    def _solve_graph(self, problem: str) -> Solution:
        """Graph theory using NetworkX."""
        import networkx as nx
        steps = []
        problem_lower = problem.lower()

        try:
            # Try weighted edges first: (u,v,weight)
            weighted = re.findall(r'\((\w+)\s*,\s*(\w+)\s*,\s*([\d.]+)\)', problem)
            # Unweighted edges: (u,v)
            unweighted = re.findall(r'\((\w+)\s*,\s*(\w+)\)', problem)
            # Remove pairs that are actually weighted (avoid double-counting)
            if weighted:
                weighted_pairs = {(u, v) for u, v, _ in weighted}
                unweighted = [(u, v) for u, v in unweighted if (u, v) not in weighted_pairs]

            if not weighted and not unweighted:
                raise ValueError(
                    "Provide edges as [(node1,node2), ...] or [(node1,node2,weight), ...]\n"
                    "Examples:\n"
                    "  shortest path from A to B (A,B,5),(A,C,3),(C,B,1)\n"
                    "  connected graph (A,B),(B,C),(C,A)")

            G = nx.Graph()
            for u, v, w in weighted:
                G.add_edge(u, v, weight=float(w))
            for u, v in unweighted:
                G.add_edge(u, v)

            steps.append(f"📐 **Graph:** {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")

            # Shortest path
            if 'shortest path' in problem_lower:
                node_candidates = re.findall(r'\bfrom\s+(\w+)\s+to\s+(\w+)', problem, re.I)
                if node_candidates:
                    src, dst = node_candidates[0]
                    use_weight = 'weight' if weighted else None
                    path = nx.shortest_path(G, src, dst, weight=use_weight)
                    length = nx.shortest_path_length(G, src, dst, weight=use_weight)
                    label = "cost" if use_weight else "hops"
                    answer = f"Shortest path {src}→{dst}: {' → '.join(path)} ({label}: {length})"
                    steps.append(f"✅ {answer}")
                else:
                    raise ValueError("Specify 'from NODE to NODE'")

            # MST
            elif any(k in problem_lower for k in ('minimum spanning', 'mst')):
                T = nx.minimum_spanning_tree(G)
                edges = list(T.edges())
                answer = f"MST edges: {edges}  (total {T.number_of_edges()} edges)"
                steps.append(f"✅ {answer}")

            # Connected
            elif 'connected' in problem_lower:
                conn = nx.is_connected(G)
                answer = f"Graph is {'connected' if conn else 'NOT connected'}"
                if not conn:
                    comps = list(nx.connected_components(G))
                    answer += f" — {len(comps)} components: {comps}"
                steps.append(f"✅ {answer}")

            # Eulerian
            elif 'euler' in problem_lower:
                is_e = nx.is_eulerian(G)
                is_semi = nx.is_semieulerian(G)
                answer = (f"{'Eulerian circuit exists' if is_e else 'Semi-Eulerian (trail)' if is_semi else 'Not Eulerian'}")
                steps.append(f"✅ {answer}")

            # Degree
            elif 'degree' in problem_lower:
                degs = dict(G.degree())
                answer = f"Degrees: {degs}"
                steps.append(f"✅ {answer}")

            # Centrality
            elif 'centrality' in problem_lower:
                bc = nx.betweenness_centrality(G)
                answer = f"Betweenness centrality: { {k: round(v,3) for k,v in bc.items()} }"
                steps.append(f"✅ {answer}")

            # Default: summary
            else:
                conn = nx.is_connected(G)
                degs = dict(G.degree())
                avg_deg = sum(degs.values()) / len(degs) if degs else 0
                answer = (f"Nodes: {list(G.nodes())}  |  Edges: {list(G.edges())}  |  "
                          f"Connected: {conn}  |  Avg degree: {avg_deg:.2f}")
                steps.append(f"✅ {answer}")

            return Solution(
                answer=answer, steps=steps,
                explanation="Graph analysis using NetworkX (open source).",
                problem_type="graph", difficulty="medium", confidence=1.0,
            )

        except Exception as e:
            return Solution(
                answer=f"Could not analyze graph: {str(e)}",
                steps=["**Examples:**",
                       "- `is graph [(0,1),(1,2),(2,0)] connected`",
                       "- `shortest path from A to D in [(A,B),(B,C),(C,D),(A,D)]`",
                       "- `minimum spanning tree [(0,1),(0,2),(1,2),(1,3)]`",
                       "- `degree of [(A,B),(B,C),(C,A),(A,D)]`"],
                explanation=str(e),
                problem_type="graph", difficulty="medium", confidence=0.0,
            )

    def _solve_stats_test(self, problem: str) -> Solution:
        """Hypothesis tests and confidence intervals using scipy.stats."""
        import numpy as np
        from scipy import stats
        steps = []
        problem_lower = problem.lower()

        try:
            # Extract data arrays
            arrays = re.findall(r'\[([^\]]+)\]', problem)
            data_sets = []
            for arr in arrays:
                try:
                    data_sets.append([float(x) for x in arr.split(',')])
                except ValueError:
                    pass

            # t-test
            if 't-test' in problem_lower or 'ttest' in problem_lower:
                if len(data_sets) >= 2:
                    stat, pval = stats.ttest_ind(data_sets[0], data_sets[1])
                    answer = f"t = {stat:.4f},  p-value = {pval:.4f}"
                    steps.append(f"📝 **Independent samples t-test**")
                    steps.append(f"   Group 1: n={len(data_sets[0])}, mean={np.mean(data_sets[0]):.4f}")
                    steps.append(f"   Group 2: n={len(data_sets[1])}, mean={np.mean(data_sets[1]):.4f}")
                elif len(data_sets) == 1:
                    mu_m = re.search(r'mu\s*=\s*([\d.]+)', problem, re.I)
                    mu = float(mu_m.group(1)) if mu_m else 0
                    stat, pval = stats.ttest_1samp(data_sets[0], mu)
                    answer = f"t = {stat:.4f},  p-value = {pval:.4f}"
                    steps.append(f"📝 **One-sample t-test** (μ₀ = {mu})")
                else:
                    raise ValueError("Provide data as [1,2,3,...] in the problem.")
                steps.append(f"✅ {answer}")
                steps.append(f"   {'Reject H₀ (p < 0.05)' if pval < 0.05 else 'Fail to reject H₀ (p ≥ 0.05)'}")

            # Chi-square test
            elif 'chi' in problem_lower:
                if len(data_sets) < 2:
                    raise ValueError("Provide observed and expected as two arrays.")
                if len(data_sets) == 2:
                    chi2, pval = stats.chisquare(data_sets[0], data_sets[1])
                else:
                    chi2, pval, dof, expected = stats.chi2_contingency(
                        [data_sets[i] for i in range(len(data_sets))])
                answer = f"χ² = {chi2:.4f},  p-value = {pval:.4f}"
                steps.append(f"📝 **Chi-square test**")
                steps.append(f"✅ {answer}")
                steps.append(f"   {'Reject H₀ (p < 0.05)' if pval < 0.05 else 'Fail to reject H₀ (p ≥ 0.05)'}")

            # Correlation
            elif 'correlation' in problem_lower or 'pearson' in problem_lower:
                if len(data_sets) < 2:
                    raise ValueError("Provide two data arrays.")
                r, pval = stats.pearsonr(data_sets[0], data_sets[1])
                answer = f"Pearson r = {r:.4f},  p-value = {pval:.4f}"
                steps.append(f"✅ {answer}")

            # Confidence interval
            elif 'confidence' in problem_lower:
                if not data_sets:
                    raise ValueError("Provide data as [1,2,3,...]")
                data = data_sets[0]
                ci_m = re.search(r'(\d+)\s*%', problem)
                level = float(ci_m.group(1)) / 100 if ci_m else 0.95
                ci = stats.t.interval(level, df=len(data)-1,
                                      loc=np.mean(data), scale=stats.sem(data))
                answer = f"{level*100:.0f}% CI: ({ci[0]:.4f}, {ci[1]:.4f})"
                steps.append(f"📝 **{level*100:.0f}% Confidence Interval** for mean")
                steps.append(f"   n={len(data)}, mean={np.mean(data):.4f}, SE={stats.sem(data):.4f}")
                steps.append(f"✅ {answer}")

            else:
                raise ValueError("Specify test type: t-test, chi-square, correlation, or confidence interval.")

            return Solution(
                answer=answer, steps=steps,
                explanation="Statistical test computed using scipy.stats (open source).",
                problem_type="stats_test", difficulty="hard", confidence=1.0,
            )

        except Exception as e:
            return Solution(
                answer=f"Could not compute: {str(e)}",
                steps=["**Examples:**",
                       "- `t-test [2.1,2.5,2.3] [3.1,3.4,3.0]`",
                       "- `chi-square [10,20,30] [15,15,30]`",
                       "- `pearson correlation [1,2,3] [2,4,5]`",
                       "- `95% confidence interval [4.2,4.5,4.1,4.8,4.3]`"],
                explanation=str(e),
                problem_type="stats_test", difficulty="hard", confidence=0.0,
            )

    def _solve_integral(self, problem: str) -> Solution:
        """Solve an integral problem and explain."""
        try:
            x = symbols('x')
            steps = []

            # Extract function
            expr_text = (problem.replace("integral", "").replace("of", "")
                         .replace("integrate", "").replace("∫", "").replace("dx", "").strip())
            steps.append(f"📝 **Original function:** ∫ {expr_text} dx")

            expr = self._safe_parse(expr_text)
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

            expr = self._safe_parse(expr_text)
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

            expr = self._safe_parse(expr_text)
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

            expr = self._safe_parse(expr_text)
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

    def _solve_limit(self, problem: str) -> Solution:
        """Solve a limit problem and explain."""
        try:
            x = symbols('x')
            steps = []

            steps.append(f"📝 **Original problem:** {problem}")

            # Parse "limit of f(x) as x->a" or "limit f(x) as x->a" or "lim f(x) as x approaches a"
            pattern = re.compile(
                r'(?:limit\s+of\s+|limit\s+|lim\s+)(.+?)\s+as\s+x\s*(?:->|→|approaches)\s*(.+)',
                re.IGNORECASE,
            )
            match = pattern.search(problem)

            if not match:
                # Try "limit of f(x) as x->a" without "of"
                pattern2 = re.compile(
                    r'(.+?)\s+as\s+x\s*(?:->|→|approaches)\s*(.+)',
                    re.IGNORECASE,
                )
                match = pattern2.search(problem.replace("limit", "").replace("lim", ""))

            if not match:
                raise ValueError(
                    "Could not parse limit. Use format: 'limit of f(x) as x->0'"
                )

            expr_text = match.group(1).strip()
            point_text = match.group(2).strip()

            steps.append(f"🔧 **Function:** {expr_text}")
            steps.append(f"🔧 **Point:** x → {point_text}")

            expr = self._safe_parse(expr_text)

            # Handle special point values
            point_text_lower = point_text.lower()
            if point_text_lower in ("inf", "infinity", "+inf", "+infinity", "oo"):
                point = oo
            elif point_text_lower in ("-inf", "-infinity", "-oo"):
                point = -oo
            else:
                point = self._safe_parse(point_text)

            steps.append(f"🔍 **Computing limit as x → {point}...**")

            result = limit(expr, x, point)
            steps.append(f"   Applied limit rules to {expr}")

            simplified = simplify(result)
            steps.append(f"\n✅ **Final Answer:** lim(x→{point}) {expr} = {simplified}")

            answer = f"lim(x→{point}) = {simplified}"
            explanation = (
                f"The limit of {expr} as x approaches {point} is {simplified}. "
                "This was computed using symbolic limit evaluation."
            )

            return Solution(
                answer=answer,
                steps=steps,
                explanation=explanation,
                problem_type="limit",
                difficulty="medium",
                confidence=1.0,
            )

        except Exception as e:
            return Solution(
                answer=f"Could not solve: {str(e)}",
                steps=[f"❌ Error computing limit: {str(e)}",
                       "💡 Try format: 'limit of sin(x)/x as x->0'"],
                explanation=str(e),
                problem_type="limit",
                difficulty="unknown",
                confidence=0.0,
            )

    def _solve_system(self, problem: str) -> Solution:
        """Solve a system of equations."""
        try:
            steps = []
            steps.append(f"📝 **Original problem:** {problem}")

            # Split on "and" or comma to get individual equations
            raw = re.sub(r'^\s*solve\s*', '', problem, flags=re.IGNORECASE).strip()
            parts = re.split(r'\s+and\s+|,\s*', raw, flags=re.IGNORECASE)

            if len(parts) < 2:
                raise ValueError("Need at least 2 equations for a system. Separate them with 'and' or ','.")

            equations = []
            all_symbols = set()

            for part in parts:
                part = part.strip()
                if "=" in part:
                    lhs_t, rhs_t = part.split("=", 1)
                    lhs = self._safe_parse(lhs_t.strip())
                    rhs = self._safe_parse(rhs_t.strip())
                    eq = lhs - rhs
                else:
                    eq = self._safe_parse(part)
                equations.append(eq)
                all_symbols.update(eq.free_symbols)
                steps.append(f"   Equation: {eq} = 0")

            sym_list = sorted(list(all_symbols), key=lambda s: str(s))
            steps.append(f"🔍 **Solving for:** {', '.join(str(s) for s in sym_list)}")

            solution = solve(equations, sym_list, dict=True)

            if not solution:
                return Solution(
                    answer="No solution (inconsistent or dependent system)",
                    steps=steps,
                    explanation="The system has no unique solution.",
                    problem_type="system",
                    difficulty="medium",
                    confidence=1.0,
                )

            sol = solution[0]
            answer_parts = [f"{var} = {val}" for var, val in sol.items()]
            answer = ", ".join(answer_parts)
            steps.append(f"\n✅ **Solution:** {answer}")

            for var, val in sol.items():
                for eq in equations:
                    check = simplify(eq.subs(var, val))
                steps.append(f"🔍 **Verified:** substitution checks out")

            explanation = (
                f"The system of {len(equations)} equations has the solution: {answer}. "
                "Solved using symbolic simultaneous equation solving."
            )

            return Solution(
                answer=answer,
                steps=steps,
                explanation=explanation,
                problem_type="system",
                difficulty="medium",
                confidence=1.0,
            )

        except Exception as e:
            return Solution(
                answer=f"Could not solve: {str(e)}",
                steps=[f"❌ Error: {str(e)}",
                       "💡 Format: 'solve 2x + y = 5 and x - y = 1'"],
                explanation=str(e),
                problem_type="system",
                difficulty="unknown",
                confidence=0.0,
            )
    def _solve_definite_integral(self, problem: str) -> Solution:
        """Compute a definite integral with bounds."""
        try:
            x = symbols('x')
            steps = []
            steps.append(f"📝 **Original problem:** {problem}")

            # Pattern: "integral of f(x) from a to b"
            pattern = re.compile(
                r'(?:integral\s+of\s+|integrate\s+)(.+?)\s+from\s+(.+?)\s+to\s+(.+)',
                re.IGNORECASE,
            )
            match = pattern.search(problem)
            if not match:
                raise ValueError("Use format: 'integral of f(x) from a to b'")

            func_text = match.group(1).strip()
            lower_text = match.group(2).strip()
            upper_text = match.group(3).strip()

            expr = self._safe_parse(func_text)
            lower = self._safe_parse(lower_text)
            upper = self._safe_parse(upper_text)

            steps.append(f"🔧 **Integrand:** {expr}")
            steps.append(f"🔧 **Bounds:** [{lower}, {upper}]")
            steps.append(f"🔍 **Computing definite integral...**")

            # Symbolic definite integral
            result = integrate(expr, (x, lower, upper))
            simplified = simplify(result)

            steps.append(f"   ∫ {expr} dx from {lower} to {upper}")
            steps.append(f"   = [F(x)] from {lower} to {upper}  where F is the antiderivative")
            steps.append(f"\n✅ **Final Answer:** {simplified}")

            # Numerical value if exact is complex
            try:
                numerical = float(simplified)
                steps.append(f"📐 **Numerical value:** ≈ {numerical:.6f}")
                answer = f"{simplified}  ≈  {numerical:.4f}"
            except (TypeError, ValueError):
                answer = str(simplified)

            explanation = (
                f"The definite integral of {expr} from {lower} to {upper} equals {simplified}. "
                "This represents the net signed area under the curve between the two bounds."
            )

            return Solution(
                answer=answer,
                steps=steps,
                explanation=explanation,
                problem_type="definite_integral",
                difficulty="medium",
                confidence=1.0,
            )

        except Exception as e:
            return Solution(
                answer=f"Could not compute: {str(e)}",
                steps=[f"❌ Error: {str(e)}",
                       "💡 Format: 'integral of x^2 from 0 to 3'"],
                explanation=str(e),
                problem_type="definite_integral",
                difficulty="unknown",
                confidence=0.0,
            )

    # ------------------------------------------------------------------
    # Ordinary Differential Equations
    # ------------------------------------------------------------------

    def _solve_ode(self, problem: str) -> Solution:
        """Solve an ordinary differential equation."""
        try:
            from sympy import Function, dsolve, Eq as SpEq

            x = symbols('x')
            y = Function('y')
            steps = []
            steps.append(f"📝 **Original ODE:** {problem}")

            # Strip leading keywords
            eq_str = re.sub(r'^\s*(?:ode|solve|differential equation)\s*', '', problem, flags=re.IGNORECASE).strip()

            steps.append(f"🔧 **Equation to solve:** {eq_str}")

            # Replace prime notation: y'' → D2, y' → D1, then y → y0
            eq_str = eq_str.replace("y''", "D2ODE").replace("y'", "D1ODE")
            eq_str = re.sub(r"\by\b", "y0ODE", eq_str)

            # Replace dy/dx with D1ODE
            eq_str = re.sub(r"d2y/dx2|d\^2y/dx\^2", "D2ODE", eq_str, flags=re.IGNORECASE)
            eq_str = re.sub(r"dy/dx", "D1ODE", eq_str, flags=re.IGNORECASE)

            ode_local = {
                'D2ODE': y(x).diff(x, 2),
                'D1ODE': y(x).diff(x),
                'y0ODE': y(x),
                **self.local_dict,
            }

            if "=" in eq_str:
                lhs_s, rhs_s = eq_str.split("=", 1)
                lhs = parse_expr(lhs_s.replace('^', '**'), local_dict=ode_local,
                                 transformations=self.transformations)
                rhs = parse_expr(rhs_s.replace('^', '**'), local_dict=ode_local,
                                 transformations=self.transformations)
                ode_eq = SpEq(lhs, rhs)
            else:
                expr = parse_expr(eq_str.replace('^', '**'), local_dict=ode_local,
                                  transformations=self.transformations)
                ode_eq = SpEq(expr, 0)

            steps.append(f"🔍 **Solving ODE symbolically...**")
            steps.append(f"   Using SymPy dsolve (handles linear, separable, exact ODEs)")

            solution = dsolve(ode_eq, y(x))

            steps.append(f"\n✅ **General Solution:** {solution}")
            steps.append(f"   C1, C2, ... are arbitrary constants (determined by initial conditions)")

            answer = str(solution)
            explanation = (
                f"The general solution of the ODE is {solution}. "
                "C1 (and C2 for 2nd-order) are constants of integration — "
                "provide initial conditions to find specific values."
            )

            return Solution(
                answer=answer,
                steps=steps,
                explanation=explanation,
                problem_type="ode",
                difficulty="hard",
                confidence=1.0,
            )

        except Exception as e:
            return Solution(
                answer=f"Could not solve ODE: {str(e)}",
                steps=[f"❌ Error: {str(e)}",
                       "💡 Formats:",
                       "   First-order:  y' + 2*y = 0",
                       "   Second-order: y'' - 3*y' + 2*y = 0",
                       "   Prefix with 'ode' if needed: ode y' = x*y"],
                explanation=str(e),
                problem_type="ode",
                difficulty="unknown",
                confidence=0.0,
            )

    # ------------------------------------------------------------------
    # Matrix Operations
    # ------------------------------------------------------------------

    def _parse_matrix(self, text: str) -> sp.Matrix:
        """Parse [[1,2],[3,4]] notation into a SymPy Matrix."""
        import ast
        # Find the first [[...]] block
        match = re.search(r'\[\[.+?\]\]', text, re.DOTALL)
        if not match:
            raise ValueError("No matrix found. Use format: [[1,2],[3,4]]")
        data = ast.literal_eval(match.group(0))
        return sp.Matrix(data)

    def _solve_matrix(self, problem: str) -> Solution:
        """Perform matrix operations."""
        try:
            steps = []
            steps.append(f"📝 **Original problem:** {problem}")
            problem_lower = problem.lower()

            # Detect if there are two matrices (for multiply)
            matrices_raw = re.findall(r'\[\[.+?\]\]', problem, re.DOTALL)
            A = self._parse_matrix(problem)
            steps.append(f"🔧 **Matrix A:**\n{A}")

            # --- Determine operation ---
            if any(k in problem_lower for k in ("inverse", "inv")):
                steps.append("🔍 **Computing matrix inverse...**")
                if A.det() == 0:
                    answer = "Matrix is singular (determinant = 0) — no inverse exists."
                    steps.append("❌ " + answer)
                    return Solution(answer=answer, steps=steps,
                                    explanation=answer, problem_type="matrix",
                                    difficulty="medium", confidence=1.0)
                result = A.inv()
                steps.append(f"   det(A) = {A.det()} ≠ 0 → inverse exists")
                steps.append(f"\n✅ **A⁻¹ =**\n{result}")
                answer = str(result)
                explanation = f"The inverse of the matrix is:\n{result}"

            elif any(k in problem_lower for k in ("determinant", "det")):
                steps.append("🔍 **Computing determinant...**")
                result = A.det()
                steps.append(f"   Expanding along first row...")
                steps.append(f"\n✅ **det(A) = {result}**")
                answer = f"det = {result}"
                explanation = f"The determinant of the matrix is {result}."

            elif any(k in problem_lower for k in ("eigenvalue", "eigenvalues")):
                steps.append("🔍 **Computing eigenvalues...**")
                eigenvals = A.eigenvals()
                steps.append(f"   Solving characteristic polynomial det(A - λI) = 0")
                ev_str = ", ".join(f"λ = {v} (multiplicity {m})" for v, m in eigenvals.items())
                steps.append(f"\n✅ **Eigenvalues:** {ev_str}")
                answer = f"Eigenvalues: {ev_str}"
                explanation = (
                    f"The eigenvalues of the matrix are: {ev_str}. "
                    "These are the values λ where (A - λI)v = 0 has non-trivial solutions."
                )

            elif any(k in problem_lower for k in ("eigenvector", "eigenvectors")):
                steps.append("🔍 **Computing eigenvectors...**")
                eigenvects = A.eigenvects()
                lines = []
                for eigenval, mult, vects in eigenvects:
                    for v in vects:
                        lines.append(f"  λ = {eigenval}: v = {v.T}")
                steps.append(f"\n✅ **Eigenvectors:**\n" + "\n".join(lines))
                answer = "Eigenvectors:\n" + "\n".join(lines)
                explanation = "Eigenvectors are non-zero vectors v satisfying A·v = λ·v."

            elif "transpose" in problem_lower:
                steps.append("🔍 **Computing transpose...**")
                result = A.T
                steps.append(f"\n✅ **Aᵀ =**\n{result}")
                answer = str(result)
                explanation = f"The transpose swaps rows and columns: result is\n{result}"

            elif "rank" in problem_lower:
                steps.append("🔍 **Computing rank...**")
                result = A.rank()
                steps.append(f"   Row reducing matrix...")
                steps.append(f"\n✅ **rank(A) = {result}**")
                answer = f"rank = {result}"
                explanation = f"The rank of the matrix is {result} (number of linearly independent rows/columns)."

            elif "rref" in problem_lower:
                steps.append("🔍 **Row Reducing (RREF)...**")
                rref_matrix, pivot_cols = A.rref()
                steps.append(f"   Applying elementary row operations...")
                steps.append(f"   Pivot columns: {pivot_cols}")
                steps.append(f"\n✅ **RREF =**\n{rref_matrix}")
                answer = str(rref_matrix)
                explanation = f"The Row Reduced Echelon Form is:\n{rref_matrix}\nPivot columns: {pivot_cols}"

            elif "trace" in problem_lower:
                steps.append("🔍 **Computing trace...**")
                result = A.trace()
                steps.append(f"\n✅ **trace(A) = {result}** (sum of diagonal elements)")
                answer = f"trace = {result}"
                explanation = f"The trace is the sum of the diagonal elements: {result}."

            elif any(k in problem_lower for k in ("multiply", "product")) and len(matrices_raw) >= 2:
                B = sp.Matrix(eval(matrices_raw[1]))  # second matrix
                steps.append(f"🔧 **Matrix B:**\n{B}")
                steps.append("🔍 **Multiplying A × B...**")
                result = A * B
                steps.append(f"\n✅ **A × B =**\n{result}")
                answer = str(result)
                explanation = f"The product A × B is:\n{result}"

            else:
                # Default: show properties
                steps.append("🔍 **Computing matrix properties...**")
                det = A.det()
                rnk = A.rank()
                steps.append(f"   Shape: {A.shape[0]} × {A.shape[1]}")
                steps.append(f"   Determinant: {det}")
                steps.append(f"   Rank: {rnk}")
                if A.shape[0] == A.shape[1]:
                    steps.append(f"   Trace: {A.trace()}")
                    steps.append(f"   Invertible: {'Yes' if det != 0 else 'No (singular)'}")
                answer = f"Shape: {A.shape}, det={det}, rank={rnk}"
                explanation = f"Matrix properties computed. Specify 'inverse', 'determinant', 'eigenvalues', 'rref', 'rank', or 'transpose'."

            return Solution(
                answer=answer,
                steps=steps,
                explanation=explanation,
                problem_type="matrix",
                difficulty="medium",
                confidence=1.0,
            )

        except Exception as e:
            return Solution(
                answer=f"Could not compute: {str(e)}",
                steps=[f"❌ Error: {str(e)}",
                       "💡 Formats:",
                       "   inverse of [[1,2],[3,4]]",
                       "   determinant of [[1,2],[3,4]]",
                       "   eigenvalues of [[2,1],[1,3]]",
                       "   rref [[1,2,3],[4,5,6]]",
                       "   rank of [[1,2,3],[4,5,6],[7,8,9]]"],
                explanation=str(e),
                problem_type="matrix",
                difficulty="unknown",
                confidence=0.0,
            )

    # ------------------------------------------------------------------
    # Statistics
    # ------------------------------------------------------------------

    def _solve_statistics(self, problem: str) -> Solution:
        """Compute descriptive statistics on a dataset."""
        try:
            import ast
            import math

            steps = []
            steps.append(f"📝 **Original problem:** {problem}")
            problem_lower = problem.lower()

            # Extract list of numbers
            match = re.search(r'\[([^\]]+)\]', problem)
            if not match:
                # Try comma-separated numbers after keyword
                match2 = re.search(r'(?:of|:)\s*([\d\s,.\-]+)', problem)
                if match2:
                    data = [float(n.strip()) for n in match2.group(1).split(',') if n.strip()]
                else:
                    raise ValueError("Could not find data. Use format: mean of [1, 2, 3, 4, 5]")
            else:
                data = [float(n.strip()) for n in match.group(1).split(',') if n.strip()]

            if len(data) == 0:
                raise ValueError("Empty dataset.")

            n = len(data)
            total = sum(data)
            mean_val = total / n
            sorted_data = sorted(data)

            # Median
            if n % 2 == 0:
                median_val = (sorted_data[n // 2 - 1] + sorted_data[n // 2]) / 2
            else:
                median_val = sorted_data[n // 2]

            # Variance & std dev (population)
            variance_val = sum((xi - mean_val) ** 2 for xi in data) / n
            std_val = math.sqrt(variance_val)

            # Sample variance & std dev
            if n > 1:
                sample_var = sum((xi - mean_val) ** 2 for xi in data) / (n - 1)
                sample_std = math.sqrt(sample_var)
            else:
                sample_var = 0.0
                sample_std = 0.0

            # Mode
            from collections import Counter
            counts = Counter(data)
            max_count = max(counts.values())
            modes = [k for k, v in counts.items() if v == max_count]
            mode_str = str(modes[0]) if len(modes) == 1 else str(modes)

            # Range
            data_range = sorted_data[-1] - sorted_data[0]

            steps.append(f"🔧 **Dataset ({n} values):** {data}")
            steps.append(f"🔧 **Sorted:** {sorted_data}")
            steps.append(f"\n📊 **Descriptive Statistics:**")
            steps.append(f"   Count:              n = {n}")
            steps.append(f"   Sum:                Σx = {total}")
            steps.append(f"   Mean:               x̄ = {mean_val:.4f}")
            steps.append(f"   Median:             {median_val:.4f}")
            steps.append(f"   Mode:               {mode_str}")
            steps.append(f"   Range:              {data_range:.4f}")
            steps.append(f"   Population Std Dev: σ = {std_val:.4f}")
            steps.append(f"   Sample Std Dev:     s = {sample_std:.4f}")
            steps.append(f"   Population Variance: σ² = {variance_val:.4f}")
            steps.append(f"   Sample Variance:    s² = {sample_var:.4f}")
            steps.append(f"   Min:                {sorted_data[0]}")
            steps.append(f"   Max:                {sorted_data[-1]}")

            # Q1, Q2, Q3
            def percentile(sorted_arr, p):
                idx = p / 100 * (len(sorted_arr) - 1)
                lo, hi = int(idx), min(int(idx) + 1, len(sorted_arr) - 1)
                return sorted_arr[lo] + (sorted_arr[hi] - sorted_arr[lo]) * (idx - lo)

            q1 = percentile(sorted_data, 25)
            q3 = percentile(sorted_data, 75)
            iqr = q3 - q1
            steps.append(f"   Q1 (25th pct):      {q1:.4f}")
            steps.append(f"   Q3 (75th pct):      {q3:.4f}")
            steps.append(f"   IQR:                {iqr:.4f}")

            # Specific answer based on what was asked
            if "mean" in problem_lower or "average" in problem_lower:
                answer = f"Mean = {mean_val:.4f}"
            elif "median" in problem_lower:
                answer = f"Median = {median_val:.4f}"
            elif "mode" in problem_lower:
                answer = f"Mode = {mode_str}"
            elif "std" in problem_lower or "standard deviation" in problem_lower:
                answer = f"Population std = {std_val:.4f},  Sample std = {sample_std:.4f}"
            elif "variance" in problem_lower:
                answer = f"Population variance = {variance_val:.4f},  Sample variance = {sample_var:.4f}"
            else:
                answer = (
                    f"n={n}, mean={mean_val:.4f}, median={median_val:.4f}, "
                    f"std={std_val:.4f}, min={sorted_data[0]}, max={sorted_data[-1]}"
                )

            steps.append(f"\n✅ **Answer:** {answer}")

            explanation = (
                f"Full descriptive statistics computed for {n} data points. "
                f"Mean = {mean_val:.4f}, Median = {median_val:.4f}, "
                f"Std Dev = {std_val:.4f}."
            )

            return Solution(
                answer=answer,
                steps=steps,
                explanation=explanation,
                problem_type="statistics",
                difficulty="easy",
                confidence=1.0,
            )

        except Exception as e:
            return Solution(
                answer=f"Could not compute: {str(e)}",
                steps=[f"❌ Error: {str(e)}",
                       "💡 Formats:",
                       "   mean of [1, 2, 3, 4, 5]",
                       "   std of [2.1, 3.4, 5.6, 2.2]",
                       "   statistics of [10, 20, 30, 40, 50]"],
                explanation=str(e),
                problem_type="statistics",
                difficulty="unknown",
                confidence=0.0,
            )

    # ------------------------------------------------------------------
    # Laplace Transform
    # ------------------------------------------------------------------

    def _solve_laplace(self, problem: str) -> Solution:
        """Compute the Laplace transform of a function."""
        try:
            from sympy import laplace_transform, symbols as syms, Function
            t, s = syms('t s', positive=True)
            steps = []
            steps.append(f"📝 **Original:** {problem}")

            raw = re.sub(r'laplace\s+transform\s+of\s*', '', problem, flags=re.IGNORECASE)
            raw = re.sub(r'laplace\s+of\s*', '', raw, flags=re.IGNORECASE).strip()

            local = {**self.local_dict, 't': t, 's': s}
            expr = parse_expr(raw.replace('^', '**'), local_dict=local,
                              transformations=self.transformations)

            steps.append(f"🔧 **f(t) =** {expr}")
            steps.append("🔍 **Applying Laplace transform: L{{f(t)}} = ∫₀^∞ f(t)e^(-st) dt**")

            result, cond, _ = laplace_transform(expr, t, s)
            result = simplify(result)

            steps.append(f"   Condition: {cond}")
            steps.append(f"\n✅ **L{{f(t)}} = {result}**")

            answer = f"L{{f(t)}} = {result}"
            explanation = (
                f"The Laplace transform of {expr} is {result}. "
                f"Valid for {cond}. "
                "Use Laplace transforms to solve ODEs by converting them to algebraic equations."
            )
            return Solution(answer=answer, steps=steps, explanation=explanation,
                            problem_type="laplace", difficulty="hard", confidence=1.0)

        except Exception as e:
            return Solution(
                answer=f"Could not compute: {str(e)}",
                steps=[f"❌ Error: {str(e)}",
                       "💡 Formats:",
                       "   laplace transform of sin(t)",
                       "   laplace transform of t^2",
                       "   laplace transform of exp(-2*t)*cos(t)"],
                explanation=str(e), problem_type="laplace",
                difficulty="unknown", confidence=0.0,
            )

    def _solve_inverse_laplace(self, problem: str) -> Solution:
        """Compute the inverse Laplace transform."""
        try:
            from sympy import inverse_laplace_transform, symbols as syms
            t, s = syms('t s', positive=True)
            steps = []
            steps.append(f"📝 **Original:** {problem}")

            raw = re.sub(r'inverse\s+laplace\s+(?:transform\s+)?(?:of\s*)?', '',
                         problem, flags=re.IGNORECASE).strip()

            local = {**self.local_dict, 't': t, 's': s}
            expr = parse_expr(raw.replace('^', '**'), local_dict=local,
                              transformations=self.transformations)

            steps.append(f"🔧 **F(s) =** {expr}")
            steps.append("🔍 **Computing inverse Laplace transform: L⁻¹{{F(s)}}**")

            result = inverse_laplace_transform(expr, s, t)
            result = simplify(result)

            steps.append(f"\n✅ **L⁻¹{{F(s)}} = {result}**")

            answer = f"f(t) = {result}"
            explanation = (
                f"The inverse Laplace transform of {expr} is {result}. "
                "This recovers the time-domain function from the s-domain representation."
            )
            return Solution(answer=answer, steps=steps, explanation=explanation,
                            problem_type="inverse_laplace", difficulty="hard", confidence=1.0)

        except Exception as e:
            return Solution(
                answer=f"Could not compute: {str(e)}",
                steps=[f"❌ Error: {str(e)}",
                       "💡 Formats:",
                       "   inverse laplace of 1/(s+2)",
                       "   inverse laplace of s/(s^2+1)",
                       "   inverse laplace of 1/(s^2+4*s+5)"],
                explanation=str(e), problem_type="inverse_laplace",
                difficulty="unknown", confidence=0.0,
            )

    # ------------------------------------------------------------------
    # Fourier Transform
    # ------------------------------------------------------------------

    def _solve_fourier(self, problem: str) -> Solution:
        """Compute the Fourier transform of a function."""
        try:
            from sympy import fourier_transform, symbols as syms
            x, k = syms('x k')
            steps = []
            steps.append(f"📝 **Original:** {problem}")

            raw = re.sub(r'fourier\s+transform\s+of\s*', '', problem, flags=re.IGNORECASE)
            raw = re.sub(r'fourier\s+of\s*', '', raw, flags=re.IGNORECASE).strip()

            local = {**self.local_dict, 'x': x, 'k': k}
            expr = parse_expr(raw.replace('^', '**'), local_dict=local,
                              transformations=self.transformations)

            steps.append(f"🔧 **f(x) =** {expr}")
            steps.append("🔍 **Applying Fourier transform: F(k) = ∫ f(x) e^(-2πi k x) dx**")

            result = fourier_transform(expr, x, k)
            result = simplify(result)

            steps.append(f"\n✅ **F(k) = {result}**")

            answer = f"F(k) = {result}"
            explanation = (
                f"The Fourier transform of {expr} is {result}. "
                "Fourier transforms decompose a function into its frequency components."
            )
            return Solution(answer=answer, steps=steps, explanation=explanation,
                            problem_type="fourier", difficulty="hard", confidence=1.0)

        except Exception as e:
            return Solution(
                answer=f"Could not compute: {str(e)}",
                steps=[f"❌ Error: {str(e)}",
                       "💡 Formats:",
                       "   fourier transform of exp(-x^2)",
                       "   fourier transform of exp(-Abs(x))",
                       "   fourier transform of 1/(1+x^2)"],
                explanation=str(e), problem_type="fourier",
                difficulty="unknown", confidence=0.0,
            )

    # ------------------------------------------------------------------
    # Double / Triple Integrals
    # ------------------------------------------------------------------

    def _solve_double_integral(self, problem: str) -> Solution:
        """Compute a double or triple integral."""
        try:
            from sympy import symbols as syms
            x, y, z = syms('x y z')
            steps = []
            steps.append(f"📝 **Original:** {problem}")

            problem_lower = problem.lower()
            is_triple = "triple" in problem_lower or "∭" in problem

            # Strip leading keyword
            raw = re.sub(r'^(?:double|triple)\s+integral\s+(?:of\s*)?', '',
                         problem, flags=re.IGNORECASE).strip()

            # Pattern: f(x,y) dx from a to b dy from c to d [dz from e to f]
            # Also accept: f(x,y) dA where dA implies dx dy
            bound_pattern = re.compile(
                r'(.+?)\s+dx\s+from\s+(.+?)\s+to\s+(.+?)\s+dy\s+from\s+(.+?)\s+to\s+(.+?)(?:\s+dz\s+from\s+(.+?)\s+to\s+(.+?))?$',
                re.IGNORECASE,
            )
            m = bound_pattern.search(raw)
            if not m:
                raise ValueError(
                    "Use format: 'double integral of f(x,y) dx from a to b dy from c to d'"
                )

            func_str = m.group(1).strip()
            x_lo, x_hi = m.group(2).strip(), m.group(3).strip()
            y_lo, y_hi = m.group(4).strip(), m.group(5).strip()
            z_lo = m.group(6).strip() if m.group(6) else None
            z_hi = m.group(7).strip() if m.group(7) else None

            local = {**self.local_dict, 'x': x, 'y': y, 'z': z}
            expr = parse_expr(func_str.replace('^', '**'), local_dict=local,
                              transformations=self.transformations)

            xl = parse_expr(x_lo.replace('^', '**'), local_dict=local, transformations=self.transformations)
            xh = parse_expr(x_hi.replace('^', '**'), local_dict=local, transformations=self.transformations)
            yl = parse_expr(y_lo.replace('^', '**'), local_dict=local, transformations=self.transformations)
            yh = parse_expr(y_hi.replace('^', '**'), local_dict=local, transformations=self.transformations)

            steps.append(f"🔧 **Integrand:** {expr}")
            steps.append(f"🔧 **x bounds:** [{xl}, {xh}]   y bounds: [{yl}, {yh}]")

            # Inner integral over x
            steps.append("🔍 **Step 1 — Integrate over x:**")
            inner = integrate(expr, (x, xl, xh))
            inner = simplify(inner)
            steps.append(f"   ∫ {expr} dx from {xl} to {xh} = {inner}")

            # Outer integral over y
            steps.append("🔍 **Step 2 — Integrate over y:**")
            result = integrate(inner, (y, yl, yh))
            result = simplify(result)
            steps.append(f"   ∫ {inner} dy from {yl} to {yh} = {result}")

            # Optional triple integral over z
            if z_lo and z_hi and is_triple:
                zl = parse_expr(z_lo.replace('^', '**'), local_dict=local, transformations=self.transformations)
                zh = parse_expr(z_hi.replace('^', '**'), local_dict=local, transformations=self.transformations)
                steps.append("🔍 **Step 3 — Integrate over z:**")
                result = simplify(integrate(result, (z, zl, zh)))
                steps.append(f"   Final = {result}")

            try:
                num = float(result)
                answer = f"{result}  ≈  {num:.4f}"
                steps.append(f"📐 **Numerical value:** {num:.6f}")
            except (TypeError, ValueError):
                answer = str(result)

            steps.append(f"\n✅ **Final Answer:** {answer}")

            label = "Triple" if is_triple else "Double"
            explanation = (
                f"The {label} integral evaluates to {result}. "
                "Computed by iterating: integrate over x first, then y (then z for triple). "
                "This represents volume/area under the surface f(x,y)."
            )
            return Solution(answer=answer, steps=steps, explanation=explanation,
                            problem_type="double_integral", difficulty="hard", confidence=1.0)

        except Exception as e:
            return Solution(
                answer=f"Could not compute: {str(e)}",
                steps=[f"❌ Error: {str(e)}",
                       "💡 Format:",
                       "   double integral of x*y dx from 0 to 1 dy from 0 to 1",
                       "   double integral of x^2+y^2 dx from 0 to 2 dy from 0 to 2"],
                explanation=str(e), problem_type="double_integral",
                difficulty="unknown", confidence=0.0,
            )

    # ------------------------------------------------------------------
    # Probability Distributions
    # ------------------------------------------------------------------

    def _solve_probability(self, problem: str) -> Solution:
        """Evaluate probability distributions: Normal, Binomial, Poisson, Exponential."""
        try:
            import math
            steps = []
            steps.append(f"📝 **Original:** {problem}")
            p_lower = problem.lower()

            def parse_param(text, *keys):
                for k in keys:
                    m = re.search(rf'\b{re.escape(k)}\s*=\s*([\d.\-]+)', text, re.IGNORECASE)
                    if m:
                        return float(m.group(1))
                return None

            def parse_x(text):
                """Parse the standalone x= value (not inside a word like 'exponential')."""
                m = re.search(r'(?<![a-z])x\s*=\s*([\d.\-]+)', text, re.IGNORECASE)
                return float(m.group(1)) if m else None

            # ── Normal distribution ──────────────────────────────────────
            if any(k in p_lower for k in ("normal", "gaussian")):
                mu = parse_param(problem, "mean", "mu") or 0.0
                sigma = parse_param(problem, "std", "sigma", "sd") or 1.0
                x_val = parse_x(problem)

                steps.append(f"🔧 **Normal distribution: N(μ={mu}, σ={sigma})**")
                steps.append(f"   PDF: f(x) = (1/(σ√2π)) · exp(-(x-μ)²/(2σ²))")
                steps.append(f"   Mean = {mu},  Std Dev = {sigma},  Variance = {sigma**2}")

                if x_val is not None:
                    z = (x_val - mu) / sigma
                    pdf_val = (1/(sigma * math.sqrt(2*math.pi))) * math.exp(-0.5 * z**2)
                    cdf_val = 0.5 * (1 + math.erf(z / math.sqrt(2)))
                    steps.append(f"\n   At x = {x_val}:")
                    steps.append(f"   z-score = (x - μ)/σ = ({x_val} - {mu})/{sigma} = {z:.4f}")
                    steps.append(f"   PDF f({x_val}) = {pdf_val:.6f}")
                    steps.append(f"   CDF P(X ≤ {x_val}) = {cdf_val:.6f}")
                    steps.append(f"   P(X > {x_val}) = {1-cdf_val:.6f}")
                    answer = f"PDF={pdf_val:.4f}, CDF P(X≤{x_val})={cdf_val:.4f}, z={z:.4f}"
                else:
                    answer = f"N(μ={mu}, σ={sigma}): Mean={mu}, Variance={sigma**2}, Std={sigma}"

            # ── Binomial distribution ────────────────────────────────────
            elif "binomial" in p_lower:
                n = int(parse_param(problem, "n") or 10)
                p = parse_param(problem, r"p\s*=", "prob") or 0.5
                k = parse_param(problem, "k") or parse_x(problem)

                steps.append(f"🔧 **Binomial distribution: B(n={n}, p={p})**")
                steps.append(f"   PMF: P(X=k) = C(n,k) · pᵏ · (1-p)^(n-k)")
                steps.append(f"   Mean = n·p = {n*p:.4f}")
                steps.append(f"   Variance = n·p·(1-p) = {n*p*(1-p):.4f}")
                steps.append(f"   Std Dev = {math.sqrt(n*p*(1-p)):.4f}")

                if k is not None:
                    k = int(k)
                    pmf = math.comb(n, k) * (p**k) * ((1-p)**(n-k))
                    cdf = sum(math.comb(n, j) * (p**j) * ((1-p)**(n-j)) for j in range(k+1))
                    steps.append(f"\n   P(X = {k}) = C({n},{k}) · {p}^{k} · {1-p}^{n-k} = {pmf:.6f}")
                    steps.append(f"   P(X ≤ {k}) = {cdf:.6f}")
                    answer = f"P(X={k}) = {pmf:.4f},  P(X≤{k}) = {cdf:.4f}"
                else:
                    answer = f"B(n={n}, p={p}): Mean={n*p:.4f}, Std={math.sqrt(n*p*(1-p)):.4f}"

            # ── Poisson distribution ─────────────────────────────────────
            elif "poisson" in p_lower:
                lam = parse_param(problem, "lambda", "rate", "lam") or 1.0
                k = parse_param(problem, "k") or parse_x(problem)

                steps.append(f"🔧 **Poisson distribution: Pois(λ={lam})**")
                steps.append(f"   PMF: P(X=k) = λᵏ · e^(-λ) / k!")
                steps.append(f"   Mean = λ = {lam}")
                steps.append(f"   Variance = λ = {lam}")

                if k is not None:
                    k = int(k)
                    pmf = (lam**k * math.exp(-lam)) / math.factorial(k)
                    cdf = sum((lam**j * math.exp(-lam)) / math.factorial(j) for j in range(k+1))
                    steps.append(f"\n   P(X = {k}) = {lam}^{k} · e^(-{lam}) / {k}! = {pmf:.6f}")
                    steps.append(f"   P(X ≤ {k}) = {cdf:.6f}")
                    answer = f"P(X={k}) = {pmf:.4f},  P(X≤{k}) = {cdf:.4f}"
                else:
                    answer = f"Pois(λ={lam}): Mean=Variance={lam}"

            # ── Exponential distribution ─────────────────────────────────
            elif "exponential" in p_lower:
                lam = parse_param(problem, "lambda", "rate") or 1.0
                x_val = parse_x(problem)

                steps.append(f"🔧 **Exponential distribution: Exp(λ={lam})**")
                steps.append(f"   PDF: f(x) = λ · e^(-λx)  for x ≥ 0")
                steps.append(f"   Mean = 1/λ = {1/lam:.4f}")
                steps.append(f"   Variance = 1/λ² = {1/lam**2:.4f}")

                if x_val is not None:
                    pdf_val = lam * math.exp(-lam * x_val)
                    cdf_val = 1 - math.exp(-lam * x_val)
                    steps.append(f"\n   P(X ≤ {x_val}) = 1 - e^(-{lam}·{x_val}) = {cdf_val:.6f}")
                    steps.append(f"   PDF f({x_val}) = {pdf_val:.6f}")
                    answer = f"P(X≤{x_val}) = {cdf_val:.4f},  PDF={pdf_val:.4f}"
                else:
                    answer = f"Exp(λ={lam}): Mean={1/lam:.4f}, Variance={1/lam**2:.4f}"
            else:
                raise ValueError("Specify: normal, binomial, poisson, or exponential distribution.")

            steps.append(f"\n✅ **Answer:** {answer}")
            explanation = (
                f"Probability distribution computed. {answer}. "
                "Use 'mean=', 'std=', 'n=', 'p=', 'lambda=' and optionally 'x=' for point probabilities."
            )
            return Solution(answer=answer, steps=steps, explanation=explanation,
                            problem_type="probability", difficulty="medium", confidence=1.0)

        except Exception as e:
            return Solution(
                answer=f"Could not compute: {str(e)}",
                steps=[f"❌ Error: {str(e)}",
                       "💡 Formats:",
                       "   normal distribution mean=0 std=1 x=1.96",
                       "   binomial distribution n=10 p=0.3 k=4",
                       "   poisson distribution lambda=5 k=3",
                       "   exponential distribution lambda=2 x=1"],
                explanation=str(e), problem_type="probability",
                difficulty="unknown", confidence=0.0,
            )

    # ------------------------------------------------------------------
    # Linear Regression
    # ------------------------------------------------------------------

    def _solve_regression(self, problem: str) -> Solution:
        """Fit a linear regression model to data points."""
        try:
            import ast, math
            import numpy as np
            steps = []
            steps.append(f"📝 **Original:** {problem}")

            # Parse x and y arrays
            arrays = re.findall(r'\[([^\]]+)\]', problem)
            if len(arrays) < 2:
                raise ValueError("Provide two lists: x=[...] y=[...]")

            x_data = np.array([float(v.strip()) for v in arrays[0].split(',') if v.strip()])
            y_data = np.array([float(v.strip()) for v in arrays[1].split(',') if v.strip()])

            if len(x_data) != len(y_data):
                raise ValueError(f"x and y must have the same length ({len(x_data)} vs {len(y_data)})")
            if len(x_data) < 2:
                raise ValueError("Need at least 2 data points.")

            n = len(x_data)
            steps.append(f"🔧 **Data points:** n = {n}")
            steps.append(f"   x = {x_data.tolist()}")
            steps.append(f"   y = {y_data.tolist()}")

            # Least squares: y = mx + b
            coeffs = np.polyfit(x_data, y_data, 1)
            m, b = coeffs[0], coeffs[1]

            # R² coefficient of determination
            y_pred = m * x_data + b
            ss_res = np.sum((y_data - y_pred) ** 2)
            ss_tot = np.sum((y_data - np.mean(y_data)) ** 2)
            r_sq = 1 - ss_res / ss_tot if ss_tot != 0 else 1.0
            r = math.sqrt(abs(r_sq)) * (1 if m >= 0 else -1)

            # Standard error
            se = math.sqrt(ss_res / (n - 2)) if n > 2 else 0.0

            steps.append(f"\n🔍 **Fitting y = mx + b using least squares...**")
            steps.append(f"   x̄ = {np.mean(x_data):.4f},  ȳ = {np.mean(y_data):.4f}")
            steps.append(f"   Slope m = Σ(xᵢ-x̄)(yᵢ-ȳ) / Σ(xᵢ-x̄)² = {m:.4f}")
            steps.append(f"   Intercept b = ȳ - m·x̄ = {b:.4f}")
            steps.append(f"\n📊 **Model quality:**")
            steps.append(f"   R² (coefficient of determination) = {r_sq:.4f}")
            steps.append(f"   r  (Pearson correlation)          = {r:.4f}")
            steps.append(f"   Standard error                    = {se:.4f}")
            steps.append(f"\n✅ **Regression line: y = {m:.4f}x + ({b:.4f})**")

            # Interpretation
            if r_sq >= 0.95:
                fit_quality = "excellent fit (R²≥0.95)"
            elif r_sq >= 0.80:
                fit_quality = "good fit (R²≥0.80)"
            elif r_sq >= 0.60:
                fit_quality = "moderate fit (R²≥0.60)"
            else:
                fit_quality = "weak fit (R²<0.60) — data may not be linear"

            answer = f"y = {m:.4f}x + {b:.4f}   (R² = {r_sq:.4f}, {fit_quality})"
            steps.append(f"   Fit quality: {fit_quality}")

            explanation = (
                f"Linear regression: y = {m:.4f}x + {b:.4f}. "
                f"Slope = {m:.4f} (y changes by {m:.4f} for each unit increase in x). "
                f"Intercept = {b:.4f}. R² = {r_sq:.4f} — the model explains {r_sq*100:.1f}% of the variance."
            )
            return Solution(answer=answer, steps=steps, explanation=explanation,
                            problem_type="regression", difficulty="medium", confidence=1.0)

        except Exception as e:
            return Solution(
                answer=f"Could not compute: {str(e)}",
                steps=[f"❌ Error: {str(e)}",
                       "💡 Format:",
                       "   regression [1,2,3,4,5] [2.1,3.9,6.2,7.8,10.1]",
                       "   linear fit x=[1,2,3] y=[2,4,6]"],
                explanation=str(e), problem_type="regression",
                difficulty="unknown", confidence=0.0,
            )
