# Numen Quick Start Guide

Get started with Numen in 3 easy steps!

## 🚀 Quick Launch

### Step 1: Install Dependencies

```bash
pip install -e .
```

This installs all required packages including:
- Core math libraries (SymPy, NumPy, SciPy)
- UI components (Gradio)
- OCR support (pytesseract, pix2tex, OpenCV)
- ML frameworks (PyTorch, Transformers)

### Step 2: Install System Dependencies (Optional for OCR)

For full OCR support, install Tesseract:

**Ubuntu/Debian:**
```bash
sudo apt-get install tesseract-ocr
```

**macOS:**
```bash
brew install tesseract
```

**Windows:**
Download from: https://github.com/UB-Mannheim/tesseract/wiki

### Step 3: Launch the UI

```bash
python launch_ui.py
```

Then open http://localhost:7860 in your browser!

## 📚 Usage Examples

### Example 1: Text Input

1. Go to the "📝 Text Solver" tab
2. Enter: `Solve for x: 2x + 5 = 13`
3. Click "Solve"
4. See verified solution: `x = 4` ✓

### Example 2: Image Upload

1. Go to the "📷 Image Solver" tab
2. Take a photo of an equation (or upload an image)
3. Click "Extract & Solve"
4. Numen will:
   - Extract the equation using OCR
   - Solve it mathematically
   - Verify the solution symbolically

### Example 3: PDF Processing

1. Go to the "📄 File Solver" tab
2. Upload a PDF with equations
3. Click "Process File"
4. Get all equations extracted and solved!

### Example 4: Cryptanalysis

1. Go to the "🔐 Cryptanalysis" tab
2. Describe your crypto system
3. Optionally enter RSA parameters (n, e)
4. Get vulnerability analysis with:
   - Security level estimation
   - Attack vectors
   - Mathematical weaknesses
   - Mitigation strategies

### Example 5: Neural Dynamics

1. Go to the "🧠 Neural Dynamics" tab
2. Describe neural signals or cognitive state
3. Select dynamical model (FitzHugh-Nagumo, Wilson-Cowan)
4. Get analysis with:
   - Equilibrium points
   - Stability classification
   - Cognitive state prediction
   - State transition probabilities

## 🎯 Key Features

### Zero Hallucination Mode
All solutions are symbolically verified using SymPy. If verification fails, the solution is rejected.

### Multi-Modal Input
- ✏️ Type equations directly
- 📷 Upload photos of equations
- 📄 Process PDF documents
- 📝 Parse text files with LaTeX

### Cross-Domain Analysis
- Apply topology to cryptography
- Use differential equations for neural modeling
- Bridge number theory and cryptanalysis

## 🔧 Advanced Usage

### Python API

```python
from numen import NumenEngine

# Create engine
engine = NumenEngine(
    use_mcts=True,              # Enable search
    require_verification=True,   # Zero hallucination mode
)

# Solve problem
result = engine.solve("Find derivative of x^3")

# Check results
print(f"Solution: {result.solution}")
print(f"Verified: {result.verified}")
print(f"Confidence: {result.confidence:.1%}")
```

### OCR API

```python
from numen.ui.ocr import EquationExtractor

extractor = EquationExtractor(use_latex_ocr=True)

# From image
equations = extractor.extract_from_image("equation.png")
print(f"Extracted: {equations[0].text}")

# From PDF
equations = extractor.extract_from_pdf("paper.pdf", pages=[1, 2])

# Auto-detect
equations = extractor.auto_extract("document.pdf")
```

### REST API

Start the API server:

```bash
python -m uvicorn numen.api.server:app --host 0.0.0.0 --port 8000
```

Then use:

```bash
curl -X POST "http://localhost:8000/solve" \
  -H "Content-Type: application/json" \
  -d '{"problem": "2x + 5 = 13"}'
```

## 🎓 Training (Advanced)

Fine-tune Numen on custom datasets:

```bash
python -m numen.training.train \
  --base-model deepseek-ai/deepseek-math-7b-base \
  --epochs 3 \
  --batch-size 4 \
  --output-dir checkpoints/custom
```

## 🐛 Troubleshooting

### OCR not working
- Install Tesseract: `sudo apt-get install tesseract-ocr`
- Check pytesseract: `python -c "import pytesseract; print(pytesseract.get_tesseract_version())"`

### Out of memory
- Use smaller batch sizes
- Enable 4-bit quantization
- Use CPU instead of GPU

### Gradio UI not loading
- Check port 7860 is available
- Try different port: `python launch_ui.py --port 8080`
- Check firewall settings

## 📖 Next Steps

- Read the full README.md
- Explore examples/ directory
- Check tests/ for unit tests
- Try the cryptanalysis features
- Experiment with neural dynamics
- Fine-tune on your own dataset

## 💡 Tips

1. **For best OCR results**: Use clear, high-contrast images
2. **For complex problems**: Enable MCTS search
3. **For cryptanalysis**: Provide concrete parameters when possible
4. **For speed**: Disable MCTS for simple equations

## 🆘 Need Help?

- Check the documentation in README.md
- Review examples in examples/
- Inspect the code in numen/

Happy solving! 🧮
