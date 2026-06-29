# AI Analyst Agent Deployment Guide

This guide outlines how to deploy, configure, and run the AI Analyst Agent in both local test environments and cloud production settings. It provides instructions on database schemas, open-source embeddings, Redis caching, and front-end connection configurations.

---

## 1. System Architecture

The application is built on a decoupled architecture consisting of four main components:
1. **Frontend**: React + TypeScript + Vite SPA.
2. **Backend**: FastAPI web server orchestrating the agent workflows (SQL generation, RAG document similarity lookups, and Pandas calculations).
3. **Database**: PostgreSQL with the `pgvector` extension for structured business records and unstructured document embeddings.
4. **Caching & Queue**: Redis for fast response and SQL cache storage.

```
       +---------------------------------------------+
       |             User Web Browser                |
       +----------------------+----------------------+
                              |
                     HTTP Chat Requests
                              |
                              v
       +----------------------+----------------------+
       |                FastAPI App                  | <---> [ Groq Cloud API ]
       +---------+--------------------+--------------+
                 |                    |
          Structured SQL          Vector Query
                 |                    |
                 v                    v
       +---------+--------------------+--------------+
       |             PostgreSQL + pgvector           |
       +---------------------------------------------+
```

---

## 2. Environment Variables & Credentials

Create a `.env` file in the root directory. Ensure all sensitive values are injected as environment variables in production rather than hardcoded in files.

```ini
# Database Connection DSN
DATABASE_URL=postgresql://postgres:password@localhost:5432/ai_analyst_db

# Groq Cloud API Credentials (Required)
GROQ_API_KEY=gsk_your_api_key_here

# Embedding & Reranking Configuration
EMBEDDING_MODEL_NAME=all-MiniLM-L6-v2
RERANK_MODEL_NAME=cross-encoder/nli-deberta-v3-base

# Cache Server
REDIS_URL=redis://localhost:6379/0
REDIS_CACHE_TTL=3600

# Hugging Face Egress Control (Optional)
# If set to 1, the model loader expects weights to already exist in cache folder
HF_HUB_OFFLINE=0
TRANSFORMERS_OFFLINE=0
```

---

## 3. Local Deployment via Docker Compose

The easiest way to stand up the full stack (FastAPI Backend, PostgreSQL + pgvector Database, and Redis Cache) is to use Docker Compose.

### Step 1: Update Configuration
Ensure `docker-compose.yml` has the correct environment parameters:
```yaml
version: '3.8'

services:
  db:
    image: pgvector/pgvector:pg16
    container_name: ai_analyst_postgres
    restart: always
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: your_secure_password
      POSTGRES_DB: ai_analyst_db
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    container_name: ai_analyst_redis
    restart: always
    ports:
      - "6379:6379"

  web:
    build: .
    container_name: ai_analyst_backend
    restart: always
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:your_secure_password@db:5432/ai_analyst_db
      - GROQ_API_KEY=${GROQ_API_KEY}
      - REDIS_URL=redis://redis:6379/0
      - EMBEDDING_MODEL_NAME=all-MiniLM-L6-v2
    depends_on:
      - db
      - redis
    volumes:
      - .:/workspace

volumes:
  postgres_data:
```

### Step 2: Build and Run Services
Run the following command to start the DB, Redis, and Backend services:
```bash
# Pass the API key securely from your shell environment
export GROQ_API_KEY="your-actual-api-key"
docker-compose up --build -d
```

### Step 3: Run Migrations and Ingest Datasets
Once the containers are healthy, execute the database schema builder and data ingestion pipeline inside the backend container:
```bash
docker-compose exec web python scripts/ingest_all.py
```
This script will:
1. Verify database connectivity and create the `vector` extension.
2. Initialize tables based on the SQLAlchemy schema.
3. Import CSV datasets (suppliers, products, transactions, etc.) into the relational tables.
4. Extract text from the marketing policy PDFs, compute embedding vectors using `all-MiniLM-L6-v2`, and save the vectors to the pgvector document index.
5. Index database metadata for dynamic schema routing.

---

## 4. Production Deployment Guidelines

### Database Selection & Supabase Setup
- Avoid hosting PostgreSQL on a raw container in production.
- Use a managed cloud database service like **Supabase (PostgreSQL 15+ + pgvector)**:
  1. **Enable Vector Extension**: On the Supabase Dashboard, navigate to the SQL Editor and execute:
     ```sql
     CREATE EXTENSION IF NOT EXISTS vector WITH SCHEMA public;
     ```
  2. **Configure DATABASE_URL**: Retrieve your transaction-pooler connection string (usually port `6543`) from the Database Settings and set `DATABASE_URL` as an environment variable in Render or your production environment:
     ```ini
     DATABASE_URL=postgresql://postgres:[password]@aws-0-[region].pooler.supabase.com:6543/postgres?pgbouncer=true
     ```
  3. **Auto-Initialization**: The startup initialization logic has been optimized for managed clouds. It automatically runs a direct connection verification check first, bypassing the `CREATE DATABASE` queries which are restricted on Supabase.

### Upstash Redis Cache Setup
- **Configure REDIS_URL**: Retrieve your secure Redis connection DSN from the Upstash console. Ensure it uses the secure `rediss://` scheme:
  ```ini
  REDIS_URL=rediss://default:[token]@your-instance.upstash.io:6379/0
  ```
- **SSL & Retry Strategy**: The application automatically enforces SSL/TLS handshakes for `rediss://` targets and initiates connection retries using an exponential backoff strategy (up to 3 times).
- **Graceful Failure (Circuit Breaker)**: In case of database downtime or network timeouts, a runtime circuit breaker trips to disable Upstash calls and falls back dynamically to an in-memory cache to guarantee zero backend downtime.

### Packaging Hugging Face Models
To prevent containers from attempting to download PyTorch and model weights at startup (which creates high latency and risks download failures), bake the model weights into the container image:
```dockerfile
# Add to your production Dockerfile (uses model names from your config or defaults):
RUN python -c "import os; from sentence_transformers import SentenceTransformer, CrossEncoder; \
SentenceTransformer(os.getenv('EMBEDDING_MODEL_NAME', 'all-MiniLM-L6-v2')); \
CrossEncoder(os.getenv('RERANK_MODEL_NAME', 'cross-encoder/nli-deberta-v3-base'))"
```

### Frontend Builds
1. Navigate to the `frontend/` directory.
2. Configure your environment VITE variables:
   ```bash
   VITE_API_URL="https://api.yourdomain.com" npm run build
   ```
3. Deploy the compiled assets in the `dist/` directory to a static site host (AWS S3 + CloudFront, Vercel, or Nginx).
