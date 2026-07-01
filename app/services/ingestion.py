import os
import pandas as pd
from pypdf import PdfReader
from sqlalchemy.orm import Session

from app.database import engine
from app.models import (
    Supplier, Product, Customer, MarketingCampaign, Inventory,
    InventoryHistory, SalesRecord, ReturnRecord, WarehouseEvent, Review, DocumentChunk
)
from app.services.embedding import EmbeddingService

class IngestionService:
    def __init__(self, db: Session):
        self.db = db
        self.embedding_service = EmbeddingService()

    def clean_tables(self):
        """Truncate all tables to allow clean re-runs of ingestion."""
        print("Truncating tables to clear previous runs...")
        # Order is critical due to foreign key constraints!
        tables_to_clear = [
            'document_chunks', 'reviews', 'returns', 'sales',
            'inventory_history', 'inventory', 'marketing_campaigns',
            'customers', 'products', 'suppliers', 'warehouse_events'
        ]
        connection = engine.connect()
        transaction = connection.begin()
        try:
            from sqlalchemy import text
            for table in tables_to_clear:
                connection.execute(text(f"TRUNCATE TABLE {table} CASCADE;"))
            transaction.commit()
            print("Successfully cleared all tables.")
        except Exception as e:
            transaction.rollback()
            print(f"Error during truncation: {e}")
            raise e
        finally:
            connection.close()

    def ingest_suppliers(self, csv_path: str):
        print("Ingesting suppliers...")
        df = pd.read_csv(csv_path)
        suppliers = []
        for _, row in df.iterrows():
            suppliers.append(Supplier(
                supplier_id=row['supplier_id'],
                supplier_name=row['supplier_name'],
                lead_time_days=int(row['lead_time_days']),
                country=row['country'],
                rating=float(row['rating'])
            ))
        self.db.add_all(suppliers)
        self.db.commit()
        print(f"Loaded {len(suppliers)} suppliers.")

    def ingest_products(self, csv_path: str):
        print("Ingesting products...")
        df = pd.read_csv(csv_path)
        products = []
        for _, row in df.iterrows():
            products.append(Product(
                product_id=row['product_id'],
                product_name=row['product_name'],
                category=row['category'],
                price=float(row['price']),
                cost=float(row['cost']),
                supplier_id=row['supplier_id']
            ))
        self.db.add_all(products)
        self.db.commit()
        print(f"Loaded {len(products)} products.")

    def ingest_customers(self, csv_path: str):
        print("Ingesting customers...")
        df = pd.read_csv(csv_path)
        customers = []
        for _, row in df.iterrows():
            customers.append(Customer(
                customer_id=row['customer_id'],
                name=row['name'],
                email=row['email'],
                signup_date=pd.to_datetime(row['signup_date']).date(),
                segment=row['segment'],
                gender=row['gender'],
                state=row['state'],
                city=row['city'],
                region=row['region']
            ))
        self.db.add_all(customers)
        self.db.commit()
        print(f"Loaded {len(customers)} customers.")

    def ingest_marketing_campaigns(self, csv_path: str):
        print("Ingesting marketing campaigns...")
        df = pd.read_csv(csv_path)
        campaigns = []
        for _, row in df.iterrows():
            campaigns.append(MarketingCampaign(
                campaign_id=row['campaign_id'],
                campaign_name=row['campaign_name'],
                start_date=pd.to_datetime(row['start_date']).date(),
                end_date=pd.to_datetime(row['end_date']).date(),
                discount_percent=float(row['discount_percent']),
                target_category=row['target_category']
            ))
        self.db.add_all(campaigns)
        self.db.commit()
        print(f"Loaded {len(campaigns)} marketing campaigns.")

    def ingest_inventory(self, csv_path: str):
        print("Ingesting inventory...")
        df = pd.read_csv(csv_path)
        inventory = []
        for _, row in df.iterrows():
            inventory.append(Inventory(
                product_id=row['product_id'],
                warehouse_location=row['warehouse_location'],
                current_stock=int(row['current_stock']),
                reorder_point=int(row['reorder_point']),
                reorder_quantity=int(row['reorder_quantity'])
            ))
        self.db.add_all(inventory)
        self.db.commit()
        print(f"Loaded {len(inventory)} current inventory records.")

    def ingest_inventory_history(self, csv_path: str):
        print("Ingesting inventory history...")
        df = pd.read_csv(csv_path)
        history = []
        for _, row in df.iterrows():
            history.append(InventoryHistory(
                product_id=row['product_id'],
                week_start_date=pd.to_datetime(row['week_start_date']).date(),
                stock_on_hand=int(row['stock_on_hand']),
                status=row['status']
            ))
        # Batch insert for speed
        self.db.add_all(history)
        self.db.commit()
        print(f"Loaded {len(history)} inventory history records.")

    def ingest_sales(self, csv_path: str):
        print("Ingesting sales (in batches)...")
        df = pd.read_csv(csv_path)
        
        # Batch loading for 50,000 records
        batch_size = 5000
        total_records = len(df)
        
        for start_idx in range(0, total_records, batch_size):
            end_idx = min(start_idx + batch_size, total_records)
            batch_df = df.iloc[start_idx:end_idx]
            
            sales_batch = []
            for _, row in batch_df.iterrows():
                sales_batch.append(SalesRecord(
                    transaction_id=row['transaction_id'],
                    transaction_date=pd.to_datetime(row['transaction_date']),
                    customer_id=row['customer_id'],
                    product_id=row['product_id'],
                    quantity=int(row['quantity']),
                    unit_price=float(row['unit_price']),
                    discount_applied=float(row['discount_applied']),
                    total_amount=float(row['total_amount']),
                    payment_method=row['payment_method']
                ))
            self.db.add_all(sales_batch)
            self.db.commit()
            print(f"Ingested sales records {start_idx} to {end_idx}...")
            
        print("Finished sales ingestion.")

    def ingest_returns(self, csv_path: str):
        print("Ingesting returns...")
        df = pd.read_csv(csv_path)
        returns = []
        for _, row in df.iterrows():
            returns.append(ReturnRecord(
                return_id=row['return_id'],
                transaction_id=row['transaction_id'],
                product_id=row['product_id'],
                return_date=pd.to_datetime(row['return_date']),
                reason=row['reason'],
                refund_amount=float(row['refund_amount'])
            ))
        self.db.add_all(returns)
        self.db.commit()
        print(f"Loaded {len(returns)} returns.")

    def ingest_warehouse_events(self, csv_path: str):
        print("Ingesting warehouse events...")
        df = pd.read_csv(csv_path)
        events = []
        for _, row in df.iterrows():
            events.append(WarehouseEvent(
                event_date=pd.to_datetime(row['event_date']).date(),
                event_name=row['event_name'],
                description=row['description']
            ))
        self.db.add_all(events)
        self.db.commit()
        print(f"Loaded {len(events)} warehouse events.")

    def ingest_reviews(self, csv_path: str):
        print("Ingesting product reviews...")
        df = pd.read_csv(csv_path)
        
        batch_size = 2000
        total_records = len(df)
        
        for start_idx in range(0, total_records, batch_size):
            end_idx = min(start_idx + batch_size, total_records)
            batch_df = df.iloc[start_idx:end_idx]
            
            reviews_batch = []
            for _, row in batch_df.iterrows():
                reviews_batch.append(Review(
                    review_id=row['review_id'],
                    customer_id=row['customer_id'],
                    product_id=row['product_id'],
                    rating=int(row['rating']),
                    review_text=row['review_text'],
                    review_date=pd.to_datetime(row['review_date'])
                ))
            self.db.add_all(reviews_batch)
            self.db.commit()
            print(f"Ingested reviews {start_idx} to {end_idx}...")
            
        print("Finished reviews ingestion.")

    def ingest_pdf_documents(self, doc_folder: str):
        print("Ingesting and embedding PDF business documents...")
        if not os.path.exists(doc_folder):
            print(f"Documents folder not found at {doc_folder}. Skipping PDF ingestion.")
            return

        pdf_files = [f for f in os.listdir(doc_folder) if f.endswith('.pdf')]
        
        for filename in pdf_files:
            file_path = os.path.join(doc_folder, filename)
            print(f"Processing PDF: {filename}...")
            
            reader = PdfReader(file_path)
            full_text = ""
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    full_text += text + "\n"
            
            # Paragraph-based chunking
            paragraphs = [p.strip() for p in full_text.split('\n\n') if p.strip()]
            
            chunks = []
            chunk_size_words = 150
            chunk_overlap_words = 30
            
            for p in paragraphs:
                words = p.split()
                if len(words) > chunk_size_words:
                    for i in range(0, len(words), chunk_size_words - chunk_overlap_words):
                        chunk = " ".join(words[i:i + chunk_size_words])
                        chunks.append(chunk)
                else:
                    chunks.append(p)
            
            # Embed and insert chunks
            title = filename.replace('.pdf', '').replace('_', ' ').title()
            db_chunks = []
            
            for idx, chunk_content in enumerate(chunks):
                # Generate embedding vector
                embedding = self.embedding_service.get_embedding(chunk_content)
                
                db_chunks.append(DocumentChunk(
                    filename=filename,
                    title=title,
                    chunk_index=idx,
                    content=chunk_content,
                    embedding=embedding
                ))
                
            self.db.add_all(db_chunks)
            self.db.commit()
            print(f"Loaded {len(db_chunks)} chunks for {filename}.")
            
        print("Finished PDF documents ingestion.")
