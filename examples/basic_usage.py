#!/usr/bin/env python3
"""
Basic usage examples for Numen reasoning engine.
"""

from numen import NumenEngine


def example_simple_algebra():
    """Solve simple algebraic equation."""
    print("=" * 60)
    print("Example 1: Simple Algebra")
    print("=" * 60)

    engine = NumenEngine(use_mcts=False, require_verification=True)

    problem = "Solve for x: 2x + 5 = 13"
    result = engine.solve(problem)

    print(f"\nProblem: {problem}")
    print(f"Solution: {result.solution}")
    print(f"Verified: {result.verified}")
    print(f"Confidence: {result.confidence:.2%}")
    print(f"\nReasoning chain:")
    for step in result.reasoning_chain:
        print(f"  - {step}")


def example_cryptanalysis():
    """Analyze RSA parameters."""
    print("\n" + "=" * 60)
    print("Example 2: Cryptanalysis")
    print("=" * 60)

    from numen.strategies.cryptanalysis import CryptanalysisStrategy

    crypto = CryptanalysisStrategy()

    # Weak RSA parameters
    n = 77  # 7 × 11 (easily factored)
    e = 7

    vulnerabilities = crypto.analyze_rsa_parameters(n, e)

    print(f"\nAnalyzing RSA with n={n}, e={e}")
    print(f"\nFound {len(vulnerabilities)} vulnerabilities:")

    for vuln in vulnerabilities:
        print(f"\n  Type: {vuln.type.value}")
        print(f"  Severity: {vuln.severity:.1f}/1.0")
        print(f"  Description: {vuln.description}")
        print(f"  Attack: {vuln.attack_vector}")
        print(f"  Mitigation: {vuln.mitigation}")


def example_neural_analysis():
    """Analyze neural dynamics."""
    print("\n" + "=" * 60)
    print("Example 3: Neural Dynamics Analysis")
    print("=" * 60)

    from numen.strategies.neural_analysis import NeuralAnalysisStrategy, CognitiveState
    import numpy as np

    neural = NeuralAnalysisStrategy()

    # Simulate neural signal data
    signal_data = {
        "eeg_alpha": np.random.randn(100) * 0.5,  # Low variance
    }

    # Build dynamical model
    dynamics = neural.model_as_dynamical_system(signal_data)

    print(f"\nDynamical Model:")
    print(f"  Equations:")
    for eq in dynamics.equations:
        print(f"    {eq}")

    print(f"\n  Equilibria: {len(dynamics.equilibria)}")
    print(f"  Stability: {dynamics.stability}")

    # Predict cognitive state
    current_signal = signal_data["eeg_alpha"]
    state = neural.predict_cognitive_state(current_signal, dynamics)

    print(f"\nPredicted Cognitive State: {state.value}")

    # Predict transitions
    transitions = neural.predict_state_transition(state, dynamics)

    if transitions:
        print(f"\nPossible Transitions:")
        for trans in transitions:
            print(f"  {trans.from_state.value} → {trans.to_state.value}")
            print(f"    Probability: {trans.probability:.2%}")
            print(f"    Time: {trans.time_to_transition:.1f}s")


def example_cross_domain():
    """Cross-domain translation."""
    print("\n" + "=" * 60)
    print("Example 4: Cross-Domain Translation")
    print("=" * 60)

    from numen.strategies.cross_domain import CrossDomainTranslator, MathDomain

    translator = CrossDomainTranslator()

    # Topology to Cryptography
    crypto_problem = "Does this protocol have unique key derivation paths?"
    topological_view = translator.translate(
        crypto_problem,
        source_domain=MathDomain.CRYPTOGRAPHY,
        target_domain=MathDomain.TOPOLOGY,
    )

    print(f"\nOriginal (Cryptography): {crypto_problem}")
    print(f"Translated (Topology): {topological_view}")

    # Find analogies
    problem = "Find stable equilibrium points"
    analogies = translator.find_analogies(problem, MathDomain.DIFFERENTIAL_EQUATIONS)

    print(f"\n\nFinding analogies for: '{problem}'")
    print(f"Source domain: Differential Equations")
    print(f"\nAnalogous problems:")
    for domain, analogous in analogies:
        print(f"  [{domain.value}]: {analogous}")


def example_verification():
    """Symbolic verification."""
    print("\n" + "=" * 60)
    print("Example 5: Symbolic Verification")
    print("=" * 60)

    from numen.core.verifier import SymbolicVerifier

    verifier = SymbolicVerifier()

    # Test cases
    test_cases = [
        ("Solve 2x+5=13", "x=4", True),
        ("Solve 2x+5=13", "x=3", False),
        ("Simplify x²-1", "(x-1)(x+1)", True),
    ]

    for problem, solution, should_pass in test_cases:
        result = verifier.verify_solution(problem, solution)
        status = "✓" if result.confidence > 0.8 else "✗"
        print(f"\n{status} Problem: {problem}")
        print(f"  Solution: {solution}")
        print(f"  Status: {result.status.value}")
        print(f"  Confidence: {result.confidence:.2%}")
        print(f"  Explanation: {result.explanation}")


def main():
    """Run all examples."""
    print("\n" + "=" * 60)
    print("NUMEN MATHEMATICAL REASONING ENGINE - EXAMPLES")
    print("=" * 60)

    example_simple_algebra()
    example_cryptanalysis()
    example_neural_analysis()
    example_cross_domain()
    example_verification()

    print("\n" + "=" * 60)
    print("Examples complete!")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
