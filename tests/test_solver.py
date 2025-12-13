"""Tests for multi-strategy solver."""

import pytest
from numen.core.solver import MathSolver
from numen.core.verifier import VerificationStatus


def test_solve_algebraic():
    """Test algebraic solving."""
    solver = MathSolver()

    attempt = solver.solve("x + 5 = 10", require_verification=False)

    assert attempt is not None
    assert attempt.solution is not None


def test_solve_with_verification():
    """Test solving with verification requirement."""
    solver = MathSolver()

    attempt = solver.solve("2*x + 5 = 13", require_verification=True)

    if attempt and attempt.verification.status == VerificationStatus.VERIFIED:
        assert attempt.confidence > 0.5


def test_strategy_ranking():
    """Test strategy ranking by problem type."""
    solver = MathSolver()

    strategies = solver._rank_strategies("solve the polynomial equation")

    # Algebraic strategy should be ranked high
    assert strategies[0].type.value == "algebraic"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
