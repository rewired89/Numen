"""
Simple OCR for extracting math problems from images.

Uses pytesseract for basic OCR (works for printed text).
For handwritten equations, we'll add pix2tex later.
"""

import re
from typing import Optional, List
from dataclasses import dataclass


@dataclass
class ExtractedProblem:
    """Extracted math problem from image."""
    text: str
    confidence: float
    cleaned_text: str


class SimpleOCR:
    """
    Simple OCR for math problems.

    For now, uses pytesseract (handles printed text well).
    Can be extended with pix2tex for handwritten LaTeX later.
    """

    def __init__(self):
        try:
            import pytesseract
            from PIL import Image
            import cv2
            import numpy as np
            self.pytesseract = pytesseract
            self.Image = Image
            self.cv2 = cv2
            self.np = np
            self.available = True
        except ImportError:
            self.available = False

    def extract_from_image(self, image_path: str) -> Optional[ExtractedProblem]:
        """
        Extract math problem from image file.

        Args:
            image_path: Path to image file

        Returns:
            ExtractedProblem or None if failed
        """
        if not self.available:
            return ExtractedProblem(
                text="OCR not available. Install: pip install pytesseract pillow opencv-python",
                confidence=0.0,
                cleaned_text="",
            )

        try:
            # Load image
            image = self.Image.open(image_path)

            # Convert to OpenCV format
            img_cv = self.cv2.cvtColor(self.np.array(image), self.cv2.COLOR_RGB2BGR)

            # Preprocess image for better OCR
            gray = self.cv2.cvtColor(img_cv, self.cv2.COLOR_BGR2GRAY)

            # Increase contrast
            gray = self.cv2.convertScaleAbs(gray, alpha=1.5, beta=0)

            # Denoise
            denoised = self.cv2.fastNlMeansDenoising(gray)

            # Threshold
            thresh = self.cv2.adaptiveThreshold(
                denoised, 255,
                self.cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                self.cv2.THRESH_BINARY, 11, 2
            )

            # Extract text
            text = self.pytesseract.image_to_string(thresh)

            # Clean up the text
            cleaned = self._clean_math_text(text)

            # Estimate confidence (simple heuristic)
            confidence = 0.8 if cleaned and len(cleaned) > 0 else 0.0

            return ExtractedProblem(
                text=text.strip(),
                confidence=confidence,
                cleaned_text=cleaned,
            )

        except Exception as e:
            return ExtractedProblem(
                text=f"Error: {str(e)}",
                confidence=0.0,
                cleaned_text="",
            )

    def extract_from_pil_image(self, pil_image) -> Optional[ExtractedProblem]:
        """
        Extract math problem from PIL Image object.

        Args:
            pil_image: PIL Image

        Returns:
            ExtractedProblem or None if failed
        """
        if not self.available:
            return ExtractedProblem(
                text="OCR not available. Install: pip install pytesseract pillow opencv-python",
                confidence=0.0,
                cleaned_text="",
            )

        try:
            # Convert to OpenCV format
            img_cv = self.cv2.cvtColor(self.np.array(pil_image), self.cv2.COLOR_RGB2BGR)

            # Preprocess
            gray = self.cv2.cvtColor(img_cv, self.cv2.COLOR_BGR2GRAY)
            gray = self.cv2.convertScaleAbs(gray, alpha=1.5, beta=0)
            denoised = self.cv2.fastNlMeansDenoising(gray)
            thresh = self.cv2.adaptiveThreshold(
                denoised, 255,
                self.cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                self.cv2.THRESH_BINARY, 11, 2
            )

            # Extract text
            text = self.pytesseract.image_to_string(thresh)
            cleaned = self._clean_math_text(text)
            confidence = 0.8 if cleaned and len(cleaned) > 0 else 0.0

            return ExtractedProblem(
                text=text.strip(),
                confidence=confidence,
                cleaned_text=cleaned,
            )

        except Exception as e:
            return ExtractedProblem(
                text=f"Error: {str(e)}",
                confidence=0.0,
                cleaned_text="",
            )

    def _clean_math_text(self, text: str) -> str:
        """
        Clean up OCR text to make it suitable for math parsing.

        Args:
            text: Raw OCR text

        Returns:
            Cleaned text
        """
        # Remove extra whitespace
        cleaned = " ".join(text.split())

        # Common OCR corrections
        corrections = {
            "×": "*",
            "÷": "/",
            "—": "-",
            "–": "-",
            "l": "1",  # lowercase L often mistaken for 1
        }

        for old, new in corrections.items():
            cleaned = cleaned.replace(old, new)

        # Remove non-math characters (keep numbers, letters, operators, =, parentheses)
        cleaned = re.sub(r'[^0-9a-zA-Z+\-*/=()^\s.,]', '', cleaned)

        # Remove extra spaces around operators
        cleaned = re.sub(r'\s*([+\-*/=()^])\s*', r'\1', cleaned)

        return cleaned.strip()
