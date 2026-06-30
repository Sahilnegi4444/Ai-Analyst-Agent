# Multi-stage Docker build
# =====================================================================
# STAGE 1: Builder
# =====================================================================
FROM python:3.12-slim AS builder

WORKDIR /build

# Install compilation tools
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set up virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
ENV PIP_NO_CACHE_DIR=1

# Copy requirements and install python packages
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Pre-download SentenceTransformer and CrossEncoder models during build time
ENV HF_HOME=/opt/huggingface_cache
RUN python -c "from sentence_transformers import SentenceTransformer, CrossEncoder; \
SentenceTransformer('all-MiniLM-L6-v2'); \
CrossEncoder('cross-encoder/nli-deberta-v3-base')"

# =====================================================================
# STAGE 2: Runner (Production)
# =====================================================================
FROM python:3.12-slim AS runner

WORKDIR /workspace

# Install minimal runtime libraries (curl for health check)
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create restricted non-root group and user
RUN groupadd -r appgroup && useradd -r -g appgroup -d /home/appuser -m appuser

# Copy virtual environment from builder stage
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy preloaded models from builder stage to appuser's home directory
COPY --from=builder /opt/huggingface_cache /home/appuser/.cache/huggingface
RUN chown -R appuser:appgroup /home/appuser/.cache/huggingface

# Set environment variables
ENV HF_HOME=/home/appuser/.cache/huggingface
ENV HF_HUB_OFFLINE=1
ENV TRANSFORMERS_OFFLINE=1
ENV PYTHONUNBUFFERED=1

# Copy application files
COPY --chown=appuser:appgroup . .

# Ensure data directory exists and is writable by appuser
RUN mkdir -p /workspace/data && chown -R appuser:appgroup /workspace/data

# Expose API port
EXPOSE 8000

# Docker Healthcheck calling /health
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Run container as non-root user
USER appuser

# Default command starts FastAPI through start script
CMD ["/bin/sh", "scripts/start.sh"]
