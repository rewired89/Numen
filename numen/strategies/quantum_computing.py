"""
Quantum computing strategies for cryptanalysis and optimization.

Analyzes quantum algorithms and their implications for:
- Post-quantum cryptography
- Quantum speedup analysis
- Quantum attack vectors
"""

from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import math


class QuantumAlgorithm(Enum):
    """Quantum algorithms for various problems."""

    SHORS = "shors"  # Integer factorization
    GROVERS = "grovers"  # Unstructured search
    SIMONS = "simons"  # Period finding
    DEUTSCH_JOZSA = "deutsch_jozsa"  # Function property detection
    HHL = "hhl"  # Linear systems
    VQE = "vqe"  # Variational quantum eigensolver


@dataclass
class QuantumSpeedup:
    """Analysis of quantum algorithm speedup."""

    algorithm: QuantumAlgorithm
    classical_complexity: str
    quantum_complexity: str
    speedup_factor: str
    problem_size: int
    description: str
    practical_qubits_needed: int
    fault_tolerance_required: bool


@dataclass
class PostQuantumAnalysis:
    """Post-quantum cryptography analysis."""

    current_system: str
    quantum_vulnerable: bool
    time_to_break_classical: str
    time_to_break_quantum: str
    recommended_alternative: str
    security_level_bits_classical: int
    security_level_bits_quantum: int


