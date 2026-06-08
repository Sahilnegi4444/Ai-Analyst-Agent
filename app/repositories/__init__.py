import numpy as np
from app.repositories.base import BaseRepository
from app.models import (
    Supplier, Product, Customer, MarketingCampaign, Inventory,
    InventoryHistory, SalesRecord, ReturnRecord, WarehouseEvent, Review, DocumentChunk
)
from sqlalchemy.orm import Session
from typing import List, Tuple

# =====================================================================
# SUPPLIER REPOSITORY
# =====================================================================
class SupplierRepository(BaseRepository[Supplier]):
    """
    Repository class handling CRUD operations for the Supplier entity.
    """
    def __init__(self, db: Session):
        super().__init__(Supplier, db)

# =====================================================================
# PRODUCT REPOSITORY
# =====================================================================
class ProductRepository(BaseRepository[Product]):
    """
    Repository class handling CRUD operations for the Product entity.
    """
    def __init__(self, db: Session):
        super().__init__(Product, db)

# =====================================================================
# CUSTOMER REPOSITORY
# =====================================================================
class CustomerRepository(BaseRepository[Customer]):
    """
    Repository class handling CRUD operations for the Customer entity.
    """
    def __init__(self, db: Session):
        super().__init__(Customer, db)

# =====================================================================
# MARKETING CAMPAIGN REPOSITORY
# =====================================================================
class MarketingCampaignRepository(BaseRepository[MarketingCampaign]):
    """
    Repository class handling CRUD operations for the MarketingCampaign entity.
    """
    def __init__(self, db: Session):
        super().__init__(MarketingCampaign, db)

# =====================================================================
# INVENTORY REPOSITORY
# =====================================================================
class InventoryRepository(BaseRepository[Inventory]):
    """
    Repository class handling CRUD operations for the Inventory entity.
    """
    def __init__(self, db: Session):
        super().__init__(Inventory, db)

# =====================================================================
# INVENTORY HISTORY REPOSITORY
# =====================================================================
class InventoryHistoryRepository(BaseRepository[InventoryHistory]):
    """
    Repository class handling CRUD operations for the InventoryHistory entity.
    """
    def __init__(self, db: Session):
        super().__init__(InventoryHistory, db)

# =====================================================================
# SALES REPOSITORY
# =====================================================================
class SalesRepository(BaseRepository[SalesRecord]):
    """
    Repository class handling CRUD operations for the SalesRecord entity.
    """
    def __init__(self, db: Session):
        super().__init__(SalesRecord, db)

# =====================================================================
# RETURN REPOSITORY
# =====================================================================
class ReturnRepository(BaseRepository[ReturnRecord]):
    """
    Repository class handling CRUD operations for the ReturnRecord entity.
    """
    def __init__(self, db: Session):
        super().__init__(ReturnRecord, db)

# =====================================================================
# WAREHOUSE EVENT REPOSITORY
# =====================================================================
class WarehouseEventRepository(BaseRepository[WarehouseEvent]):
    """
    Repository class handling CRUD operations for the WarehouseEvent entity.
    """
    def __init__(self, db: Session):
        super().__init__(WarehouseEvent, db)

# =====================================================================
# REVIEW REPOSITORY
# =====================================================================
class ReviewRepository(BaseRepository[Review]):
    """
    Repository class handling CRUD operations for the Review entity.
    """
    def __init__(self, db: Session):
        super().__init__(Review, db)

# =====================================================================
# DOCUMENT REPOSITORY (RAG RETRIEVAL)
# =====================================================================
class DocumentRepository(BaseRepository[DocumentChunk]):
    """
    Repository class handling operations for business document chunks.
    Implements local Python-based cosine similarity search using NumPy
    to search embeddings stored in the PostgreSQL database.
    """
    def __init__(self, db: Session):
        super().__init__(DocumentChunk, db)

    def search_similar(self, query_embedding: List[float], limit: int = 5) -> List[Tuple[DocumentChunk, float]]:
        """
        Retrieves similar document chunks by computing cosine similarity in Python.
        Avoids dependency on external pgvector extension for local database runs.
        
        Returns:
            List[Tuple[DocumentChunk, float]]: List of (chunk, cosine_distance) sorted by distance ascending.
        """
        # Fetch all chunks (this is extremely fast on small document catalogs)
        all_chunks = self.db.query(self.model).all()
        if not all_chunks:
            return []
            
        q_vec = np.array(query_embedding)
        q_norm = np.linalg.norm(q_vec)
        
        results = []
        for chunk in all_chunks:
            chunk_vec = np.array(chunk.embedding)
            chunk_norm = np.linalg.norm(chunk_vec)
            
            # Guard against zero-vector division
            if q_norm == 0 or chunk_norm == 0:
                similarity = 0.0
            else:
                # Cosine Similarity = (A . B) / (||A|| * ||B||)
                similarity = np.dot(q_vec, chunk_vec) / (q_norm * chunk_norm)
                
            # Cosine Distance = 1.0 - Cosine Similarity
            distance = 1.0 - float(similarity)
            results.append((chunk, distance))
            
        # Sort by distance ascending (closer to 0.0 is more similar)
        results.sort(key=lambda x: x[1])
        return results[:limit]
