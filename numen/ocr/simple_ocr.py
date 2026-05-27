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

            # Auto-detect Tesseract on Windows if not already in PATH
            import sys, os
            if sys.platform == "win32":
                candidates = [
                    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
                    r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
                    os.path.expanduser(r"~\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"),
                ]
                for path in candidates:
                    if os.path.isfile(path):
                        pytesseract.pytesseract.tesseract_cmd = path
                        break

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
            image = self.Image.open(image_path)
            img_cv = self.cv2.cvtColor(self.np.array(image), self.cv2.COLOR_RGB2BGR)
            processed = self._preprocess(img_cv)

            cfg_block  = "--oem 3 --psm 6"
            cfg_sparse = "--oem 3 --psm 11"
            t1 = self.pytesseract.image_to_string(processed, config=cfg_block).strip()
            t2 = self.pytesseract.image_to_string(processed, config=cfg_sparse).strip()
            text = t1 if len(t1) >= len(t2) else t2

            cleaned = self._clean_math_text(text)
            confidence = 0.8 if cleaned else 0.0
            return ExtractedProblem(text=text, confidence=confidence, cleaned_text=cleaned)

        except Exception as e:
            return ExtractedProblem(text=f"Error: {str(e)}", confidence=0.0, cleaned_text="")

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
            img_cv = self.cv2.cvtColor(self.np.array(pil_image), self.cv2.COLOR_RGB2BGR)
            processed = self._preprocess(img_cv)

            # Try multiple Tesseract PSM modes; pick the result with most content
            cfg_block  = "--oem 3 --psm 6"
            cfg_sparse = "--oem 3 --psm 11"
            t1 = self.pytesseract.image_to_string(processed, config=cfg_block).strip()
            t2 = self.pytesseract.image_to_string(processed, config=cfg_sparse).strip()
            text = t1 if len(t1) >= len(t2) else t2

            cleaned = self._clean_math_text(text)
            confidence = 0.8 if cleaned else 0.0
            return ExtractedProblem(text=text, confidence=confidence, cleaned_text=cleaned)

        except Exception as e:
            return ExtractedProblem(text=f"Error: {str(e)}", confidence=0.0, cleaned_text="")

    def _preprocess(self, img_cv):
        """Upscale + denoise + threshold for best Tesseract accuracy on math."""
        gray = self.cv2.cvtColor(img_cv, self.cv2.COLOR_BGR2GRAY)

        # Upscale 3x — critical for superscripts and small symbols
        h, w = gray.shape
        gray = self.cv2.resize(gray, (w * 3, h * 3), interpolation=self.cv2.INTER_CUBIC)

        # Mild contrast boost
        gray = self.cv2.convertScaleAbs(gray, alpha=1.4, beta=10)

        # Denoise
        gray = self.cv2.fastNlMeansDenoising(gray, h=10)

        # Otsu threshold works better than adaptive for math on white paper
        _, thresh = self.cv2.threshold(gray, 0, 255, self.cv2.THRESH_BINARY + self.cv2.THRESH_OTSU)
        return thresh

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
