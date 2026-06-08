import os
import sys

# Add the workspace root to sys.path so we can import the app module
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.database import SessionLocal
from app.repositories import (
    SupplierRepository, ProductRepository, CustomerRepository,
    MarketingCampaignRepository, InventoryRepository, InventoryHistoryRepository,
    SalesRepository, ReturnRepository, WarehouseEventRepository,
    ReviewRepository, DocumentRepository
)
from app.services.embedding import EmbeddingService

def main():
    print("Starting database diagnostic verification...")
    db = SessionLocal()
    try:
        # Initialize repositories
        repos = {
            "Suppliers": SupplierRepository(db),
            "Products": ProductRepository(db),
            "Customers": CustomerRepository(db),
            "Campaigns": MarketingCampaignRepository(db),
            "Inventory": InventoryRepository(db),
            "InventoryHistory": InventoryHistoryRepository(db),
            "Sales": SalesRepository(db),
            "Returns": ReturnRepository(db),
            "Events": WarehouseEventRepository(db),
            "Reviews": ReviewRepository(db),
            "Documents": DocumentRepository(db)
        }

        # 1. Print row counts
        print("\n--- Database Row Counts ---")
        for name, repo in repos.items():
            count = repo.count()
            print(f"{name:18}: {count} records")

        # 2. Run a sample SQL analytical query: Top 3 products by revenue
        print("\n--- SQL Query Test: Top 3 Products by Revenue ---")
        from app.models import Product, SalesRecord
        from sqlalchemy import func
        
        top_products = (
            db.query(Product.product_name, func.sum(SalesRecord.total_amount).label('total_revenue'))
            .join(SalesRecord, Product.product_id == SalesRecord.product_id)
            .group_by(Product.product_name)
            .order_by(func.sum(SalesRecord.total_amount).desc())
            .limit(3)
            .all()
        )
        
        for idx, (name, rev) in enumerate(top_products, 1):
            print(f"{idx}. {name}: ${float(rev):,.2f}")

        # 3. Run a sample vector search query: RAG retrieval test
        print("\n--- pgvector Vector Similarity Search Test (Emulated) ---")
        query_text = "What is the procedure for inventory reordering and stockout prevention?"
        print(f"Query: '{query_text}'")
        
        # Get query embedding
        embed_service = EmbeddingService()
        query_vector = embed_service.get_embedding(query_text)
        
        # Search documents
        doc_repo = repos["Documents"]
        similar_chunks = doc_repo.search_similar(query_vector, limit=2)
        
        print(f"\nTop 2 matching document chunks:")
        for idx, (chunk, distance) in enumerate(similar_chunks, 1):
            print(f"\n[{idx}] Document: {chunk.filename} (Title: {chunk.title})")
            print(f"    Cosine Distance: {distance:.4f} (Similarity: {1.0 - distance:.4f})")
            print(f"    Content snippet: {chunk.content[:200]}...")

        print("\n==============================================")
        print("DATABASE DIAGNOSTIC VERIFICATION COMPLETED!")
        print("==============================================")

    except Exception as e:
        print(f"\n[ERROR] Verification failed: {e}")
        sys.exit(1)
    finally:
        db.close()

if __name__ == '__main__':
    main()
