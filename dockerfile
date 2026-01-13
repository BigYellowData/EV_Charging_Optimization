# Multi-stage Dockerfile for optimized production builds
FROM python:3.11-slim as builder

WORKDIR /build

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Production stage
FROM python:3.11-slim

WORKDIR /app

# Copy installed dependencies from builder
COPY --from=builder /root/.local /root/.local

# Copy source code
COPY src/ ./src/
COPY .env* ./

# Create directories
RUN mkdir -p data_cache results logs

# Add local bin to PATH
ENV PATH=/root/.local/bin:$PATH

# Set Python path
ENV PYTHONPATH=/app

# Healthcheck
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
CMD python -c "from src.config.settings import settings; print('OK')" || exit 1

# Entry point
ENTRYPOINT ["python", "-m", "src.cli.main"]
CMD []
