# VM Assessment BOM Generator - Containerfile
# Compatible with Docker, Podman, Buildah
FROM python:3.11-slim-bullseye

# Build arguments
ARG BUILD_DATE
ARG BUILD_REVISION
ARG VERSION=1.0.0

# Metadata labels for GitHub Container Registry
LABEL org.opencontainers.image.title="VM Assessment BOM Generator"
LABEL org.opencontainers.image.description="Web-based tool for generating Bill of Materials from VM assessment files"
LABEL org.opencontainers.image.version="${VERSION}"
LABEL org.opencontainers.image.revision="${BUILD_REVISION}"
LABEL org.opencontainers.image.created="${BUILD_DATE}"
LABEL org.opencontainers.image.authors="VM Assessment Team"
LABEL org.opencontainers.image.url="https://github.com/your-org/vm-assessment-bom"
LABEL org.opencontainers.image.source="https://github.com/your-org/vm-assessment-bom"
LABEL org.opencontainers.image.vendor="Your Organization"
LABEL org.opencontainers.image.licenses="Enterprise"

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV APP_ENV=production
ENV WORKERS=4
ENV PORT=8000

# Create non-root user for security
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Set work directory
WORKDIR /app

# Copy requirements first for better layer caching
COPY requirements.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy web application code
COPY web_app/ ./

# Create necessary directories with proper permissions
RUN mkdir -p /app/static/uploads /app/logs && \
    chown -R appuser:appuser /app && \
    chmod -R 755 /app

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/', timeout=10)"

# Start command
CMD ["python", "-m", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]