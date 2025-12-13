"""
Advanced reasoning algorithms for Numen.

This module contains state-of-the-art algorithms from LLM research
that dramatically improve mathematical reasoning accuracy.
"""

from numen.algorithms.self_consistency import SelfConsistencyReasoner
from numen.algorithms.process_reward_model import ProcessRewardModel, StepByStepGenerator
from numen.algorithms.tree_of_thoughts import TreeOfThoughts, DFSTreeOfThoughts

__all__ = [
    "SelfConsistencyReasoner",
    "ProcessRewardModel",
    "StepByStepGenerator",
    "TreeOfThoughts",
    "DFSTreeOfThoughts",
]
