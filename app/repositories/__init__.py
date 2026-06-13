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
    Implements SQL-based cosine similarity search using the pgvector extension.
    """
    def __init__(self, db: Session):
        super().__init__(DocumentChunk, db)

    def search_similar(self, query_embedding: List[float], limit: int = 5) -> List[Tuple[DocumentChunk, float]]:
        """
        Retrieves similar document chunks by executing a pgvector cosine distance search.
        
        Returns:
            List[Tuple[DocumentChunk, float]]: List of (chunk, cosine_distance) sorted by distance ascending.
        """
        results = (
            self.db.query(self.model, self.model.embedding.cosine_distance(query_embedding).label('distance'))
            .order_by('distance')
            .limit(limit)
            .all()
        )
        return [(r[0], float(r[1])) for r in results]
