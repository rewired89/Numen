from setuptools import setup, find_packages

setup(
    name="numen",
    version="1.0.0",
    description="Math solver for everyone — Algebra to Calculus, Matrices, ODEs, Statistics, Graphing",
    author="rewired89",
    author_email="sanchezleal1989@gmail.com",
    packages=find_packages(),
    python_requires=">=3.9",
    install_requires=[
        # Symbolic math (core engine)
        "sympy>=1.12",
        "numpy>=1.24.0",
        "scipy>=1.10.0",
        # Web UI
        "gradio>=4.0.0",
        "matplotlib>=3.7.0",
        # API server
        "fastapi>=0.100.0",
        "uvicorn>=0.23.0",
        "pydantic>=2.0.0",
        # OCR
        "pillow>=10.0.0",
        "pytesseract>=0.3.10",
        # Utilities
        "networkx>=3.1",
    ],
    extras_require={
        "dev": ["pytest>=7.4.0", "black>=23.0.0", "mypy>=1.4.0"],
        "ocr-full": [
            "pdf2image>=1.16.0",
            "opencv-python>=4.8.0",
        ],
        "training": [
            "torch>=2.0.0",
            "transformers>=4.30.0",
            "accelerate>=0.20.0",
            "datasets>=2.14.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "numen=numen.cli:main",
        ],
    },
)

