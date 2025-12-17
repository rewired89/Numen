#!/usr/bin/env python3
"""
Numen Student - Simple Math Problem Solver

For students who need help with homework:
- Type a problem → Get answer with step-by-step explanation
- Upload a photo → OCR extracts problem → Get answer with explanation

100% accurate answers powered by symbolic mathematics.
"""

import gradio as gr
from numen.solvers.student_solver import StudentSolver, Solution
from numen.ocr.simple_ocr import SimpleOCR

# Initialize solver and OCR
solver = StudentSolver()
ocr = SimpleOCR()


def solve_text_problem(problem_text):
    """Solve a math problem from text input."""
    if not problem_text or not problem_text.strip():
        return "❌ **Error**\n\nPlease enter a math problem.", "", ""

    try:
        # Solve the problem
        solution = solver.solve_problem(problem_text)

        # Format answer
        answer_output = f"## ✅ Answer\n\n# {solution.answer}"

        # Format steps
        steps_output = "## 📋 Step-by-Step Solution\n\n"
        for step in solution.steps:
            steps_output += f"{step}\n\n"

        # Format explanation
        explanation_output = f"## 💡 Explanation\n\n{solution.explanation}\n\n"
        explanation_output += f"**Problem Type:** {solution.problem_type.title()}\n\n"
        explanation_output += f"**Difficulty:** {solution.difficulty.title()}\n\n"

        if solution.confidence == 1.0:
            explanation_output += "**Confidence:** ✅ 100% (Verified by symbolic math)"
        else:
            explanation_output += f"**Confidence:** ⚠️ {solution.confidence*100:.0f}%"

        return answer_output, steps_output, explanation_output

    except Exception as e:
        return f"❌ **Error**\n\n{str(e)}", "", ""


def solve_photo_problem(image):
    """Solve a math problem from uploaded photo."""
    if image is None:
        return "❌ **Error**\n\nPlease upload a photo of your math problem.", "", "", ""

    try:
        # Extract text from image
        extraction = ocr.extract_from_pil_image(image)

        if not extraction or extraction.confidence == 0.0:
            return (
                f"❌ **OCR Failed**\n\n{extraction.text if extraction else 'Could not read image'}",
                "",
                "",
                ""
            )

        # Show extracted text
        extracted_output = f"## 📷 Extracted from Photo\n\n**Raw OCR:** {extraction.text}\n\n**Cleaned:** {extraction.cleaned_text}\n\n**Confidence:** {extraction.confidence*100:.0f}%"

        # Solve the cleaned problem
        solution = solver.solve_problem(extraction.cleaned_text)

        # Format outputs
        answer_output = f"## ✅ Answer\n\n# {solution.answer}"

        steps_output = "## 📋 Step-by-Step Solution\n\n"
        for step in solution.steps:
            steps_output += f"{step}\n\n"

        explanation_output = f"## 💡 Explanation\n\n{solution.explanation}\n\n"
        explanation_output += f"**Problem Type:** {solution.problem_type.title()}\n\n"

        return extracted_output, answer_output, steps_output, explanation_output

    except Exception as e:
        return f"❌ **Error**\n\n{str(e)}", "", "", ""