class QuantumComputingStrategy:
    """
    Quantum computing analysis for cryptography and optimization.

    Focus areas:
    - Shor's algorithm for factorization (RSA breaking)
    - Grover's algorithm for search (symmetric crypto)
    - Post-quantum cryptography recommendations
    - Quantum resource estimation
    """

    def analyze_shors_algorithm(
        self,
        n: int,
        estimate_resources: bool = True,
    ) -> Dict[str, Any]:
        """
        Analyze Shor's algorithm for factoring integer n.

        Shor's algorithm factors n in O((log n)³) time with high probability.

        Args:
            n: Integer to factor
            estimate_resources: Estimate quantum resources needed

        Returns:
            Analysis including speedup, qubit requirements, gate count
        """
        bit_length = n.bit_length()

        # Classical complexity (GNFS - General Number Field Sieve)
        # O(exp((64/9 * ln(n) * ln(ln(n)))^(1/3)))
        ln_n = math.log(n)
        ln_ln_n = math.log(ln_n) if ln_n > 1 else 1
        classical_exp = (64/9 * ln_n * ln_ln_n) ** (1/3)

        # Quantum complexity: O((log n)³)
        quantum_ops = bit_length ** 3

        # Qubit requirements
        # Need ~2n + 3 qubits for Shor's algorithm
        qubits_needed = 2 * bit_length + 3

        # Gate count estimation
        # Rough estimate: O(n² log n) gates
        gates_needed = bit_length ** 2 * math.log2(bit_length) if bit_length > 1 else 1

        # Time estimation (on current/near-term quantum computers)
        # Assume gate time ~100ns, need error correction (multiply by ~1000)
        gate_time_ns = 100
        error_correction_overhead = 1000
        estimated_time_seconds = (gates_needed * gate_time_ns * error_correction_overhead) / 1e9

        analysis = {
            "algorithm": "Shor's Factorization",
            "input_size": n,
            "input_bits": bit_length,
            "classical_complexity": f"O(exp({classical_exp:.2f})) ≈ 2^{classical_exp:.1f} operations",
            "quantum_complexity": f"O((log n)³) ≈ {quantum_ops:.0f} operations",
            "speedup": "Exponential",
            "qubits_required": qubits_needed,
            "logical_gates_required": int(gates_needed),
            "estimated_runtime_seconds": estimated_time_seconds,
            "estimated_runtime_readable": self._format_time(estimated_time_seconds),
            "fault_tolerance_required": True,
            "feasible_with_current_tech": qubits_needed < 100 and n < 2**2048,  # Conservative
            "notes": [],
        }

        # Add specific notes
        if qubits_needed > 4000:
            analysis["notes"].append(
                f"Requires {qubits_needed} logical qubits - beyond current hardware"
            )
        elif qubits_needed > 1000:
            analysis["notes"].append(
                "Requires medium-scale fault-tolerant quantum computer (5-10 years)"
            )
        else:
            analysis["notes"].append(
                "Within reach of near-term fault-tolerant quantum computers"
            )

        # Error correction overhead
        physical_qubits = qubits_needed * 1000  # Rough surface code estimate
        analysis["physical_qubits_estimated"] = physical_qubits

        if physical_qubits > 100000:
            analysis["notes"].append(
                f"Estimated {physical_qubits:,} physical qubits needed for error correction"
            )

        return analysis

    def analyze_grovers_algorithm(
        self,
        search_space_size: int,
        key_bits: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Analyze Grover's algorithm for unstructured search.

        Grover's algorithm searches N items in O(√N) time.
        Implications for symmetric cryptography (AES, etc.)

        Args:
            search_space_size: Size of search space (e.g., 2^128 for AES-128)
            key_bits: Number of key bits (if applicable)

        Returns:
            Analysis of quantum search speedup
        """
        N = search_space_size

        if key_bits is None:
            key_bits = math.log2(N) if N > 1 else 1

        # Classical brute force: O(N)
        classical_ops = N

        # Grover's algorithm: O(√N)
        quantum_ops = math.sqrt(N)

        # Speedup factor
        speedup = classical_ops / quantum_ops if quantum_ops > 0 else 1

        # Effective key bits after Grover's
        effective_bits_quantum = key_bits / 2

        # Qubit requirements (need log₂(N) qubits)
        qubits_needed = int(math.log2(N)) if N > 1 else 1

        analysis = {
            "algorithm": "Grover's Search",
            "search_space_size": N,
            "key_bits_classical": key_bits,
            "effective_bits_quantum": effective_bits_quantum,
            "classical_complexity": f"O(N) = O(2^{key_bits:.0f}) operations",
            "quantum_complexity": f"O(√N) = O(2^{effective_bits_quantum:.0f}) operations",
            "speedup_factor": f"√N ≈ {speedup:.2e}x",
            "qubits_required": qubits_needed,
            "iterations_needed": int(quantum_ops),
        }

        # Security implications
        if effective_bits_quantum < 128:
            analysis["security_status"] = "VULNERABLE"
            analysis["recommendation"] = f"Increase key size to {int(effective_bits_quantum * 2) + 128} bits for post-quantum security"
        else:
            analysis["security_status"] = "SECURE"
            analysis["recommendation"] = "Current key size provides post-quantum security against Grover's algorithm"

        return analysis

    def analyze_post_quantum_security(
        self,
        crypto_system: str,
        key_size_bits: int,
    ) -> PostQuantumAnalysis:
        """
        Analyze if cryptosystem is secure against quantum attacks.

        Args:
            crypto_system: Type of crypto (RSA, AES, ECC, etc.)
            key_size_bits: Key size in bits

        Returns:
            Post-quantum security analysis
        """
        system_lower = crypto_system.lower()

        # RSA / Integer Factorization
        if "rsa" in system_lower or "factorization" in system_lower:
            return PostQuantumAnalysis(
                current_system=f"RSA-{key_size_bits}",
                quantum_vulnerable=True,
                time_to_break_classical=self._estimate_classical_break_time(key_size_bits, "rsa"),
                time_to_break_quantum="Polynomial time (practical with large QC)",
                recommended_alternative="CRYSTALS-Kyber (lattice-based KEM) or NTRU",
                security_level_bits_classical=key_size_bits // 2,  # Rough estimate
                security_level_bits_quantum=0,  # Completely broken
            )

        # ECC / Discrete Log
        elif "ecc" in system_lower or "elliptic" in system_lower or "ecdsa" in system_lower:
            return PostQuantumAnalysis(
                current_system=f"ECC-{key_size_bits}",
                quantum_vulnerable=True,
                time_to_break_classical=self._estimate_classical_break_time(key_size_bits, "ecc"),
                time_to_break_quantum="Polynomial time (Shor's algorithm applies)",
                recommended_alternative="CRYSTALS-Dilithium (lattice-based signatures)",
                security_level_bits_classical=key_size_bits,
                security_level_bits_quantum=0,  # Broken by Shor's
            )

        # AES / Symmetric
        elif "aes" in system_lower or "symmetric" in system_lower:
            effective_bits = key_size_bits / 2  # Grover's halves security

            return PostQuantumAnalysis(
                current_system=f"AES-{key_size_bits}",
                quantum_vulnerable=effective_bits < 128,
                time_to_break_classical=f"2^{key_size_bits} operations (infeasible)",
                time_to_break_quantum=f"2^{effective_bits:.0f} operations (Grover's)",
                recommended_alternative=f"AES-{max(256, key_size_bits * 2)}" if effective_bits < 128 else "Current size sufficient",
                security_level_bits_classical=key_size_bits,
                security_level_bits_quantum=int(effective_bits),
            )

        # SHA / Hash functions
        elif "sha" in system_lower or "hash" in system_lower:
            # Grover's provides √N speedup for preimage attacks
            # Collision: classical O(2^(n/2)), quantum O(2^(n/3))
            collision_bits_classical = key_size_bits / 2
            collision_bits_quantum = key_size_bits / 3

            return PostQuantumAnalysis(
                current_system=f"SHA-{key_size_bits}",
                quantum_vulnerable=collision_bits_quantum < 128,
                time_to_break_classical=f"2^{collision_bits_classical:.0f} for collision",
                time_to_break_quantum=f"2^{collision_bits_quantum:.0f} for collision (BHT algorithm)",
                recommended_alternative=f"SHA-{max(384, int(key_size_bits * 1.5))}" if collision_bits_quantum < 128 else "Current size sufficient",
                security_level_bits_classical=int(collision_bits_classical),
                security_level_bits_quantum=int(collision_bits_quantum),
            )

        else:
            # Unknown system
            return PostQuantumAnalysis(
                current_system=crypto_system,
                quantum_vulnerable=True,  # Conservative assumption
                time_to_break_classical="Unknown",
                time_to_break_quantum="Unknown - assume vulnerable",
                recommended_alternative="Consult post-quantum cryptography standards (NIST PQC)",
                security_level_bits_classical=0,
                security_level_bits_quantum=0,
            )

    def recommend_post_quantum_migration(
        self,
        current_systems: List[str],
    ) -> Dict[str, Any]:
        """
        Recommend migration path to post-quantum cryptography.

        Args:
            current_systems: List of current cryptographic systems in use

        Returns:
            Migration recommendations with timeline
        """
        recommendations = {
            "immediate_action": [],
            "near_term": [],
            "long_term": [],
            "monitoring": [],
        }

        for system in current_systems:
            if "rsa" in system.lower() or "ecc" in system.lower():
                recommendations["immediate_action"].append({
                    "system": system,
                    "action": "Begin migration planning",
                    "reason": "Vulnerable to Shor's algorithm",
                    "alternatives": ["CRYSTALS-Kyber", "NTRU", "CRYSTALS-Dilithium"],
                })

            elif "aes-128" in system.lower() or "sha-256" in system.lower():
                recommendations["near_term"].append({
                    "system": system,
                    "action": "Upgrade key/hash size",
                    "reason": "Grover's algorithm reduces effective security",
                    "alternatives": ["AES-256", "SHA-384"],
                })

            elif "aes-256" in system.lower() or "sha-384" in system.lower():
                recommendations["monitoring"].append({
                    "system": system,
                    "action": "Monitor quantum computing progress",
                    "reason": "Currently quantum-resistant but may need future upgrades",
                })

        return recommendations

    def estimate_quantum_threat_timeline(self) -> Dict[str, str]:
        """
        Estimate timeline for quantum computing threats.

        Based on current progress in quantum computing hardware.
        """
        return {
            "2025": "Small-scale demonstrations (~100 qubits, no error correction)",
            "2027-2030": "Early fault-tolerant systems (~1000 logical qubits)",
            "2030-2035": "Medium-scale quantum computers (potential RSA-2048 breaking)",
            "2035-2040": "Large-scale quantum computers (most classical crypto vulnerable)",
            "recommendation": "Begin post-quantum migration NOW - standards are ready (NIST PQC)",
            "note": "Timeline is uncertain - could be faster with breakthroughs"
        }

    def _estimate_classical_break_time(self, key_bits: int, system: str) -> str:
        """Estimate time to break with classical computers."""
        if system == "rsa":
            # Very rough GNFS estimate
            if key_bits >= 2048:
                return "Centuries (with current hardware)"
            elif key_bits >= 1024:
                return "Years to decades"
            else:
                return "Days to months"
        elif system == "ecc":
            # Pollard's rho
            if key_bits >= 256:
                return "Infeasible (2^128+ operations)"
            elif key_bits >= 192:
                return "Centuries"
            else:
                return "Years"
        else:
            return "Unknown"

    def _format_time(self, seconds: float) -> str:
        """Format time in human-readable form."""
        if seconds < 1:
            return f"{seconds*1000:.2f} milliseconds"
        elif seconds < 60:
            return f"{seconds:.2f} seconds"
        elif seconds < 3600:
            return f"{seconds/60:.2f} minutes"
        elif seconds < 86400:
            return f"{seconds/3600:.2f} hours"
        elif seconds < 31536000:
            return f"{seconds/86400:.2f} days"
        else:
            return f"{seconds/31536000:.2f} years"
