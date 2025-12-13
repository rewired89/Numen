"""Tests for symbolic verifier."""

import pytest
from numen.core.verifier import SymbolicVerifier, VerificationStatus


def test_verify_simple_equation():
    """Test verification of simple equation."""
    verifier = SymbolicVerifier()

    result = verifier.verify_solution(
        problem="2x + 5 = 13",
        solution="4",
    )

    assert result.status == VerificationStatus.VERIFIED
    assert result.confidence == 1.0


def test_verify_incorrect_solution():
    """Test rejection of incorrect solution."""
    verifier = SymbolicVerifier()

    result = verifier.verify_solution(
        problem="2x + 5 = 13",
        solution="3",
    )

    assert result.status == VerificationStatus.FAILED


def test_verify_simplification():
    """Test simplification verification."""
    verifier = SymbolicVerifier()

    result = verifier.verify_solution(
        problem="Simplify x**2 - 1",
        solution="(x-1)*(x+1)",
    )

    # Should verify as equivalent
    assert result.confidence > 0.8


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
