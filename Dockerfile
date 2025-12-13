FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Install Numen
RUN pip install -e .

# Expose API port
EXPOSE 8000

# Run API server
CMD ["python", "-m", "uvicorn", "numen.api.server:app", "--host", "0.0.0.0", "--port", "8000"]
