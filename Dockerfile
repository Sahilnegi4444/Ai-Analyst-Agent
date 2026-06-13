FROM python:3.12-slim

# Set working directory inside container
WORKDIR /workspace

# Install system dependencies for compilation (psycopg2-binary etc.)
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code files into the container
COPY . .

# Expose ports
EXPOSE 8000

# Default command to run the Uvicorn web server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
