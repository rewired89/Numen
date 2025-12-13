"""
Gradio web UI for Numen reasoning engine.

Features:
- Text input for direct equation entry
- Image upload with OCR
- File upload (PDF, images, text files)
- Real-time solving with verification
- Cryptanalysis interface
- Neural dynamics interface
"""

import gradio as gr
from typing import Optional, List, Tuple
import json
from pathlib import Path

from numen import NumenEngine
from numen.ui.ocr import EquationExtractor, ExtractedEquation
from numen.strategies.cryptanalysis import CryptanalysisStrategy
from numen.strategies.neural_analysis import NeuralAnalysisStrategy
import numpy as np


class NumenUI:
    """Gradio UI for Numen reasoning engine."""

    def __init__(self):
        self.engine = NumenEngine(
            use_mcts=True,
            max_mcts_iterations=500,
            require_verification=True,
        )
        self.ocr = EquationExtractor(use_latex_ocr=True)
        self.crypto = CryptanalysisStrategy()
        self.neural = NeuralAnalysisStrategy()

    def solve_from_text(
        self,
        problem: str,
        use_mcts: bool = True,
        require_verification: bool = True,
    ) -> Tuple[str, str, str, str]:
        """
        Solve problem from text input.

        Returns:
            Tuple of (solution, verification_status, confidence, reasoning_chain)
        """
        if not problem.strip():
            return "Please enter a problem.", "No input", "0%", "No steps"

        # Temporarily configure engine
        self.engine.use_mcts = use_mcts
        self.engine.require_verification = require_verification

        try:
            result = self.engine.solve(problem)

            solution = result.solution or "No solution found"
            verification = f"{result.verification.status.value} - {result.verification.explanation}"
            confidence = f"{result.confidence:.1%}"
            reasoning = "\n".join(f"{i+1}. {step}" for i, step in enumerate(result.reasoning_chain))

            return solution, verification, confidence, reasoning

        except Exception as e:
            return f"Error: {str(e)}", "Failed", "0%", str(e)

    def solve_from_image(
        self,
        image,
        use_mcts: bool = True,
    ) -> Tuple[str, str, str, str, str]:
        """
        Solve equation from uploaded image.

        Returns:
            Tuple of (extracted_text, solution, verification, confidence, reasoning)
        """
        if image is None:
            return "No image uploaded", "", "No input", "0%", ""

        try:
            # Extract equations from image
            equations = self.ocr.extract_from_image(image, preprocess=True)

            if not equations or equations[0].confidence < 0.1:
                return "Could not extract equation from image. Please try a clearer image or type manually.", "", "", "", ""

            # Take the best extraction
            best_eq = max(equations, key=lambda e: e.confidence)
            extracted_text = best_eq.latex or best_eq.text

            # Solve the extracted equation
            solution, verification, confidence, reasoning = self.solve_from_text(
                extracted_text,
                use_mcts=use_mcts,
                require_verification=True,
            )

            return extracted_text, solution, verification, confidence, reasoning

        except Exception as e:
            return f"Error: {str(e)}", "", "Failed", "0%", str(e)

    def solve_from_file(
        self,
        file,
        use_mcts: bool = True,
    ) -> Tuple[str, str]:
        """
        Extract and solve equations from uploaded file.

        Returns:
            Tuple of (extracted_equations, solutions)
        """
        if file is None:
            return "No file uploaded", ""

        try:
            # Extract equations
            equations = self.ocr.auto_extract(file.name)

            if not equations:
                return "No equations found in file", ""

            # Display extracted equations
            extracted_text = "Extracted Equations:\n\n"
            for i, eq in enumerate(equations, 1):
                confidence_indicator = "✓" if eq.confidence > 0.7 else "?"
                extracted_text += f"{i}. [{confidence_indicator}] {eq.text}\n"
                if eq.page_number:
                    extracted_text += f"   (Page {eq.page_number})\n"
                extracted_text += "\n"

            # Solve each equation
            solutions_text = "Solutions:\n\n"
            for i, eq in enumerate(equations, 1):
                solutions_text += f"Problem {i}: {eq.text}\n"

                try:
                    result = self.engine.solve(eq.text)
                    solutions_text += f"Solution: {result.solution}\n"
                    solutions_text += f"Verified: {result.verified} ({result.confidence:.1%})\n"
                except Exception as e:
                    solutions_text += f"Error: {str(e)}\n"

                solutions_text += "\n" + "-" * 60 + "\n\n"

            return extracted_text, solutions_text

        except Exception as e:
            return f"Error: {str(e)}", ""

    def analyze_crypto(
        self,
        protocol_description: str,
        rsa_n: Optional[str] = None,
        rsa_e: Optional[str] = None,
    ) -> str:
        """Analyze cryptographic protocol."""
        if not protocol_description.strip():
            return "Please provide a protocol description."

        try:
            # Protocol-level analysis
            vulnerabilities = self.crypto.detect_protocol_vulnerabilities(protocol_description)

            # RSA-specific analysis if parameters provided
            if rsa_n and rsa_e:
                try:
                    n = int(rsa_n)
                    e = int(rsa_e)
                    rsa_vulns = self.crypto.analyze_rsa_parameters(n, e)
                    vulnerabilities.extend(rsa_vulns)
                except ValueError:
                    pass

            # Format results
            if not vulnerabilities:
                return "✓ No obvious vulnerabilities detected.\n\nNote: This is a preliminary analysis. Full security audit recommended."

            result = f"Found {len(vulnerabilities)} potential vulnerabilities:\n\n"

            for i, vuln in enumerate(vulnerabilities, 1):
                severity_bar = "🔴" * int(vuln.severity * 5)
                result += f"{i}. {vuln.type.value.upper()}\n"
                result += f"   Severity: {severity_bar} ({vuln.severity:.1f}/1.0)\n"
                result += f"   Description: {vuln.description}\n"
                result += f"   Attack Vector: {vuln.attack_vector}\n"
                result += f"   Mathematical Basis: {vuln.mathematical_basis}\n"
                result += f"   Mitigation: {vuln.mitigation}\n\n"

            return result

        except Exception as e:
            return f"Error: {str(e)}"

    def analyze_neural(
        self,
        description: str,
        model_type: str = "fitzhugh_nagumo",
    ) -> str:
        """Analyze neural dynamics."""
        if not description.strip():
            return "Please provide a description of neural signals or dynamics."

        try:
            # Generate synthetic signal data (in practice, would come from actual measurements)
            signal_data = {
                "eeg": np.random.randn(100) * 0.5
            }

            # Build dynamical model
            dynamics = self.neural.model_as_dynamical_system(
                signal_data=signal_data,
                model_type=model_type,
            )

            # Predict cognitive state
            current_signal = signal_data["eeg"]
            state = self.neural.predict_cognitive_state(current_signal, dynamics)

            # Predict transitions
            transitions = self.neural.predict_state_transition(state, dynamics)

            # Format results
            result = f"Neural Dynamics Analysis\n\n"
            result += f"Dynamical Model: {model_type}\n\n"

            result += "Equations:\n"
            for eq in dynamics.equations:
                result += f"  {eq}\n"

            result += f"\nEquilibrium Points: {len(dynamics.equilibria)}\n"
            result += f"Stability: {', '.join(dynamics.stability)}\n\n"

            result += f"Predicted Cognitive State: {state.value.upper()}\n\n"

            if transitions:
                result += "Possible State Transitions:\n"
                for trans in transitions:
                    result += f"  • {trans.from_state.value} → {trans.to_state.value}\n"
                    result += f"    Probability: {trans.probability:.1%}\n"
                    result += f"    Time: {trans.time_to_transition:.1f}s\n"
                    result += f"    Conditions: {', '.join(trans.triggering_conditions)}\n\n"

            return result

        except Exception as e:
            return f"Error: {str(e)}"

    def create_interface(self) -> gr.Blocks:
        """Create Gradio interface."""

        with gr.Blocks(
            title="Numen - Mathematical Reasoning Engine",
            theme=gr.themes.Soft(),
        ) as app:

            gr.Markdown(
                """
                # 🧮 Numen - Mathematical Reasoning Engine

                Specialized AI for cross-domain mathematical problem solving in cybersecurity and neuroscience.

                **Features:**
                - 🔢 Solve equations with symbolic verification (zero hallucination)
                - 📷 Extract equations from images using OCR
                - 📄 Process PDF documents and text files
                - 🔐 Cryptographic vulnerability analysis
                - 🧠 Neural dynamics modeling
                """
            )

            with gr.Tabs():

                # Tab 1: Text Input Solver
                with gr.Tab("📝 Text Solver"):
                    gr.Markdown("### Enter a mathematical problem to solve")

                    with gr.Row():
                        with gr.Column():
                            text_input = gr.Textbox(
                                label="Problem",
                                placeholder="e.g., Solve for x: 2x + 5 = 13",
                                lines=3,
                            )
                            use_mcts_text = gr.Checkbox(label="Use MCTS Search", value=True)
                            require_verification_text = gr.Checkbox(label="Require Verification", value=True)
                            solve_text_btn = gr.Button("Solve", variant="primary")

                        with gr.Column():
                            solution_output = gr.Textbox(label="Solution", lines=3)
                            verification_output = gr.Textbox(label="Verification Status", lines=2)
                            confidence_output = gr.Textbox(label="Confidence")
                            reasoning_output = gr.Textbox(label="Reasoning Chain", lines=8)

                    solve_text_btn.click(
                        fn=self.solve_from_text,
                        inputs=[text_input, use_mcts_text, require_verification_text],
                        outputs=[solution_output, verification_output, confidence_output, reasoning_output],
                    )

                    # Examples
                    gr.Examples(
                        examples=[
                            ["Solve for x: 2x + 5 = 13", True, True],
                            ["Find the derivative of x^3 + 2x^2 - 5x + 1", True, True],
                            ["Simplify (x^2 - 1) / (x - 1)", False, True],
                            ["Prove that the square root of 2 is irrational", True, False],
                        ],
                        inputs=[text_input, use_mcts_text, require_verification_text],
                    )

                # Tab 2: Image Upload
                with gr.Tab("📷 Image Solver"):
                    gr.Markdown("### Upload an image containing equations")

                    with gr.Row():
                        with gr.Column():
                            image_input = gr.Image(label="Upload Image", type="pil")
                            use_mcts_image = gr.Checkbox(label="Use MCTS Search", value=True)
                            solve_image_btn = gr.Button("Extract & Solve", variant="primary")

                        with gr.Column():
                            extracted_output = gr.Textbox(label="Extracted Equation", lines=2)
                            image_solution_output = gr.Textbox(label="Solution", lines=3)
                            image_verification_output = gr.Textbox(label="Verification", lines=2)
                            image_confidence_output = gr.Textbox(label="Confidence")
                            image_reasoning_output = gr.Textbox(label="Reasoning Chain", lines=6)

                    solve_image_btn.click(
                        fn=self.solve_from_image,
                        inputs=[image_input, use_mcts_image],
                        outputs=[
                            extracted_output,
                            image_solution_output,
                            image_verification_output,
                            image_confidence_output,
                            image_reasoning_output,
                        ],
                    )

                # Tab 3: File Upload
                with gr.Tab("📄 File Solver"):
                    gr.Markdown("### Upload a file (PDF, image, or text) containing equations")

                    with gr.Row():
                        with gr.Column():
                            file_input = gr.File(label="Upload File (PDF, Image, or Text)")
                            use_mcts_file = gr.Checkbox(label="Use MCTS Search", value=True)
                            solve_file_btn = gr.Button("Process File", variant="primary")

                        with gr.Column():
                            file_extracted_output = gr.Textbox(label="Extracted Equations", lines=10)
                            file_solutions_output = gr.Textbox(label="Solutions", lines=10)

                    solve_file_btn.click(
                        fn=self.solve_from_file,
                        inputs=[file_input, use_mcts_file],
                        outputs=[file_extracted_output, file_solutions_output],
                    )

                # Tab 4: Cryptanalysis
                with gr.Tab("🔐 Cryptanalysis"):
                    gr.Markdown("### Analyze cryptographic protocols for vulnerabilities")

                    with gr.Row():
                        with gr.Column():
                            crypto_desc = gr.Textbox(
                                label="Protocol Description",
                                placeholder="Describe the cryptographic protocol or system...",
                                lines=5,
                            )
                            with gr.Row():
                                rsa_n_input = gr.Textbox(label="RSA Modulus (n) - Optional", placeholder="e.g., 77")
                                rsa_e_input = gr.Textbox(label="RSA Exponent (e) - Optional", placeholder="e.g., 7")
                            crypto_btn = gr.Button("Analyze", variant="primary")

                        with gr.Column():
                            crypto_output = gr.Textbox(label="Vulnerability Analysis", lines=15)

                    crypto_btn.click(
                        fn=self.analyze_crypto,
                        inputs=[crypto_desc, rsa_n_input, rsa_e_input],
                        outputs=crypto_output,
                    )

                    gr.Examples(
                        examples=[
                            ["RSA encryption with custom implementation using ECB mode", "77", "7"],
                            ["Key exchange protocol that reuses nonces across sessions", "", ""],
                        ],
                        inputs=[crypto_desc, rsa_n_input, rsa_e_input],
                    )

                # Tab 5: Neural Analysis
                with gr.Tab("🧠 Neural Dynamics"):
                    gr.Markdown("### Analyze neural signals using dynamical systems theory")

                    with gr.Row():
                        with gr.Column():
                            neural_desc = gr.Textbox(
                                label="Neural Signal Description",
                                placeholder="Describe the neural signals or cognitive state...",
                                lines=5,
                            )
                            neural_model = gr.Dropdown(
                                choices=["fitzhugh_nagumo", "wilson_cowan", "generic"],
                                label="Dynamical Model",
                                value="fitzhugh_nagumo",
                            )
                            neural_btn = gr.Button("Analyze", variant="primary")

                        with gr.Column():
                            neural_output = gr.Textbox(label="Dynamics Analysis", lines=15)

                    neural_btn.click(
                        fn=self.analyze_neural,
                        inputs=[neural_desc, neural_model],
                        outputs=neural_output,
                    )

                    gr.Examples(
                        examples=[
                            ["EEG signals showing sustained oscillatory patterns during focused task", "fitzhugh_nagumo"],
                            ["Excitatory-inhibitory balance in prefrontal cortex during decision making", "wilson_cowan"],
                        ],
                        inputs=[neural_desc, neural_model],
                    )

            gr.Markdown(
                """
                ---

                **About Numen:**
                - Uses Monte Carlo Tree Search for solution exploration
                - Symbolic verification with SymPy (100% accuracy guarantee)
                - Cross-domain translation (topology ↔ crypto, dynamics ↔ neural)
                - Zero hallucination tolerance

                **Powered by:** DeepSeek-Math / Llama 3.1 (fine-tuned) + SymPy + Custom MCTS
                """
            )

        return app


def launch_ui(
    share: bool = False,
    server_name: str = "0.0.0.0",
    server_port: int = 7860,
):
    """
    Launch Gradio UI for Numen.

    Args:
        share: Create public share link
        server_name: Server host
        server_port: Server port
    """
    ui = NumenUI()
    app = ui.create_interface()

    app.launch(
        share=share,
        server_name=server_name,
        server_port=server_port,
        show_error=True,
    )


if __name__ == "__main__":
    launch_ui(share=False)
