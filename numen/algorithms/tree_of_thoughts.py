"""
Tree of Thoughts (ToT): Deliberate exploration of reasoning trees.

Key paper: "Tree of Thoughts: Deliberate Problem Solving with Large Language Models"
(Yao et al., 2023)

ToT explicitly models the reasoning process as a tree where each node is a
partial solution state. Better than MCTS for math because it:
1. Evaluates partial solutions (not just terminal states)
2. Backtracks intelligently
3. Uses domain knowledge to prune branches
"""

from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
import math


class ThoughtState(Enum):
    """State of a thought/reasoning step."""

    PROMISING = "promising"  # Likely to lead to solution
    STUCK = "stuck"  # Dead end, should backtrack
    SOLVED = "solved"  # Reached valid solution
    UNKNOWN = "unknown"  # Not yet evaluated


@dataclass
class Thought:
    """
    A thought (partial reasoning step) in the tree.

    Unlike MCTS nodes, thoughts represent reasoning steps explicitly.
    """

    id: str
    parent: Optional['Thought']
    children: List['Thought'] = field(default_factory=list)

    # Reasoning content
    description: str = ""
    mathematical_state: str = ""  # Current equation/expression
    reasoning_so_far: List[str] = field(default_factory=list)

    # Evaluation
    state: ThoughtState = ThoughtState.UNKNOWN
    value: float = 0.0  # Estimated value of this path
    visits: int = 0

    # Verification
    verified: bool = False
    is_solution: bool = False

    def __hash__(self):
        return hash(self.id)


class TreeOfThoughts:
    """
    Tree of Thoughts for mathematical reasoning.

    Explores reasoning trees by:
    1. Generating multiple next-step candidates
    2. Evaluating each candidate (promising/stuck/solved)
    3. Selecting most promising path
    4. Backtracking if stuck
    """

    def __init__(
        self,
        breadth: int = 5,  # Number of alternatives per step
        max_depth: int = 20,  # Maximum reasoning depth
        evaluation_fn: Optional[Callable] = None,
    ):
        self.breadth = breadth
        self.max_depth = max_depth
        self.evaluation_fn = evaluation_fn or self._default_evaluation

    def solve(
        self,
        problem: str,
        generator_fn: Callable,  # Generates next thought candidates
        verifier_fn: Callable,  # Verifies if thought is valid
    ) -> tuple[Optional[str], List[Thought]]:
        """
        Solve problem using Tree of Thoughts.

        Args:
            problem: Mathematical problem
            generator_fn: Function that generates next reasoning steps
            verifier_fn: Function that verifies reasoning validity

        Returns:
            Tuple of (solution, reasoning_path)
        """
        # Initialize root thought
        root = Thought(
            id="root",
            parent=None,
            description="Initial problem",
            mathematical_state=problem,
            reasoning_so_far=[],
        )

        # Run breadth-first search with evaluation
        solution_path = self._bfs_with_evaluation(
            root,
            generator_fn,
            verifier_fn,
        )

        if solution_path:
            final_thought = solution_path[-1]
            return final_thought.mathematical_state, solution_path
        else:
            return None, []

    def _bfs_with_evaluation(
        self,
        root: Thought,
        generator_fn: Callable,
        verifier_fn: Callable,
    ) -> Optional[List[Thought]]:
        """
        Breadth-first search with thought evaluation.

        At each level:
        1. Generate k candidate next thoughts
        2. Evaluate each candidate
        3. Keep top-b most promising
        4. Expand those
        """
        from queue import PriorityQueue

        # Priority queue of (negative_value, thought)
        # Using negative value so highest value has highest priority
        frontier = PriorityQueue()
        frontier.put((0, root))

        visited = set()
        max_iterations = 1000
        iteration = 0

        while not frontier.empty() and iteration < max_iterations:
            iteration += 1

            # Get most promising thought
            _, current = frontier.get()

            if current.id in visited:
                continue

            visited.add(current.id)

            # Check if solved
            if current.is_solution:
                # Reconstruct path
                return self._reconstruct_path(current)

            # Check depth limit
            depth = len(current.reasoning_so_far)
            if depth >= self.max_depth:
                continue

            # Generate candidate next thoughts
            candidates = self._generate_next_thoughts(
                current,
                generator_fn,
                verifier_fn,
            )

            # Evaluate candidates
            evaluated_candidates = []
            for candidate in candidates:
                value = self.evaluation_fn(candidate, current)
                candidate.value = value
                evaluated_candidates.append((value, candidate))

            # Keep top breadth candidates
            evaluated_candidates.sort(reverse=True, key=lambda x: x[0])
            top_candidates = evaluated_candidates[:self.breadth]

            # Add to frontier
            for value, candidate in top_candidates:
                if candidate.state != ThoughtState.STUCK:
                    frontier.put((-value, candidate))  # Negative for max-heap

        # No solution found
        return None

    def _generate_next_thoughts(
        self,
        current: Thought,
        generator_fn: Callable,
        verifier_fn: Callable,
    ) -> List[Thought]:
        """
        Generate multiple candidate next thoughts.

        Each thought represents a possible next reasoning step.
        """
        # Generate k candidate next steps
        candidates_data = generator_fn(
            current.mathematical_state,
            num_candidates=self.breadth,
        )

        thoughts = []
        for i, candidate_data in enumerate(candidates_data):
            thought = Thought(
                id=f"{current.id}_child_{i}",
                parent=current,
                description=candidate_data.get("description", ""),
                mathematical_state=candidate_data.get("state", ""),
                reasoning_so_far=current.reasoning_so_far + [candidate_data.get("description", "")],
            )

            # Verify if this step is valid
            verification = verifier_fn(thought.mathematical_state)
            thought.verified = verification.get("valid", False)

            if verification.get("is_solution", False):
                thought.is_solution = True
                thought.state = ThoughtState.SOLVED

            current.children.append(thought)
            thoughts.append(thought)

        return thoughts

    def _default_evaluation(self, thought: Thought, parent: Thought) -> float:
        """
        Evaluate how promising a thought is.

        Returns value in [0, 1] where higher = more promising.
        """
        value = 0.5  # Neutral starting point

        # Bonus if verified
        if thought.verified:
            value += 0.3

        # Bonus if solution
        if thought.is_solution:
            value = 1.0
            return value

        # Penalty if expression is getting very complex
        if len(thought.mathematical_state) > len(parent.mathematical_state) * 2:
            value -= 0.2

        # Bonus if expression is simplifying
        if len(thought.mathematical_state) < len(parent.mathematical_state):
            value += 0.1

        # Penalty for deep paths (prefer shorter solutions)
        depth_penalty = len(thought.reasoning_so_far) * 0.02
        value -= depth_penalty

        return max(0.0, min(1.0, value))

    def _reconstruct_path(self, thought: Thought) -> List[Thought]:
        """Reconstruct path from root to this thought."""
        path = []
        current = thought

        while current is not None:
            path.append(current)
            current = current.parent

        return list(reversed(path))

    def format_reasoning_tree(
        self,
        thoughts: List[Thought],
        show_alternatives: bool = False,
    ) -> str:
        """
        Format reasoning tree for human reading.

        Args:
            thoughts: Path through tree (or full tree if show_alternatives)
            show_alternatives: Show alternative thoughts that weren't chosen
        """
        output = "## Tree of Thoughts Reasoning\n\n"

        for i, thought in enumerate(thoughts):
            if thought.parent is None:
                continue  # Skip root

            # Indentation based on depth
            indent = "  " * (i - 1)

            # Status icon
            if thought.state == ThoughtState.SOLVED:
                icon = "✅"
            elif thought.verified:
                icon = "✓"
            else:
                icon = "→"

            output += f"{indent}{icon} **Step {i}**: {thought.description}\n"
            output += f"{indent}   State: `{thought.mathematical_state}`\n"
            output += f"{indent}   Value: {thought.value:.2f}\n"

            # Show alternatives if requested
            if show_alternatives and thought.parent:
                alternatives = [
                    c for c in thought.parent.children
                    if c != thought
                ]
                if alternatives:
                    output += f"{indent}   Alternatives considered:\n"
                    for alt in alternatives[:3]:  # Show top 3
                        output += f"{indent}     - {alt.description} (value: {alt.value:.2f})\n"

            output += "\n"

        return output


