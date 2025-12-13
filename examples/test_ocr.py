#!/usr/bin/env python3
"""
Test OCR capabilities of Numen.
"""

from numen.ui.ocr import EquationExtractor
from pathlib import Path


def test_text_extraction():
    """Test extracting equations from text."""
    print("=" * 60)
    print("Testing Text Extraction")
    print("=" * 60)

    extractor = EquationExtractor()

    # Create a test text file
    test_content = """
    Mathematical Problems:

    1. Solve for x: 2x + 5 = 13

    2. Find the derivative: f(x) = x³ + 2x² - 5x + 1

    3. Simplify: (x² - 1) / (x - 1)

    4. LaTeX equation: $\\int_0^1 x^2 dx = \\frac{1}{3}$
    """

    with open("/tmp/test_equations.txt", "w") as f:
        f.write(test_content)

    equations = extractor.extract_from_text_file("/tmp/test_equations.txt")

    print(f"\nExtracted {len(equations)} equations:\n")
    for i, eq in enumerate(equations, 1):
        print(f"{i}. {eq.text}")
        print(f"   Confidence: {eq.confidence:.1%}")
        if eq.latex:
            print(f"   LaTeX: {eq.latex}")
        print()


def test_image_extraction():
    """Test extracting equations from images."""
    print("\n" + "=" * 60)
    print("Testing Image Extraction (requires sample image)")
    print("=" * 60)

    # Note: This requires actual image files
    # In a real scenario, you'd have test images

    print("\nTo test image extraction:")
    print("1. Save an image with an equation to /tmp/equation.png")
    print("2. Run: python -c \"from numen.ui.ocr import EquationExtractor; eq = EquationExtractor(); print(eq.extract_from_image('/tmp/equation.png'))\"")


def main():
    """Run OCR tests."""
    test_text_extraction()
    test_image_extraction()

    print("\n" + "=" * 60)
    print("OCR Testing Complete!")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