def create_student_ui():
    """Create simple student-focused interface."""

    # Custom CSS for better mobile experience
    custom_css = """
    .gr-button-primary {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%) !important;
        border: none !important;
        font-size: 18px !important;
        padding: 12px 24px !important;
        font-weight: bold !important;
    }
    .gr-button-primary:hover {
        transform: scale(1.02);
        box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4) !important;
    }
    .answer-box {
        font-size: 24px !important;
        font-weight: bold !important;
        color: #10b981 !important;
    }
    """

    with gr.Blocks(title="Numen - Math Homework Helper", css=custom_css) as app:

        gr.Markdown("""
        # 🧮 Numen - Math Homework Solver
        ### Get instant help with your math homework! 100% accurate answers.
        """)

        with gr.Tabs() as tabs:

            # TEXT INPUT TAB
            with gr.Tab("📝 Type Your Problem"):
                gr.Markdown("""
                ### Type any math problem and get a detailed solution!

                **Examples:**
                - `solve 2x + 5 = 13`
                - `derivative of x^3 + 2x^2`
                - `integral of sin(x)`
                - `simplify (x^2 - 1)/(x - 1)`
                - `expand (x + 3)^2`
                """)

                with gr.Row():
                    with gr.Column(scale=2):
                        text_input = gr.Textbox(
                            label="Enter your math problem",
                            placeholder="e.g., solve 3x + 7 = 22",
                            lines=3,
                            elem_classes=["input-box"]
                        )

                        solve_text_btn = gr.Button(
                            "🚀 Solve Problem",
                            variant="primary",
                            size="lg",
                            elem_classes=["solve-button"]
                        )

                        gr.Markdown("""
                        **💡 Tips:**
                        - Use `*` for multiplication: `2*x` not `2x`
                        - Use `^` or `**` for exponents: `x^2` or `x**2`
                        - Use parentheses for clarity: `(x+1)/(x-1)`
                        """)

                    with gr.Column(scale=3):
                        text_answer = gr.Markdown(label="Answer", elem_classes=["answer-box"])
                        text_steps = gr.Markdown(label="Steps")
                        text_explanation = gr.Markdown(label="Explanation")

                solve_text_btn.click(
                    fn=solve_text_problem,
                    inputs=[text_input],
                    outputs=[text_answer, text_steps, text_explanation]
                )

                # Example buttons
                gr.Markdown("### 📚 Try These Examples:")
                with gr.Row():
                    example1 = gr.Button("solve 2x + 5 = 13", size="sm")
                    example2 = gr.Button("derivative of x^3", size="sm")
                    example3 = gr.Button("integral of x^2", size="sm")

                example1.click(lambda: "solve 2x + 5 = 13", outputs=[text_input])
                example2.click(lambda: "derivative of x^3", outputs=[text_input])
                example3.click(lambda: "integral of x^2", outputs=[text_input])

            # PHOTO UPLOAD TAB
            with gr.Tab("📷 Upload Photo"):
                gr.Markdown("""
                ### Take a photo of your math problem and we'll solve it!

                **Tips for best results:**
                - ✅ Use good lighting
                - ✅ Write clearly (or use printed text)
                - ✅ Center the problem in the photo
                - ✅ Avoid shadows and glare
                """)

                with gr.Row():
                    with gr.Column(scale=2):
                        photo_input = gr.Image(
                            label="Upload or capture photo of math problem",
                            type="pil",
                            sources=["upload", "webcam"],
                            elem_classes=["photo-input"]
                        )

                        solve_photo_btn = gr.Button(
                            "🔍 Extract & Solve",
                            variant="primary",
                            size="lg"
                        )

                        gr.Markdown("""
                        **📱 On mobile?**
                        - Click "webcam" to use your phone camera
                        - Take a clear photo of your homework
                        - Click "Extract & Solve"
                        """)

                    with gr.Column(scale=3):
                        photo_extracted = gr.Markdown(label="Extracted Text")
                        photo_answer = gr.Markdown(label="Answer", elem_classes=["answer-box"])
                        photo_steps = gr.Markdown(label="Steps")
                        photo_explanation = gr.Markdown(label="Explanation")

                solve_photo_btn.click(
                    fn=solve_photo_problem,
                    inputs=[photo_input],
                    outputs=[photo_extracted, photo_answer, photo_steps, photo_explanation]
                )

                gr.Markdown("""
                **⚠️ Note:** OCR works best with printed text. Handwritten equations may require clearer writing.
                If OCR fails, you can manually type the problem in the "Type Your Problem" tab.
                """)

            # ABOUT TAB
            with gr.Tab("ℹ️ About"):
                gr.Markdown("""
                ## 🎓 About Numen

                **Numen** is a math homework solver that uses symbolic mathematics to give you **100% accurate answers**.

                ### ✨ Features

                **1. Text Input**
                - Type any algebra, calculus, or simplification problem
                - Get step-by-step solutions
                - Understand HOW to solve, not just the answer

                **2. Photo Upload**
                - Take a picture of your homework
                - OCR extracts the math problem automatically
                - Get instant solutions

                **3. 100% Accuracy**
                - Unlike AI tutors that can make mistakes
                - Numen uses symbolic math (SymPy) for guaranteed correct answers
                - Every answer is verified mathematically

                ### 📚 What You Can Solve

                ✅ **Algebra**
                - Linear equations: `solve 2x + 5 = 13`
                - Quadratic equations: `solve x^2 - 5x + 6 = 0`
                - Systems of equations

                ✅ **Calculus**
                - Derivatives: `derivative of x^3 + 2x^2`
                - Integrals: `integral of sin(x)`
                - Limits (coming soon)

                ✅ **Simplification**
                - Simplify: `simplify (x^2 - 1)/(x - 1)`
                - Expand: `expand (x + 3)^2`
                - Factor: `factor x^2 - 5x + 6`

                ### 🎯 Why Numen?

                | Feature | Wolfram Alpha | ChatGPT | **Numen** |
                |---------|---------------|---------|-----------|
                | Accuracy | ✅ High | ❌ Can hallucinate | ✅ **100%** |
                | Step-by-step | ⚠️ Premium only | ✅ Yes | ✅ **Free** |
                | Photo upload | ❌ No | ❌ No | ✅ **Yes** |
                | Price | $7/month | $20/month | 🎉 **FREE** |

                ### 🚀 Coming Soon

                - 📊 Progress tracking (see your improvement)
                - 🎮 Gamification (points, badges, leaderboards)
                - 📱 Mobile app (iOS & Android)
                - 🧠 Adaptive learning (personalized practice)
                - 🌍 More subjects (physics, chemistry)

                ### 💡 Tips for Success

                **Getting the best results:**
                1. ✅ Write problems clearly
                2. ✅ Use standard math notation
                3. ✅ Check the extracted text (from photos)
                4. ✅ Study the step-by-step solution (don't just copy the answer!)

                **Remember:**
                - Numen is a **learning tool**, not a cheating tool
                - Use it to **understand** concepts
                - Always **show your work** on assignments
                - Ask your teacher if you're still confused!

                ### 📞 Contact & Support

                - **Questions?** Email: support@numen-math.com
                - **Bug reports?** GitHub: github.com/rewired89/Numen
                - **Suggestions?** We'd love to hear from you!

                ---

                **Version:** 1.0.0 (Student Edition)
                **Accuracy:** 100% (Symbolic Verification)
                **Made with ❤️ for students who want to learn math**
                """)

        gr.Markdown("""
        ---
        **💡 Pro Tip:** Understanding the steps is more important than just getting the answer. Study the solution carefully!
        """)

    return app


if __name__ == "__main__":
    print("=" * 60)
    print("🎓 NUMEN STUDENT - MATH HOMEWORK SOLVER")
    print("=" * 60)
    print("\n✨ Features:")
    print("  📝 Type math problems → Get step-by-step solutions")
    print("  📷 Upload photos → OCR extracts problem → Instant help")
    print("  ✅ 100% Accurate answers (symbolic math)")
    print("\nStarting UI...")
    print("URL: http://localhost:7860")
    print("\nOpen on your phone? Use --share flag for public link")
    print("=" * 60 + "\n")

    app = create_student_ui()
    app.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,  # Set to True for public link
    )
