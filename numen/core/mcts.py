"""
Monte Carlo Tree Search for mathematical problem solving.
Explores solution space with UCB1 selection and backpropagation.
"""

import math
import random
from typing import List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum


class NodeState(Enum):
    UNSOLVED = "unsolved"
    SOLVING = "solving"
    VERIFIED = "verified"
    FAILED = "failed"


@dataclass
class MCTSNode:
    """Represents a state in the solution search tree."""

    state: str  # Current problem state/representation
    parent: Optional['MCTSNode'] = None
    children: List['MCTSNode'] = field(default_factory=list)
    visits: int = 0
    value: float = 0.0
    status: NodeState = NodeState.UNSOLVED
    solution_path: List[str] = field(default_factory=list)
    strategy_used: Optional[str] = None

    def is_terminal(self) -> bool:
        """Check if node represents a solved state."""
        return self.status in [NodeState.VERIFIED, NodeState.FAILED]

    def is_fully_expanded(self) -> bool:
        """Check if all child strategies have been tried."""
        return len(self.children) >= self.max_children

    @property
    def max_children(self) -> int:
        """Maximum number of child strategies to explore."""
        return 5  # algebraic, geometric, computational, numerical, cross-domain

    def ucb1_score(self, exploration_weight: float = 1.414) -> float:
        """Upper Confidence Bound for Trees score."""
        if self.visits == 0:
            return float('inf')

        exploitation = self.value / self.visits
        exploration = exploration_weight * math.sqrt(
            math.log(self.parent.visits) / self.visits
        ) if self.parent else 0

        return exploitation + exploration


class MCTSSearchEngine:
    """
    Monte Carlo Tree Search engine for mathematical problem solving.
    Explores multiple solution strategies and selects the most promising path.
    """

    def __init__(
        self,
        max_iterations: int = 1000,
        exploration_weight: float = 1.414,
        max_depth: int = 20,
    ):
        self.max_iterations = max_iterations
        self.exploration_weight = exploration_weight
        self.max_depth = max_depth
        self.iteration_count = 0

    def search(
        self,
        problem: str,
        strategy_generator,
        verifier,
    ) -> Tuple[Optional[str], List[str]]:
        """
        Execute MCTS to find verified solution.

        Args:
            problem: Mathematical problem statement
            strategy_generator: Function that generates solution strategies
            verifier: Symbolic verifier to check solutions

        Returns:
            Tuple of (solution, reasoning_chain)
        """
        root = MCTSNode(state=problem)

        for _ in range(self.max_iterations):
            self.iteration_count += 1

            # Selection: traverse tree using UCB1
            node = self._select(root)

            # Expansion: add new strategy child
            if not node.is_terminal() and not node.is_fully_expanded():
                node = self._expand(node, strategy_generator)

            # Simulation: attempt to solve using selected strategy
            value, solution = self._simulate(node, strategy_generator, verifier)

            # Backpropagation: update tree values
            self._backpropagate(node, value)

            # Early termination if verified solution found
            if value == 1.0 and solution:
                return solution, node.solution_path

        # Return best solution found
        best_child = self._best_child(root, exploration_weight=0)
        if best_child and best_child.status == NodeState.VERIFIED:
            return best_child.state, best_child.solution_path

        return None, []

    def _select(self, node: MCTSNode) -> MCTSNode:
        """Select most promising node using UCB1."""
        current = node

        while not current.is_terminal() and current.is_fully_expanded():
            if not current.children:
                break
            current = max(current.children, key=lambda n: n.ucb1_score(self.exploration_weight))

        return current

    def _expand(self, node: MCTSNode, strategy_generator) -> MCTSNode:
        """Expand node by adding a new strategy child."""
        strategies = strategy_generator(node.state, len(node.children))

        if not strategies:
            return node

        strategy = strategies[0]
        child = MCTSNode(
            state=node.state,
            parent=node,
            strategy_used=strategy.name,
            solution_path=node.solution_path + [f"Trying {strategy.name}"]
        )
        node.children.append(child)

        return child

    def _simulate(
        self,
        node: MCTSNode,
        strategy_generator,
        verifier,
    ) -> Tuple[float, Optional[str]]:
        """
        Simulate solution attempt using node's strategy.

        Returns:
            Tuple of (value, solution) where value is 0.0 or 1.0
        """
        if node.status == NodeState.VERIFIED:
            return 1.0, node.state

        if node.status == NodeState.FAILED:
            return 0.0, None

        # Attempt solution with this strategy
        # This would call the actual solver in practice
        # For now, we return placeholder values

        return 0.5, None

    def _backpropagate(self, node: MCTSNode, value: float):
        """Backpropagate simulation result up the tree."""
        current = node

        while current is not None:
            current.visits += 1
            current.value += value
            current = current.parent

    def _best_child(
        self,
        node: MCTSNode,
        exploration_weight: float = 0
    ) -> Optional[MCTSNode]:
        """Select best child based on visit count or UCB1."""
        if not node.children:
            return None

        if exploration_weight == 0:
            # Exploitation only - select most visited
            return max(node.children, key=lambda n: n.visits)
        else:
            # UCB1 selection
            return max(node.children, key=lambda n: n.ucb1_score(exploration_weight))

    def get_principal_variation(self, root: MCTSNode) -> List[MCTSNode]:
        """Extract the most-visited path from root to leaf."""
        path = []
        current = root

        while current.children:
            current = self._best_child(current, exploration_weight=0)
            if current:
                path.append(current)
            else:
                break

        return path
