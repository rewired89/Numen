"""
API request/response schemas using Pydantic.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class SolveRequest(BaseModel):
    """Request to solve a mathematical problem."""

    problem: str = Field(..., description="Mathematical problem statement")
    use_mcts: bool = Field(default=True, description="Enable MCTS search")
    max_iterations: int = Field(default=1000, description="Maximum MCTS iterations", ge=1, le=10000)
    require_verification: bool = Field(default=True, description="Only return verified solutions")
    timeout: Optional[float] = Field(default=None, description="Timeout in seconds", ge=1)
    expected_answer: Optional[str] = Field(default=None, description="Expected answer for verification")


class SolveResponse(BaseModel):
    """Response with solution and verification."""

    problem: str
    solution: Optional[str]
    verified: bool
    confidence: float
    verification_status: str
    verification_explanation: str
    reasoning_chain: List[str]
    strategies_attempted: List[str]
    computation_time_seconds: float
    symbolic_proof: Optional[str] = None


class ProveRequest(BaseModel):
    """Request to prove a mathematical statement."""

    statement: str = Field(..., description="Statement to prove")
    method: str = Field(default="auto", description="Proof method")


class ProveResponse(BaseModel):
    """Response with proof."""

    statement: str
    proof: Optional[str]
    verified: bool
    proof_method: str
    reasoning_chain: List[str]


class CryptoAnalysisRequest(BaseModel):
    """Request for cryptographic analysis."""

    protocol_description: str = Field(..., description="Description of cryptographic protocol")
    parameters: Optional[Dict[str, Any]] = Field(default=None, description="System parameters")


class CryptoAnalysisResponse(BaseModel):
    """Response with cryptographic analysis."""

    vulnerabilities: List[Dict[str, Any]]
    attack_vectors: List[Dict[str, Any]]
    security_level_bits: int
    recommendations: List[str]


class NeuralAnalysisRequest(BaseModel):
    """Request for neural signal analysis."""

    signal_description: str = Field(..., description="Description of neural signals")
    signal_data: Optional[Dict[str, List[float]]] = Field(default=None, description="Actual signal data")
    model_type: str = Field(default="fitzhugh_nagumo", description="Dynamical model type")


class NeuralAnalysisResponse(BaseModel):
    """Response with neural dynamics analysis."""

    predicted_state: str
    state_transitions: List[Dict[str, Any]]
    dynamical_model: Dict[str, Any]
    recommendations: List[str]


class HealthResponse(BaseModel):
    """API health check response."""

    status: str
    version: str
    capabilities: List[str]
