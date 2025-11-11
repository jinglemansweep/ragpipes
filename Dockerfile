# Use Python 3.12 slim image
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH="/app/src" \
    CHROMA_DB_PATH="/app/data/chroma" \
    HOST=0.0.0.0 \
    PORT=8000 \
    ENVIRONMENT=production

# Create app directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create Python virtual environment and upgrade pip
RUN python -m venv /opt/venv \
    && /opt/venv/bin/pip install --upgrade pip

# Add venv to PATH
ENV PATH="/opt/venv/bin:$PATH"

# Copy requirements first for better caching
COPY pyproject.toml README.md ./
COPY src/ ./src/

# Install Python dependencies in virtual environment (this layer will be cached if pyproject.toml doesn't change)
RUN pip install --no-cache-dir -e .

# Create non-root user
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app
USER app

# Create data directory for ChromaDB
RUN mkdir -p /app/data/chroma

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

# Run the application using virtual environment
CMD ["/opt/venv/bin/python", "-m", "uvicorn", "src.ragpipes.main:app", "--host", "0.0.0.0", "--port", "8000"]

# Labels
LABEL org.opencontainers.image.source=https://github.com/jinglemansweep/ragpipes
