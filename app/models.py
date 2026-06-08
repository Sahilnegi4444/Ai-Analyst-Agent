from sqlalchemy import Column, String, Integer, Numeric, Date, DateTime, ForeignKey, Text, Float
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import relationship
from app.database import Base

# =====================================================================
# SUPPLIER MODEL
# =====================================================================
class Supplier(Base):
    """
    SQLAlchemy model representing a product supplier.
    Contains vendor credentials, geographic location, and rating.
    """
    __tablename__ = 'suppliers'

    supplier_id = Column(String(10), primary_key=True)
    supplier_name = Column(String(100), nullable=False)
    lead_time_days = Column(Integer)
    country = Column(String(50))
    rating = Column(Numeric(3, 2))

    # Relationships
    # One supplier supplies multiple products
    products = relationship("Product", back_populates="supplier")


# =====================================================================
# PRODUCT MODEL
# =====================================================================
class Product(Base):
    """
    SQLAlchemy model representing items in the store catalog.
    Linked to a supplier and tracks price and costs.
    """
    __tablename__ = 'products'

    product_id = Column(String(10), primary_key=True)
    product_name = Column(String(100), nullable=False)
    category = Column(String(50))
    price = Column(Numeric(10, 2), nullable=False)
    cost = Column(Numeric(10, 2), nullable=False)
    supplier_id = Column(String(10), ForeignKey('suppliers.supplier_id'))

    # Relationships
    supplier = relationship("Supplier", back_populates="products")
    inventory = relationship("Inventory", uselist=False, back_populates="product")
    inventory_history = relationship("InventoryHistory", back_populates="product")
    sales = relationship("SalesRecord", back_populates="product")
    returns = relationship("ReturnRecord", back_populates="product")
    reviews = relationship("Review", back_populates="product")


# =====================================================================
# CUSTOMER MODEL
# =====================================================================
class Customer(Base):
    """
    SQLAlchemy model representing the customer registry.
    Contains segment details and demographics.
    """
    __tablename__ = 'customers'

    customer_id = Column(String(10), primary_key=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    signup_date = Column(Date)
    segment = Column(String(20))
    gender = Column(String(10))
    state = Column(String(10))
    city = Column(String(50))
    region = Column(String(20))

    # Relationships
    sales = relationship("SalesRecord", back_populates="customer")
    reviews = relationship("Review", back_populates="customer")


# =====================================================================
# MARKETING CAMPAIGN MODEL
# =====================================================================
class MarketingCampaign(Base):
    """
    SQLAlchemy model representing promotional business campaigns.
    Defines targeted categories and dynamic discounts.
    """
    __tablename__ = 'marketing_campaigns'

    campaign_id = Column(String(10), primary_key=True)
    campaign_name = Column(String(100), nullable=False)
    start_date = Column(Date)
    end_date = Column(Date)
    discount_percent = Column(Numeric(4, 2))
    target_category = Column(String(50))


# =====================================================================
# INVENTORY MODEL
# =====================================================================
class Inventory(Base):
    """
    SQLAlchemy model representing current warehouse stock status.
    One-to-one relationship with Product.
    """
    __tablename__ = 'inventory'

    product_id = Column(String(10), ForeignKey('products.product_id'), primary_key=True)
    warehouse_location = Column(String(50))
    current_stock = Column(Integer)
    reorder_point = Column(Integer)
    reorder_quantity = Column(Integer)

    # Relationships
    product = relationship("Product", back_populates="inventory")


# =====================================================================
# INVENTORY HISTORY MODEL
# =====================================================================
class InventoryHistory(Base):
    """
    SQLAlchemy model tracking weekly inventory levels over time.
    Critical for identifying historical stockouts.
    """
    __tablename__ = 'inventory_history'

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(String(10), ForeignKey('products.product_id'), nullable=False)
    week_start_date = Column(Date, nullable=False)
    stock_on_hand = Column(Integer, nullable=False)
    status = Column(String(20))

    # Relationships
    product = relationship("Product", back_populates="inventory_history")


# =====================================================================
# SALES RECORD MODEL
# =====================================================================
class SalesRecord(Base):
    """
    SQLAlchemy model for retail sales transactions.
    Tracks purchase details, unit prices, discounts, and payment methods.
    """
    __tablename__ = 'sales'

    transaction_id = Column(String(10), primary_key=True)
    transaction_date = Column(DateTime, nullable=False)
    customer_id = Column(String(10), ForeignKey('customers.customer_id'), nullable=False)
    product_id = Column(String(10), ForeignKey('products.product_id'), nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Numeric(10, 2), nullable=False)
    discount_applied = Column(Numeric(4, 2), default=0.0)
    total_amount = Column(Numeric(10, 2), nullable=False)
    payment_method = Column(String(20))

    # Relationships
    customer = relationship("Customer", back_populates="sales")
    product = relationship("Product", back_populates="sales")
    returns = relationship("ReturnRecord", back_populates="sales_record")


# =====================================================================
# RETURN RECORD MODEL
# =====================================================================
class ReturnRecord(Base):
    """
    SQLAlchemy model tracking product returns and refunds.
    """
    __tablename__ = 'returns'

    return_id = Column(String(10), primary_key=True)
    transaction_id = Column(String(10), ForeignKey('sales.transaction_id'), nullable=False)
    product_id = Column(String(10), ForeignKey('products.product_id'), nullable=False)
    return_date = Column(DateTime, nullable=False)
    reason = Column(String(100))
    refund_amount = Column(Numeric(10, 2), nullable=False)

    # Relationships
    sales_record = relationship("SalesRecord", back_populates="returns")
    product = relationship("Product", back_populates="returns")


# =====================================================================
# WAREHOUSE EVENT MODEL
# =====================================================================
class WarehouseEvent(Base):
    """
    SQLAlchemy model logging logistical bottlenecks or events in the warehouse.
    """
    __tablename__ = 'warehouse_events'

    id = Column(Integer, primary_key=True, autoincrement=True)
    event_date = Column(Date, nullable=False)
    event_name = Column(String(100), nullable=False)
    description = Column(Text)


# =====================================================================
# REVIEW MODEL
# =====================================================================
class Review(Base):
    """
    SQLAlchemy model representing customer ratings and text reviews for products.
    """
    __tablename__ = 'reviews'

    review_id = Column(String(10), primary_key=True)
    customer_id = Column(String(10), ForeignKey('customers.customer_id'), nullable=False)
    product_id = Column(String(10), ForeignKey('products.product_id'), nullable=False)
    rating = Column(Integer, nullable=False)
    review_text = Column(Text)
    review_date = Column(DateTime, nullable=False)

    # Relationships
    customer = relationship("Customer", back_populates="reviews")
    product = relationship("Product", back_populates="reviews")


# =====================================================================
# DOCUMENT CHUNK MODEL (FOR RAG SYSTEM)
# =====================================================================
class DocumentChunk(Base):
    """
    SQLAlchemy model representing parsed and chunked business documents.
    Stores native float array embeddings to allow flexible similarity search
    without requiring third-party PostgreSQL extensions (like pgvector) during local dev.
    """
    __tablename__ = 'document_chunks'

    id = Column(Integer, primary_key=True, autoincrement=True)
    filename = Column(String(100), nullable=False)
    title = Column(String(200), nullable=False)
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    # Storing embeddings natively as PostgreSQL array of floats (dimension 384)
    embedding = Column(ARRAY(Float), nullable=False)
