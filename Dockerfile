FROM python:3.11-slim

WORKDIR /app

# System deps: tesseract for OCR, build tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps first (cached layer)
COPY requirements.txt .
RUN pip install --no-cache-dir \
    sympy numpy scipy matplotlib \
    gradio pillow pytesseract \
    fastapi uvicorn pydantic \
    networkx

# Copy project and install
COPY . .
RUN pip install --no-cache-dir -e .

# Gradio port
EXPOSE 7860

# Single command to start Numen
CMD ["numen", "up", "--port", "7860", "--host", "0.0.0.0"]
