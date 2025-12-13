"""
OCR and equation extraction from images and documents.
Supports handwritten equations, printed equations, and LaTeX.
"""

from typing import List, Optional, Dict, Any, Union
from pathlib import Path
import re
from dataclasses import dataclass

try:
    import cv2
    import numpy as np
    from PIL import Image
    import pytesseract
except ImportError:
    cv2 = None
    np = None
    Image = None
    pytesseract = None

try:
    from pdf2image import convert_from_path
except ImportError:
    convert_from_path = None

try:
    from pix2tex.cli import LatexOCR
except ImportError:
    LatexOCR = None


@dataclass
class ExtractedEquation:
    """Equation extracted from image or document."""

    text: str
    latex: Optional[str] = None
    confidence: float = 0.0
    bounding_box: Optional[tuple] = None
    page_number: Optional[int] = None


class EquationExtractor:
    """
    Extract mathematical equations from images and documents.

    Supports:
    - Images (PNG, JPG, etc.)
    - PDF documents
    - Handwritten equations
    - Printed equations
    - LaTeX notation
    """

    def __init__(self, use_latex_ocr: bool = True):
        """
        Initialize equation extractor.

        Args:
            use_latex_ocr: Use specialized LaTeX OCR (pix2tex) for better accuracy
        """
        self.use_latex_ocr = use_latex_ocr and LatexOCR is not None
        self.latex_model = None

        if self.use_latex_ocr:
            try:
                self.latex_model = LatexOCR()
            except Exception as e:
                print(f"Warning: Could not load LaTeX OCR model: {e}")
                self.use_latex_ocr = False

    def extract_from_image(
        self,
        image_path: Union[str, Path, Image.Image],
        preprocess: bool = True,
    ) -> List[ExtractedEquation]:
        """
        Extract equations from image.

        Args:
            image_path: Path to image or PIL Image
            preprocess: Apply preprocessing for better OCR

        Returns:
            List of extracted equations
        """
        if Image is None:
            raise ImportError("PIL not installed. Install with: pip install pillow")

        # Load image
        if isinstance(image_path, (str, Path)):
            image = Image.open(image_path)
        else:
            image = image_path

        # Convert to numpy array
        if cv2 is not None and preprocess:
            img_array = np.array(image)
            img_array = self._preprocess_image(img_array)
            image = Image.fromarray(img_array)

        equations = []

        # Try LaTeX OCR first (best for math)
        if self.use_latex_ocr and self.latex_model:
            try:
                latex = self.latex_model(image)
                equations.append(ExtractedEquation(
                    text=latex,
                    latex=latex,
                    confidence=0.9,  # pix2tex is generally reliable
                ))
            except Exception as e:
                print(f"LaTeX OCR failed: {e}")

        # Fallback to Tesseract
        if not equations and pytesseract is not None:
            try:
                # Use Tesseract with math-specific config
                text = pytesseract.image_to_string(
                    image,
                    config='--psm 6'  # Assume uniform block of text
                )

                # Clean extracted text
                text = self._clean_ocr_text(text)

                if text.strip():
                    equations.append(ExtractedEquation(
                        text=text,
                        confidence=0.6,  # Tesseract less reliable for math
                    ))
            except Exception as e:
                print(f"Tesseract OCR failed: {e}")

        # If all OCR fails, return simple text extraction
        if not equations:
            equations.append(ExtractedEquation(
                text="Could not extract equation. Please type it manually.",
                confidence=0.0,
            ))

        return equations

    def extract_from_pdf(
        self,
        pdf_path: Union[str, Path],
        pages: Optional[List[int]] = None,
    ) -> List[ExtractedEquation]:
        """
        Extract equations from PDF document.

        Args:
            pdf_path: Path to PDF file
            pages: Specific pages to extract (None = all pages)

        Returns:
            List of extracted equations with page numbers
        """
        if convert_from_path is None:
            raise ImportError("pdf2image not installed. Install with: pip install pdf2image")

        # Convert PDF to images
        images = convert_from_path(pdf_path, dpi=300)

        all_equations = []

        for page_num, image in enumerate(images, start=1):
            if pages and page_num not in pages:
                continue

            equations = self.extract_from_image(image)

            # Add page number
            for eq in equations:
                eq.page_number = page_num
                all_equations.append(eq)

        return all_equations

    def _preprocess_image(self, img: np.ndarray) -> np.ndarray:
        """
        Preprocess image for better OCR.

        Steps:
        - Convert to grayscale
        - Denoise
        - Threshold
        - Deskew if needed
        """
        if cv2 is None:
            return img

        # Convert to grayscale
        if len(img.shape) == 3:
            gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
        else:
            gray = img

        # Denoise
        denoised = cv2.fastNlMeansDenoising(gray)

        # Adaptive threshold
        thresh = cv2.adaptiveThreshold(
            denoised,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            11,
            2
        )

        # Invert if dark background
        if np.mean(thresh) < 127:
            thresh = cv2.bitwise_not(thresh)

        return thresh

    def _clean_ocr_text(self, text: str) -> str:
        """Clean and normalize OCR output."""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)

        # Common OCR corrections for math symbols
        replacements = {
            'x': '×',  # multiplication (context-dependent)
            '÷': '/',
            '—': '-',
            '–': '-',
            '"': '',
            '"': '',
        }

        # Apply replacements carefully
        # (In practice, we'd use more sophisticated logic)

        return text.strip()

    def extract_from_text_file(
        self,
        file_path: Union[str, Path],
    ) -> List[ExtractedEquation]:
        """
        Extract equations from text file.

        Looks for:
        - Lines with mathematical operators
        - LaTeX equations (between $ or $$)
        - Numbered equations
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        equations = []

        # Extract LaTeX equations
        latex_patterns = [
            r'\$\$([^$]+)\$\$',  # Display mode
            r'\$([^$]+)\$',      # Inline mode
            r'\\begin\{equation\}(.*?)\\end\{equation\}',  # Environment
        ]

        for pattern in latex_patterns:
            matches = re.findall(pattern, content, re.DOTALL)
            for match in matches:
                equations.append(ExtractedEquation(
                    text=match.strip(),
                    latex=match.strip(),
                    confidence=1.0,  # Direct LaTeX
                ))

        # Extract lines that look like equations
        lines = content.split('\n')
        math_symbols = ['=', '+', '-', '*', '/', '^', '√', '∫', '∑', '∏']

        for line in lines:
            # Skip if already extracted as LaTeX
            if any(eq.text in line for eq in equations):
                continue

            # Check if line contains math symbols
            if any(sym in line for sym in math_symbols):
                clean_line = line.strip()
                if clean_line:
                    equations.append(ExtractedEquation(
                        text=clean_line,
                        confidence=0.8,
                    ))

        return equations

    def auto_extract(
        self,
        file_path: Union[str, Path],
    ) -> List[ExtractedEquation]:
        """
        Automatically detect file type and extract equations.

        Args:
            file_path: Path to file (image, PDF, or text)

        Returns:
            List of extracted equations
        """
        path = Path(file_path)
        suffix = path.suffix.lower()

        if suffix in ['.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.webp']:
            return self.extract_from_image(file_path)
        elif suffix == '.pdf':
            return self.extract_from_pdf(file_path)
        elif suffix in ['.txt', '.tex', '.md']:
            return self.extract_from_text_file(file_path)
        else:
            raise ValueError(f"Unsupported file type: {suffix}")

    def batch_extract(
        self,
        file_paths: List[Union[str, Path]],
    ) -> Dict[str, List[ExtractedEquation]]:
        """
        Extract equations from multiple files.

        Returns:
            Dictionary mapping file paths to extracted equations
        """
        results = {}

        for file_path in file_paths:
            try:
                equations = self.auto_extract(file_path)
                results[str(file_path)] = equations
            except Exception as e:
                print(f"Error processing {file_path}: {e}")
                results[str(file_path)] = []

        return results