class DFSTreeOfThoughts(TreeOfThoughts):
    """
    Depth-First Search variant of ToT.

    Better for problems where you need to explore full solutions before
    deciding if a path is good.
    """

    def solve(
        self,
        problem: str,
        generator_fn: Callable,
        verifier_fn: Callable,
    ) -> tuple[Optional[str], List[Thought]]:
        """Solve using depth-first search."""
        root = Thought(
            id="root",
            parent=None,
            description="Initial problem",
            mathematical_state=problem,
        )

        solution_path = self._dfs(root, generator_fn, verifier_fn, depth=0)

        if solution_path:
            return solution_path[-1].mathematical_state, solution_path
        else:
            return None, []

    def _dfs(
        self,
        thought: Thought,
        generator_fn: Callable,
        verifier_fn: Callable,
        depth: int,
    ) -> Optional[List[Thought]]:
        """Depth-first search through thought tree."""

        # Check if solved
        if thought.is_solution:
            return [thought]

        # Check depth limit
        if depth >= self.max_depth:
            return None

        # Generate and evaluate candidates
        candidates = self._generate_next_thoughts(
            thought,
            generator_fn,
            verifier_fn,
        )

        # Sort by evaluation value
        candidates.sort(key=lambda t: t.value, reverse=True)

        # Try each candidate (best first)
        for candidate in candidates:
            if candidate.state == ThoughtState.STUCK:
                continue

            # Recursive DFS
            solution_path = self._dfs(
                candidate,
                generator_fn,
                verifier_fn,
                depth + 1,
            )

            if solution_path:
                return [thought] + solution_path

        # No solution found in this branch
        return None
