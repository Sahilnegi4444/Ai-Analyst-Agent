# AI Analyst Agent Deployment & Operations Guide

This guide provides complete, step-by-step instructions to configure, run, and scale the AI Analyst Agent in both local development environments and production cloud environments.

---

## Table of Contents
1. [Environment Variables & Configuration](#1-environment-variables--configuration)
2. [Local Setup (Without Docker)](#2-local-setup-without-docker)
3. [Docker Setup (Local & Production)](#3-docker-setup-local--production)
4. [Groq Configuration](#4-groq-configuration)
5. [Supabase Configuration](#5-supabase-configuration)
6. [Upstash Configuration](#6-upstash-configuration)
7. [Render Deployment](#7-render-deployment)
8. [Railway Deployment](#8-railway-deployment)
9. [Vercel Deployment](#9-vercel-deployment)
10. [Common Deployment Issues & Troubleshooting](#10-common-deployment-issues--troubleshooting)
11. [Scaling Recommendations](#11-scaling-recommendations)

---

## 1. Environment Variables & Configuration

The application uses environment variables for all runtime settings. Below is the complete configuration matrix:

| Variable | Default Value | Description | Required |
| :--- | :--- | :--- | :--- |
| `DATABASE_URL` | `postgresql://analyst_user:analyst_password@localhost:5432/ai_analyst_db` | DSN for Postgres connection. Must include the `vector` extension. | **Yes** |
| `GROQ_API_KEY` | *(None)* | API token for Groq Cloud. | **Yes** |
| `REDIS_URL` | `redis://localhost:6379/0` | Cache DSN. Use `rediss://` for SSL/TLS (Upstash). | **Yes** |
| `ENVIRONMENT` | `development` | Environment environment identifier (`development` or `production`). | **Yes** (in Prod) |
| `EMBEDDING_MODEL_NAME` | `all-MiniLM-L6-v2` | Model name for text embedding generation. | No |
| `ENABLE_RERANKER` | `false` | Set to `true` to enable CrossEncoder reranking. Saves memory/CPU when `false`. | No |
| `RERANK_MODEL_NAME` | `cross-encoder/ettin-reranker-17m-v1` | Model name for CrossEncoder reranking. | No |
| `GROQ_ROUTER_MODEL` | `llama-3.1-8b-instant` | Groq model for intent routing. | No |
| `GROQ_SQL_MODEL` | `llama-3.1-8b-instant` | Groq model for text-to-SQL generation. | No |
| `GROQ_GENERATOR_MODEL` | `llama-3.3-70b-versatile` | Groq model for final business response synthesis. | No |
| `REDIS_CACHE_TTL` | `3600` | Caching time-to-live in seconds. | No |
| `INIT_DB` | `false` | Set to `true` to auto-initialize schemas on startup. | No |
| `AUTO_SEED` | `false` | Set to `true` to clear tables and re-ingest CSV/PDF datasets. | No |
| `WEB_CONCURRENCY` | `4` | Number of Gunicorn worker threads (production only). | No |

---

## 2. Local Setup (Without Docker)

Follow these steps to run the application directly on your local system:

### Prerequisites
* Python 3.12+
* Node.js 20+ & npm

### Backend Setup
1. Create a Python virtual environment and activate it:
   ```bash
   python -m venv venv
   # Windows:
   .\venv\Scripts\activate
   # Linux/macOS:
   source venv/bin/activate
   ```
2. Install all required dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Set up your local `.env` file containing credentials (see [Environment Variables](#1-environment-variables--configuration)).
4. Run the data ingestion and indexing pipeline to build tables and process RAG documents:
   ```bash
   python scripts/ingest_all.py
   ```
5. Start the local Uvicorn development server:
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

### Frontend Setup
1. Navigate to the `frontend/` folder:
   ```bash
   cd frontend
   ```
2. Install npm packages:
   ```bash
   npm install
   ```
3. Start the Vite React development server:
   ```bash
   npm run dev
   ```
4. Access the frontend dashboard in your browser at `http://localhost:5173`.

---

## 3. Docker Setup (Local & Production)

### Local Development (Docker Compose)
A preconfigured `docker-compose.yml` is provided at the root of the project to orchestrate a PostgreSQL (with `pgvector`), Redis, and FastAPI Backend stack locally:

1. Launch all services in the background:
   ```bash
   docker-compose up --build -d
   ```
2. Run database initialization and data seeding:
   ```bash
   docker-compose exec web python scripts/ingest_all.py
   ```
3. Tear down the local stack:
   ```bash
   docker-compose down -v
   ```

### Production Docker Container
The project uses a **multi-stage production Dockerfile** that optimizes layer caching, creates a non-root execution context, pre-caches model weights, and includes health check configurations:

* **Stage 1 (Builder)**: Installs build compilation tools (`gcc`, `libpq-dev`), downloads Python wheels into a virtual environment, and pre-caches the Hugging Face models so they do not attempt downloads at boot time.
* **Stage 2 (Runner)**: Uses `python:3.12-slim` containing only the dependencies and pre-cached models. The container runs under a restricted non-root user `appuser`.
* **Healthcheck**: Standard HTTP check runs against `/health`.

Build the production image locally or in CI:
```bash
docker build -t ai-analyst-backend:latest .
```

Run the production container:
```bash
docker run -d \
  -p 8000:8000 \
  -e ENVIRONMENT=production \
  -e DATABASE_URL="your-supabase-url" \
  -e REDIS_URL="your-upstash-url" \
  -e GROQ_API_KEY="your-groq-key" \
  --name ai-analyst-prod \
  ai-analyst-backend:latest
```

---

## 4. Groq Configuration

The AI Analyst Agent utilizes Groq Cloud APIs for instant inference across its workflows:

1. **Obtain an API Key**: Sign up at [console.groq.com](https://console.groq.com/) and generate an API key. Set it as `GROQ_API_KEY`.
2. **Model Selection**:
   * **Intent Routing & SQL Generation**: Standardized on `llama-3.1-8b-instant` due to its high speed (sub-200ms latency) and reliable JSON schema generation.
   * **Business Response Generation**: Standardized on `llama-3.3-70b-versatile` to synthesize high-quality, jargon-free business reports.
3. **Rate Limits & Failovers**:
   * If you hit rate limits (`429 Too Many Requests`), ensure you are running with response caching enabled on Upstash to prevent duplicate LLM calls for identical queries.

---

## 5. Supabase Configuration

To connect the application to **Supabase** (as a managed cloud database):

1. **Enable the Vector Extension**: 
   Open your Supabase project, go to **Database** (cylinder icon) > **Extensions**, search for `vector`, and enable it. Or run this SQL in the SQL Editor:
   ```sql
   CREATE EXTENSION IF NOT EXISTS vector WITH SCHEMA public;
   ```
2. **Retrieve Connection Pooling Connection String**:
   * Supabase provides a direct connection (port `5432`) and a Supavisor pooled connection (port `6543`).
   * For production, always use the **transaction-pooled connection string** (port `6543`) to manage concurrent backend requests.
   * Format:
     ```ini
     DATABASE_URL="postgresql://postgres.[project-ref]:[password]@aws-1-[region].pooler.supabase.com:6543/postgres?sslmode=require"
     ```
3. **Password URL Encoding**:
   * If your Supabase password contains special characters (like `@`, `#`, `/`), they **must** be URL-encoded in the DSN string (e.g., `@` becomes `%40`) to prevent SQLAlchemy parsing errors.
4. **Row Level Security (RLS)**:
   * To satisfy Supabase security recommendations, RLS should be enabled on all tables in the `public` schema.
   * Enable RLS on all tables:
     ```sql
     ALTER TABLE marketing_campaigns ENABLE ROW LEVEL SECURITY;
     -- Run for all tables: suppliers, products, customers, sales, returns, reviews, inventory, inventory_history, warehouse_events, document_chunks.
     ```
   * Allow the backend role (e.g., `developer` or `postgres`) to bypass RLS to run direct queries:
     ```sql
     ALTER ROLE developer BYPASSRLS;
     ```

---

## 6. Upstash Configuration

To configure **Upstash Redis** as a secure, managed cloud cache:

1. **Create Redis Database**: Create a serverless database instance in the Upstash console. Select TLS/SSL support.
2. **Configure connection DSN**: Set `REDIS_URL` using the secure `rediss://` protocol:
   ```ini
   REDIS_URL="rediss://default:[token]@your-instance.upstash.io:6379/0"
   ```
3. **Application Retries and Downtime Protection**:
   * The backend's [cache_service.py](file:///c:/Projects/Ai%20Analyst/app/services/cache_service.py) automatically runs connection retries with exponential backoff.
   * If Upstash suffers downtime or exceeds timeouts, the backend automatically activates a **circuit breaker**, falling back to a local in-memory cache to prevent user requests from failing.

---

## 7. Render Deployment

Render is a clean cloud platform to host the backend container. Instead of manual setup, we use Render **Blueprints** (`render.yaml`) to automate the infrastructure setup:

### Blueprint Deployment via `render.yaml`
1. Log into your Render dashboard and click **New > Blueprint**.
2. Connect your Git repository.
3. Render will parse the [render.yaml](file:///c:/Projects/Ai%20Analyst/render.yaml) file in the root of the project.
4. It will prompt you for the values of variables that do not have defaults:
   * `DATABASE_URL`: Your pooled Supabase DSN (with `sslmode=require`).
   * `GROQ_API_KEY`: Your Groq API Key.
   * `REDIS_URL`: Your Upstash Redis connection string.
5. Click **Approve** to create the service. Render will automatically build the Docker image, run the `/health` health check, and deploy the service.

### Disabling the Reranker for Free-Tier Deployment
To comfortably host the backend within Render's free tier (512MB RAM limit), the Reranker is disabled by default (`ENABLE_RERANKER=false`).
* This avoids loading the Deberta model into memory, reducing idle RAM usage from **~600MB+ to under 120MB**.
* Reranking can be re-enabled at any time by changing only the environment variable `ENABLE_RERANKER=true` under the Render service settings (without code changes).

### Frontend Deployment (Static Site)
1. Click **New > Static Site**.
2. Connect your Git repository.
3. Configure the build parameters:
   * **Build Command**: `cd frontend && npm install && npm run build`
   * **Publish Directory**: `frontend/dist`
4. Add the following environment variable:
   * `VITE_API_URL`: *(Your Render backend web service URL, e.g., `https://ai-analyst-backend.onrender.com`)*
5. Deploy the static site.


---

## 8. Railway Deployment

Railway supports fast container deployments from GitHub.

1. Log into Railway and click **New Project > Deploy from GitHub repo**.
2. Choose your repository.
3. Once the service is added, navigate to **Settings**:
   * Set **Custom Start Command** to: `sh scripts/start.sh` (or leave empty to let Dockerfile run it).
   * Set **Healthcheck Path** to `/health`.
4. Go to **Variables** and add:
   * `ENVIRONMENT`: `production`
   * `DATABASE_URL`: *(Your pooled Supabase DSN)*
   * `REDIS_URL`: *(Your Upstash Redis DSN)*
   * `GROQ_API_KEY`: *(Your Groq API Key)*
5. Railway will build your container and expose an automated domain.

---

## 9. Vercel Deployment

Vercel is optimal for hosting the frontend React Single Page Application (SPA).

1. Log into Vercel and click **Add New > Project**.
2. Connect your Git repository.
3. Configure project settings:
   * **Framework Preset**: `Vite`
   * **Root Directory**: `frontend`
4. Under **Environment Variables**, add:
   * `VITE_API_URL`: *(Your production backend URL)*
5. **SPA Router Configuration**:
   * Create a `vercel.json` file inside the `frontend/` directory to handle SPA history routes correctly:
     ```json
     {
       "rewrites": [{ "source": "/(.*)", "destination": "/index.html" }]
     }
     ```
6. Click **Deploy**.

---

## 10. Common Deployment Issues & Troubleshooting

### 1. Supabase Connection Blocked (`ECIRCUITBREAKER`)
* **Symptom**: `FATAL: (ECIRCUITBREAKER) too many authentication failures, new connections are temporarily blocked`.
* **Cause**: Multiple failed login attempts (often due to an unencoded database password in the DSN).
* **Fix**: Ensure your password is URL-encoded (using `%40` for `@`, etc.). Wait 5–10 minutes for Supabase's Supavisor pooler block to lift automatically.

### 2. ISP DNS Resolution Failures (NXDOMAIN)
* **Symptom**: Database hostname (e.g., `db.your-project.supabase.co`) fails to resolve with `getaddrinfo failed: Name or service not known` or `NXDOMAIN`.
* **Cause**: Major ISPs in certain regions (e.g. India) block `*.supabase.co` domains at the DNS level.
* **Fix**: Switch connection configurations to use the **Supavisor pooler hostname** (`aws-1-[region].pooler.supabase.com`), which uses the `.com` domain and bypasses ISP blocks.

### 3. Container Out Of Memory (OOM) Crashes
* **Symptom**: Container builds successfully but crashes instantly at startup with exit code `137` or `Killed`.
* **Cause**: Embedding and Reranking models (`SentenceTransformer`, `CrossEncoder`) load PyTorch model weights into RAM. Free cloud hosting tiers (like Render Free / 512MB RAM) will crash due to memory exhaustion.
* **Fix**: Ensure your cloud instance has a minimum of **1GB RAM** (preferably 2GB). Limit PyTorch CPU threads in your `.env`:
  ```ini
  OMP_NUM_THREADS=1
  MKL_NUM_THREADS=1
  ```

### 4. CORS Errors on Frontend
* **Symptom**: Console shows `Access-Control-Allow-Origin` header missing errors when frontend queries backend.
* **Fix**: Ensure you configure allowed origins in the backend `app/main.py` CORS middleware to include your production frontend URL (e.g. `https://your-app.vercel.app`).

---

## 11. Scaling Recommendations

To handle high concurrency and traffic loads in production:

### 1. Gunicorn Concurrency Tuning
Configure the number of web workers based on your container CPU allocation:
$$\text{Workers} = (2 \times \text{CPU Cores}) + 1$$
For a standard 2-core container, set `WEB_CONCURRENCY=5` in your environment variables. Each Gunicorn worker running Uvicorn threads can handle thousands of concurrent connections.

### 2. Database Connection Management
* **Transaction Pooling**: Always connect to Supabase port `6543` (transaction mode) rather than port `5432` (session mode) when scaling your application instances. Transaction pooling recycles database connections instantly, allowing thousands of application threads to share a small pool of database connections.
* **Pool Size Settings**: Set SQLAlchemy pool sizes in `app/database.py` (e.g. `pool_size=20`, `max_overflow=10`) to throttle backend connections.

### 3. Caching Optimization
* **Redis Eviction Policy**: Set Upstash Redis eviction policy to `volatile-lru` or `allkeys-lru` so that it automatically removes older cached responses when memory limits are reached.
* **Tuning TTLs**: Increase `REDIS_CACHE_TTL` (e.g., to 24h or 86400s) for slow-changing historical datasets (like 2025 sales data) to minimize database query execution costs and Groq API usage.
