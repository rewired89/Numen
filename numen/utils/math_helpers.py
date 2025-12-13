"""Mathematical helper utilities."""

import sympy as sp
from typing import Optional


def parse_math_expression(expr_str: str) -> Optional[sp.Expr]:
    """Safely parse mathematical expression."""
    try:
        return sp.sympify(expr_str)
    except:
        return None


def simplify_expression(expr: sp.Expr) -> sp.Expr:
    """Simplify mathematical expression."""
    return sp.simplify(expr)
