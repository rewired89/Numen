# Numen: Mathematical Reasoning Engine

A specialized AI mathematical reasoning engine designed for cross-domain problem solving in cybersecurity and neuroscience applications.

## Overview

Numen bridges disparate mathematical fields to discover novel insights and attack vectors. Unlike general math solvers, it combines Monte Carlo Tree Search, symbolic verification, and multi-strategy ensembles to solve complex problems with 100% verification accuracy.

## Core Capabilities

- **Multi-path Problem Solving**: MCTS-based exploration with automatic fallback strategies
- **Symbolic Verification**: 100% correctness guarantee using SymPy integration
- **Cross-domain Translation**: Applies topology to cryptography, differential equations to neural modeling
- **Zero Hallucination**: Self-verification loop eliminates unverified answers

## Architecture

```
numen/
├── core/           # Core reasoning engine (MCTS, verification, solver)
├── strategies/     # Domain-specific solving strategies
├── training/       # Model training and fine-tuning pipeline
├── api/            # Production REST API interface
├── ui/             # Gradio web UI with OCR support
└── utils/          # Helper functions and utilities
```

## Installation

```bash
pip install -e .
```

## Usage

### Web UI (Recommended)

Launch the interactive Gradio interface:

```bash
python launch_ui.py

# With public share link
python launch_ui.py --share

# Custom port
python launch_ui.py --port 8080
```

Then open http://localhost:7860 in your browser.

**UI Features:**
- 📝 Text input for direct equation entry
- 📷 Image upload with OCR (extract equations from photos)
- 📄 File upload (PDF, images, text files)
- 🔐 Cryptanalysis interface
- 🧠 Neural dynamics analysis

### Python API

```python
from numen import NumenEngine

engine = NumenEngine()
result = engine.solve("Prove that there are infinitely many primes")
print(result.solution)
print(result.verification_status)
```

### OCR Usage

```python
from numen.ui.ocr import EquationExtractor

extractor = EquationExtractor()

# Extract from image
equations = extractor.extract_from_image("equation.png")
print(equations[0].text)

# Extract from PDF
equations = extractor.extract_from_pdf("math_paper.pdf")

# Auto-detect file type
equations = extractor.auto_extract("document.pdf")
```

## Primary Use Cases

### Cryptanalysis (Nyx Cybersecurity)
- Structural weakness detection in encryption schemes
- Novel attack vector prediction using number theory
- Protocol vulnerability assessment

### Neural Signal Analysis (NeuroCompass)
- Cognitive state prediction using dynamical systems
- Brain signal pattern optimization
- Statistical mechanics applied to neural networks

## Technical Stack

- **Base Models**: DeepSeek-Math / Llama 3.1 70B (fine-tuned)
- **Verification**: SymPy, SageMath
- **Search**: Monte Carlo Tree Search
- **Training Data**: arXiv papers, OpenWebMath, MATH benchmark
- **UI**: Gradio web interface
- **OCR**: pytesseract, pix2tex (LaTeX OCR)
- **Image Processing**: OpenCV, PIL

## Success Metrics

- 85%+ accuracy on MATH competition benchmark
- 100% symbolic verification pass rate
- Zero tolerance for unverified outputs

## License

Proprietary - Nyx Cybersecurity
