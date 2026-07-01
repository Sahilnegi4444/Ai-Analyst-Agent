from sqlalchemy.orm import Session
from app.models import DocumentChunk
from app.services.embedding import EmbeddingService

TABLE_SCHEMAS = {
    "customers": {
        "description": "Registry of customers containing their unique customer_id, name, email, signup date, segment details (Standard, Premium, VIP), gender, city, state, and region (North, South, East, West). Useful for customer demographics, segments, signup trends, and customer lookup.",
        "schema_text": """Table: customers
Columns:
- customer_id: VARCHAR(10) PRIMARY KEY (Format: C0001 - C5000)
- name: VARCHAR(100)
- email: VARCHAR(100) UNIQUE
- signup_date: DATE (when the customer joined)
- segment: VARCHAR(20) (Standard, Premium, VIP)
- gender: VARCHAR(10) (M, F, O)
- state: VARCHAR(10) (e.g. NY, CA, TX, IL, FL, WA, MA, CO)
- city: VARCHAR(50)
- region: VARCHAR(20) (North, South, East, West)"""
    },
    "suppliers": {
        "description": "Supplier catalog details including supplier name, geographical country location, delivery lead times in days, and rating (1.00 to 5.00). Useful for supply chain, rating comparisons, and lead time analysis.",
        "schema_text": """Table: suppliers
Columns:
- supplier_id: VARCHAR(10) PRIMARY KEY (Format: S01 - S10)
- supplier_name: VARCHAR(100)
- lead_time_days: INTEGER (replenishment latency)
- country: VARCHAR(50)
- rating: NUMERIC(3,2) (1.00 to 5.00)"""
    },
    "products": {
        "description": "Store product catalog mapping product names, pricing, production cost, categories (Electronics, Apparel, Home & Kitchen, Beauty, Sports), and their supplier_id. Useful for product details, pricing, profit margins, cost analysis, and product counts.",
        "schema_text": """Table: products
Columns:
- product_id: VARCHAR(10) PRIMARY KEY (Format: P001 - P100)
- product_name: VARCHAR(100) ("Product A" is P001)
- category: VARCHAR(50) (Electronics, Apparel, Home & Kitchen, Beauty, Sports)
- price: NUMERIC(10,2) (selling price)
- cost: NUMERIC(10,2) (production cost / purchase cost)
- supplier_id: VARCHAR(10) FOREIGN KEY references suppliers(supplier_id)"""
    },
    "marketing_campaigns": {
        "description": "Business promotional marketing campaigns including start and end dates, targeted product categories (e.g. Apparel, Home & Kitchen, Electronics, All), and discount percentages. Useful for checking current campaigns, active dates, and target discounts.",
        "schema_text": """Table: marketing_campaigns
Columns:
- campaign_id: VARCHAR(10) PRIMARY KEY (Format: MC001 - MC005)
- campaign_name: VARCHAR(100)
- start_date: DATE
- end_date: DATE
- discount_percent: NUMERIC(4,2) (discount fraction, e.g. 0.20 for 20%)
- target_category: VARCHAR(50) (Apparel, Home & Kitchen, All, Electronics)"""
    },
    "inventory": {
        "description": "Warehouse current physical stock levels per product, warehouse location (WH-East, WH-West, WH-Central), reorder points, and standard reorder quantities. Useful for real-time inventory health, low stock checks, and replenishment limits.",
        "schema_text": """Table: inventory
Columns:
- product_id: VARCHAR(10) PRIMARY KEY FOREIGN KEY references products(product_id)
- warehouse_location: VARCHAR(50) (WH-East, WH-West, WH-Central)
- current_stock: INTEGER (today's physical stock)
- reorder_point: INTEGER
- reorder_quantity: INTEGER"""
    },
    "inventory_history": {
        "description": "Historical weekly inventory levels tracking week_start_date (Sundays of 2025), stock_on_hand levels, and low stock status (In Stock, Low Stock, Out of Stock). Useful for checking historical inventory trends, stockout dates, and status changes.",
        "schema_text": """Table: inventory_history
Columns:
- id: INTEGER PRIMARY KEY (Auto-increment)
- product_id: VARCHAR(10) FOREIGN KEY references products(product_id)
- week_start_date: DATE (Sundays of 2025)
- stock_on_hand: INTEGER (stock level during that week)
- status: VARCHAR(20) (In Stock, Low Stock, Out of Stock - P001 is Out of Stock in March 2025)"""
    },
    "sales": {
        "description": "Customer retail sales transactions log recording transaction date, quantities, unit prices, discounts applied, total amount, customer_id, product_id, and payment method (Credit Card, PayPal, Debit Card, Cash). Useful for revenue, sales volumes, MoM trends, transaction counts, payments, and product orders.",
        "schema_text": """Table: sales
Columns:
- transaction_id: VARCHAR(10) PRIMARY KEY (Format: T00001 - T50000)
- transaction_date: TIMESTAMP (dates throughout 2025)
- customer_id: VARCHAR(10) FOREIGN KEY references customers(customer_id)
- product_id: VARCHAR(10) FOREIGN KEY references products(product_id)
- quantity: INTEGER (1 - 5)
- unit_price: NUMERIC(10,2) (price at purchase)
- discount_applied: NUMERIC(4,2) (e.g. 0.20)
- total_amount: NUMERIC(10,2) (calculated: quantity * unit_price * (1 - discount))
- payment_method: VARCHAR(20) (Credit Card, PayPal, Debit Card, Cash)"""
    },
    "returns": {
        "description": "Product return and refund transactions recording return date, product_id, original transaction_id, refund amount, and reason for return (e.g. Defective, Changed Mind, Incorrect Size, Damaged in Transit, Did Not Fit). Useful for tracking customer refunds, defect rates, and return reasons.",
        "schema_text": """Table: returns
Columns:
- return_id: VARCHAR(10) PRIMARY KEY (Format: R00001 - R02000)
- transaction_id: VARCHAR(10) FOREIGN KEY references sales(transaction_id)
- product_id: VARCHAR(10) FOREIGN KEY references products(product_id)
- return_date: TIMESTAMP (occurs after transaction_date)
- reason: VARCHAR(100) (Defective, Changed Mind, Incorrect Size, Damaged in Transit, Did Not Fit)
- refund_amount: NUMERIC(10,2)"""
    },
    "warehouse_events": {
        "description": "Logs of logistical warehouse events and delays, noting the event date, name, and textual description (e.g. Warehouse Delays, weather issues, port bottlenecks). Useful for explaining drops in stock or sales delays.",
        "schema_text": """Table: warehouse_events
Columns:
- id: INTEGER PRIMARY KEY (Auto-increment)
- event_date: DATE (e.g. 2025-03-05 is Warehouse A Delay)
- event_name: VARCHAR(100)
- description: TEXT"""
    },
    "reviews": {
        "description": "Customer feedback reviews and numerical ratings (1-5 stars) linked to customer_id and product_id, with review date and text reviews. Useful for sentiment analysis, customer satisfaction, and product rating metrics.",
        "schema_text": """Table: reviews
Columns:
- review_id: VARCHAR(10) PRIMARY KEY (Format: REV00001 - REV05000)
- customer_id: VARCHAR(10) FOREIGN KEY references customers(customer_id)
- product_id: VARCHAR(10) FOREIGN KEY references products(product_id)
- rating: INTEGER (1 - 5)
- review_text: TEXT
- review_date: TIMESTAMP (occurs after transaction_date)"""
    }
}

