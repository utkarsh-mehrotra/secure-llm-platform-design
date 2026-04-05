# Use a slim, secure Python image
FROM python:3.11-slim as base

# Set build-time metadata
LABEL maintainer="Secure LLM Platform Team"
LABEL version="1.0.0"

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PYTHONPATH /app

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY src/ /app/src/
COPY tests/ /app/tests/

# Create a non-root user for security
RUN useradd -m appuser
USER appuser

# Expose the API port
EXPOSE 8000

# Health check to ensure the service is running
HEALTHCHECK --interval=30s --timeout=3s \
  CMD curl -f http://localhost:8000/health || exit 1

# Start the FastAPI application
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
