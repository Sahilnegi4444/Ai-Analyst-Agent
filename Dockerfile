FROM python:3.12-slim

# Set working directory inside container
WORKDIR /workspace

# Install system dependencies for compilation
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set Hugging Face environment variables to cache models inside the container image
ENV HF_HOME=/root/.cache/huggingface
ENV PIP_NO_CACHE_DIR=1

# Copy requirements and install python packages (caching dependencies layer)
COPY requirements.txt .
RUN pip install -r requirements.txt

# Pre-download SentenceTransformer and CrossEncoder models during the build phase
# This prevents downloading model weights at runtime and speeds up startup times.
RUN python -c "from sentence_transformers import SentenceTransformer, CrossEncoder; \
    SentenceTransformer('all-MiniLM-L6-v2'); \
    CrossEncoder('cross-encoder/nli-deberta-v3-base')"

# Copy application source files
COPY . .

# Expose backend API port
EXPOSE 8000

# Ensure start script has executable permissions
RUN chmod +x scripts/start.sh

# Default command runs the container start script
CMD ["/bin/sh", "scripts/start.sh"]
