# Kafka E-commerce System - Production Dockerfile
# Multi-stage build for optimized production image

# Build stage
FROM python:3.11-slim AS builder

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    librdkafka-dev \
    pkg-config \
    libssl-dev \
    libffi-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create and set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Production stage
FROM python:3.11-slim AS production

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH=/root/.local/bin:$PATH \
    ENVIRONMENT=production

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    netcat-traditional \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user for security
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Create application directory
WORKDIR /app

# Copy Python dependencies from builder stage
COPY --from=builder /root/.local /root/.local

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p logs data temp \
    && chown -R appuser:appuser /app

# Copy environment template
COPY .env.example .env

# Health check script
COPY <<EOF /app/healthcheck.sh
#!/bin/bash
set -e

# Check if main application is responding
curl -f http://localhost:5005/health || exit 1

# Check individual services
services=("5011" "6002" "5003" "5004")
for port in "\${services[@]}"; do
    curl -f http://localhost:\$port/health || exit 1
done

echo "All services healthy"
EOF

RUN chmod +x /app/healthcheck.sh

# Expose ports for all services
EXPOSE 5011 6002 5003 5004 5005

# Switch to non-root user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD /app/healthcheck.sh

# Default command
CMD ["python", "main.py"]

# Labels for metadata
LABEL maintainer="Kafka E-commerce Team" \
      version="1.0.0" \
      description="Kafka-based E-commerce Order Processing System" \
      org.opencontainers.image.title="Kafka E-commerce" \
      org.opencontainers.image.description="Production-ready e-commerce order processing system" \
      org.opencontainers.image.version="1.0.0" \
      org.opencontainers.image.vendor="E-commerce Solutions" \
      org.opencontainers.image.licenses="MIT"