class SchemaIndexer:
    """
    Handles indexing database table schema metadata into pgvector
    and dynamically retrieving relevant schemas based on natural language queries.
    """
    def __init__(self, db: Session):
        self.db = db
        self.embedding_service = EmbeddingService()

    def index_schemas(self):
        """Indexes all table schemas and their descriptions into the document chunks table."""
        print("Clearing old schema index metadata...")
        self.db.query(DocumentChunk).filter(DocumentChunk.filename == "database_schema.json").delete()
        self.db.commit()

        print("Indexing database schemas as vector chunks...")
        db_chunks = []
        for idx, (table_name, info) in enumerate(TABLE_SCHEMAS.items()):
            content_to_embed = f"Table: {table_name}. Description: {info['description']}"
            embedding = self.embedding_service.get_embedding(content_to_embed)
            
            db_chunks.append(DocumentChunk(
                filename="database_schema.json",
                title=f"Table: {table_name}",
                chunk_index=idx,
                content=info["schema_text"],
                embedding=embedding
            ))
            
        self.db.add_all(db_chunks)
        self.db.commit()
        print(f"Indexed {len(db_chunks)} table schemas successfully.")

    def retrieve_relevant_schemas(self, query: str, top_n: int = 4) -> str:
        """Retrieves and formats table schemas relevant to the query."""
        import re
        query_lower = query.lower()
        
        # 1. Run keyword heuristics to identify tables to force-include
        keyword_map = {
            "sales": ["sale", "sales", "sold", "revenue", "transaction", "transactions", "amount", "quantity", "quarter", "month", "year", "date", "payment", "buy", "bought", "purchase", "spend", "income"],
            "products": ["product", "products", "item", "items", "category", "price", "cost", "margin", "profit"],
            "customers": ["customer", "customers", "vip", "segment", "signup", "gender", "state", "city", "region", "who", "demographic", "people"],
            "inventory": ["inventory", "stock", "warehouse", "reorder", "current_stock"],
            "inventory_history": ["inventory history", "historical stock", "stock history", "stock level", "weekly stock"],
            "suppliers": ["supplier", "suppliers", "lead time", "rating", "country"],
            "returns": ["return", "returns", "refund", "refunds", "reason", "damaged", "defective", "did not fit"],
            "marketing_campaigns": ["campaign", "campaigns", "discount", "discounts", "marketing", "promo", "offer", "percent"],
            "warehouse_events": ["event", "events", "delay", "delays", "bottleneck", "bottlenecks", "incident", "disruption"],
            "reviews": ["review", "reviews", "rating", "ratings", "feedback", "comment", "comments", "star", "sentiment"]
        }
        
        force_tables = set()
        for table, keywords in keyword_map.items():
            for kw in keywords:
                pattern = rf"\b{kw}\b"
                if re.search(pattern, query_lower):
                    force_tables.add(table)
                    break

        # 2. Get vector search results for the query
        query_vector = self.embedding_service.get_embedding(query)
        results = (
            self.db.query(DocumentChunk, DocumentChunk.embedding.cosine_distance(query_vector).label('distance'))
            .filter(DocumentChunk.filename == "database_schema.json")
            .order_by('distance')
            .all()
        )
        
        # 3. Build the final list of schemas, prioritizing force-included tables
        selected_schemas = []
        selected_table_names = set()
        
        # Add force-included tables first
        for chunk, _ in results:
            table_name = chunk.title.replace("Table: ", "").strip()
            if table_name in force_tables:
                selected_schemas.append(chunk.content)
                selected_table_names.add(table_name)
                
        # Fill remaining slots with the closest remaining vector results
        for chunk, _ in results:
            table_name = chunk.title.replace("Table: ", "").strip()
            if table_name not in selected_table_names:
                if len(selected_schemas) < max(top_n, len(force_tables)):
                    selected_schemas.append(chunk.content)
                    selected_table_names.add(table_name)
                    
        # Limit to a maximum of 5 tables to keep context compact but complete
        selected_schemas = selected_schemas[:5]
        
        return "\n\n".join(selected_schemas)
