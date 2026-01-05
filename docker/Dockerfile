# ==========================================
# Invoice Extraction System - API Container
# Python 3.12 + FastAPI + OCR
# ==========================================

# Base image: Python 3.12 (slim for smaller size)
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies
# - tesseract-ocr: OCR engine
# - tesseract-ocr-tur: Turkish language support
# - poppler-utils: PDF utilities
# - curl: Health checks
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-tur \
    tesseract-ocr-eng \
    poppler-utils \
    curl \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
# (Copy requirements first for better caching)
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src /app/src
COPY prompts /app/prompts

# Create necessary directories
RUN mkdir -p /app/data/uploads \
             /app/data/processed \
             /app/data/temp \
             /app/logs

# Expose API port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default command (can be overridden by docker-compose)
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
