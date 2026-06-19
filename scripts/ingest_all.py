import os
import sys
import psycopg2
import urllib.parse as urlparse
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from sqlalchemy import text

# Add the workspace root to sys.path so we can import the app module
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.config import settings
from app.database import engine, Base, SessionLocal
from app.services.ingestion import IngestionService
import app.models  # Ensure all models are imported for metadata creation

def ensure_database_exists():
    """
    Checks if the target database exists in the PostgreSQL cluster.
    If it does not exist, it will connect to the default 'postgres' database and create it.
    """
    print("Checking if target database exists...")
    # Parse connection details from DATABASE_URL
    url = urlparse.urlparse(settings.DATABASE_URL)
    target_db = url.path[1:]
    
    # Connect to the default 'postgres' database
    username = url.username or 'postgres'
    password = url.password or ''
    host = url.hostname or 'localhost'
    port = url.port or 5432
    
    postgres_dsn = f"postgresql://{username}:{password}@{host}:{port}/postgres"
    
    try:
        conn = psycopg2.connect(postgres_dsn)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Check if target db exists
        cursor.execute(f"SELECT 1 FROM pg_catalog.pg_database WHERE datname = '{target_db}';")
        exists = cursor.fetchone()
        
        if not exists:
            print(f"Database '{target_db}' does not exist. Creating database...")
            cursor.execute(f"CREATE DATABASE {target_db};")
            print(f"Database '{target_db}' created successfully.")
        else:
            print(f"Database '{target_db}' already exists.")
            
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"[ERROR] Failed to ensure database exists: {e}")
        raise e

def init_db():
    """
    Registers the pgvector extension and creates the database schema.
    """
    print("Initializing database schema...")
    # Enable pgvector extension
    with engine.connect() as conn:
        print("Enabling pgvector extension in the database...")
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
        conn.commit()
        
    # Create all tables defined in models
    print("Creating all tables...")
    Base.metadata.create_all(bind=engine)
    print("Database schema initialized successfully.")

def main():
    # 1. Ensure DB exists in the cluster
    ensure_database_exists()
    
    # 2. Create schema tables and extensions
    init_db()

    # 3. Ingest CSV data and PDF documents
    db = SessionLocal()
    try:
        ingestor = IngestionService(db)
        
        # Clear any existing data for a clean run
        ingestor.clean_tables()
        
        # Ingest CSV datasets (order matters due to foreign key constraints)
        ingestor.ingest_suppliers("data/suppliers.csv")
        ingestor.ingest_products("data/products.csv")
        ingestor.ingest_customers("data/customers.csv")
        ingestor.ingest_marketing_campaigns("data/marketing_campaigns.csv")
        ingestor.ingest_inventory("data/inventory.csv")
        ingestor.ingest_inventory_history("data/inventory_history.csv")
        ingestor.ingest_sales("data/sales.csv")
        ingestor.ingest_returns("data/returns.csv")
        ingestor.ingest_warehouse_events("data/warehouse_events.csv")
        ingestor.ingest_reviews("data/reviews.csv")
        
        # Ingest and embed PDF business documents for RAG
        ingestor.ingest_pdf_documents("data/documents")
        
        # Index database schemas for dynamic retrieval
        from app.services.schema_indexer import SchemaIndexer
        schema_indexer = SchemaIndexer(db)
        schema_indexer.index_schemas()
        
        print("\n==============================================")
        print("DATABASE INGESTION COMPLETED SUCCESSFULLY!")
        print("==============================================")
        
    except Exception as e:
        print(f"\n[ERROR] Ingestion failed: {e}")
        sys.exit(1)
    finally:
        db.close()

if __name__ == '__main__':
    main()
