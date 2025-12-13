"""
Format complex reasoning chains for human understanding.
Makes MCTS and multi-strategy solving transparent.
"""

from typing import List, Dict, Any
from dataclasses import dataclass


@dataclass
class ReasoningStep:
    """Single step in reasoning chain."""

    step_number: int
    strategy: str
    action: str
    result: str
    verified: bool
    confidence: float


class ReasoningFormatter:
    """
    Format reasoning chains for clear human understanding.

    Transforms technical MCTS/solver output into readable narrative.
    """

    def __init__(self):
        self.step_icons = {
            "attempt": "🔍",
            "success": "✅",
            "failed": "❌",
            "verification": "🔬",
            "fallback": "↩️",
            "mcts_explore": "🌳",
        }

    def format_reasoning_chain(
        self,
        steps: List[str],
        final_verified: bool = False,
    ) -> str:
        """
        Format list of reasoning steps into clear narrative.

        Args:
            steps: Raw reasoning steps from solver
            final_verified: Whether final solution was verified

        Returns:
            Formatted HTML/Markdown string
        """
        if not steps:
            return "No reasoning steps recorded."

        formatted = "## 🧠 Reasoning Chain\n\n"

        # Detect strategy changes
        current_strategy = None

        for i, step in enumerate(steps, 1):
            # Parse step content
            step_lower = step.lower()

            # Detect step type
            if "attempting" in step_lower or "trying" in step_lower:
                icon = self.step_icons["attempt"]
                if "algebraic" in step_lower:
                    current_strategy = "Algebraic"
                elif "geometric" in step_lower:
                    current_strategy = "Geometric"
                elif "numerical" in step_lower:
                    current_strategy = "Numerical"
                elif "mcts" in step_lower:
                    current_strategy = "MCTS Search"
                    icon = self.step_icons["mcts_explore"]
            elif "verified" in step_lower:
                icon = self.step_icons["verification"]
            elif "failed" in step_lower:
                icon = self.step_icons["failed"]
            elif "success" in step_lower:
                icon = self.step_icons["success"]
            else:
                icon = "→"

            # Format step
            formatted += f"{icon} **Step {i}**: {step}\n"

            # Add strategy context
            if current_strategy and "strategy" in step_lower:
                formatted += f"   *Using {current_strategy} approach*\n"

            formatted += "\n"

        # Add final status
        if final_verified:
            formatted += "---\n\n"
            formatted += "✅ **VERIFIED**: Solution passed symbolic verification\n"
            formatted += "   *You can trust this answer with 100% confidence*\n"
        else:
            formatted += "---\n\n"
            formatted += "⚠️ **NOT VERIFIED**: Solution could not be symbolically verified\n"
            formatted += "   *Take this answer as a suggestion, not a guarantee*\n"

        return formatted

    def format_multi_strategy_attempt(
        self,
        attempts: List[Dict[str, Any]],
    ) -> str:
        """
        Format multiple strategy attempts into comparison table.

        Shows which strategies were tried and why they succeeded/failed.
        """
        formatted = "## 🎯 Strategy Attempts\n\n"
        formatted += "| # | Strategy | Result | Confidence | Notes |\n"
        formatted += "|---|----------|--------|------------|-------|\n"

        for i, attempt in enumerate(attempts, 1):
            strategy = attempt.get("strategy", "Unknown")
            result = "✅ Success" if attempt.get("verified", False) else "❌ Failed"
            confidence = f"{attempt.get('confidence', 0):.0%}"
            notes = attempt.get("notes", "")

            formatted += f"| {i} | {strategy} | {result} | {confidence} | {notes} |\n"

        formatted += "\n"

        # Add interpretation
        successful = [a for a in attempts if a.get("verified", False)]
        if successful:
            best = max(successful, key=lambda a: a.get("confidence", 0))
            formatted += f"**Best Strategy**: {best.get('strategy')} "
            formatted += f"(Confidence: {best.get('confidence', 0):.0%})\n"
        else:
            formatted += "**Outcome**: No strategy succeeded. Problem may be:\n"
            formatted += "- Too complex for current methods\n"
            formatted += "- Outside domain of trained knowledge\n"
            formatted += "- Requires human creativity\n"

        return formatted

    def format_verification_details(
        self,
        verification_result: Any,
    ) -> str:
        """
        Format symbolic verification details for transparency.

        Shows exactly what was verified and how.
        """
        formatted = "## 🔬 Verification Details\n\n"

        status = getattr(verification_result, 'status', None)
        confidence = getattr(verification_result, 'confidence', 0)
        explanation = getattr(verification_result, 'explanation', 'No explanation')
        proof = getattr(verification_result, 'symbolic_proof', None)

        # Status badge
        if status and hasattr(status, 'value'):
            status_str = status.value.upper()
            if status_str == "VERIFIED":
                formatted += "**Status**: ✅ VERIFIED\n\n"
            elif status_str == "FAILED":
                formatted += "**Status**: ❌ FAILED\n\n"
            else:
                formatted += f"**Status**: ⚠️ {status_str}\n\n"

        # Confidence
        formatted += f"**Confidence**: {confidence:.0%}\n\n"

        # Explanation
        formatted += f"**Explanation**: {explanation}\n\n"

        # Symbolic proof (if available)
        if proof:
            formatted += "**Symbolic Proof**:\n```\n"
            formatted += str(proof)
            formatted += "\n```\n\n"

        # What this means
        formatted += "### What This Means\n\n"
        if confidence >= 0.95:
            formatted += "- The solution is **mathematically proven correct**\n"
            formatted += "- SymPy verified all symbolic manipulations\n"
            formatted += "- You can use this answer with complete confidence\n"
        elif confidence >= 0.7:
            formatted += "- The solution appears correct but has minor uncertainties\n"
            formatted += "- Consider verifying with alternative method\n"
        else:
            formatted += "- The solution could not be verified\n"
            formatted += "- Treat as an educated guess, not a proof\n"
            formatted += "- Manual verification recommended\n"

        return formatted

    def format_mcts_search_tree(
        self,
        iterations: int,
        nodes_explored: int,
        best_path: List[str],
    ) -> str:
        """
        Format MCTS search statistics in human terms.
        """
        formatted = "## 🌳 Search Statistics\n\n"
        formatted += f"- **Iterations**: {iterations}\n"
        formatted += f"- **Nodes Explored**: {nodes_explored}\n"
        formatted += f"- **Best Path Length**: {len(best_path)} steps\n\n"

        if best_path:
            formatted += "**Solution Path**:\n"
            for i, node in enumerate(best_path, 1):
                formatted += f"{i}. {node}\n"

        return formatted
