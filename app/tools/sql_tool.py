import re
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.providers.llm import GroqLLMProvider
from app.config import settings

# =####################################################################
# DATABASE SCHEMA SPECIFICATION
# #####################################################################
DB_SCHEMA = """
Table: customers
Columns:
- customer_id: VARCHAR(10) PRIMARY KEY (Format: C0001 - C5000)
- name: VARCHAR(100)
- email: VARCHAR(100) UNIQUE
- signup_date: DATE (when the customer joined)
- segment: VARCHAR(20) (Standard, Premium, VIP)
- gender: VARCHAR(10) (M, F, O)
- state: VARCHAR(10) (e.g. NY, CA, TX, IL, FL, WA, MA, CO)
- city: VARCHAR(50)
- region: VARCHAR(20) (North, South, East, West)

Table: suppliers
Columns:
- supplier_id: VARCHAR(10) PRIMARY KEY (Format: S01 - S10)
- supplier_name: VARCHAR(100)
- lead_time_days: INTEGER (replenishment latency)
- country: VARCHAR(50)
- rating: NUMERIC(3,2) (1.00 to 5.00)

Table: products
Columns:
- product_id: VARCHAR(10) PRIMARY KEY (Format: P001 - P100)
- product_name: VARCHAR(100) ("Product A" is P001)
- category: VARCHAR(50) (Electronics, Apparel, Home & Kitchen, Beauty, Sports)
- price: NUMERIC(10,2) (selling price)
- cost: NUMERIC(10,2) (production cost / purchase cost)
- supplier_id: VARCHAR(10) FOREIGN KEY references suppliers(supplier_id)

Table: marketing_campaigns
Columns:
- campaign_id: VARCHAR(10) PRIMARY KEY (Format: MC001 - MC005)
- campaign_name: VARCHAR(100)
- start_date: DATE
- end_date: DATE
- discount_percent: NUMERIC(4,2) (discount fraction, e.g. 0.20 for 20%)
- target_category: VARCHAR(50) (Apparel, Home & Kitchen, All, Electronics)

Table: inventory
Columns:
- product_id: VARCHAR(10) PRIMARY KEY FOREIGN KEY references products(product_id)
- warehouse_location: VARCHAR(50) (WH-East, WH-West, WH-Central)
- current_stock: INTEGER (today's physical stock)
- reorder_point: INTEGER
- reorder_quantity: INTEGER

Table: inventory_history
Columns:
- id: INTEGER PRIMARY KEY (Auto-increment)
- product_id: VARCHAR(10) FOREIGN KEY references products(product_id)
- week_start_date: DATE (Sundays of 2025)
- stock_on_hand: INTEGER (stock level during that week)
- status: VARCHAR(20) (In Stock, Low Stock, Out of Stock - P001 is Out of Stock in March 2025)

Table: sales
Columns:
- transaction_id: VARCHAR(10) PRIMARY KEY (Format: T00001 - T50000)
- transaction_date: TIMESTAMP (dates throughout 2025)
- customer_id: VARCHAR(10) FOREIGN KEY references customers(customer_id)
- product_id: VARCHAR(10) FOREIGN KEY references products(product_id)
- quantity: INTEGER (1 - 5)
- unit_price: NUMERIC(10,2) (price at purchase)
- discount_applied: NUMERIC(4,2) (e.g. 0.20)
- total_amount: NUMERIC(10,2) (calculated: quantity * unit_price * (1 - discount))
- payment_method: VARCHAR(20) (Credit Card, PayPal, Debit Card, Cash)

Table: returns
Columns:
- return_id: VARCHAR(10) PRIMARY KEY (Format: R00001 - R02000)
- transaction_id: VARCHAR(10) FOREIGN KEY references sales(transaction_id)
- product_id: VARCHAR(10) FOREIGN KEY references products(product_id)
- return_date: TIMESTAMP (occurs after transaction_date)
- reason: VARCHAR(100) (Defective, Changed Mind, Incorrect Size, Damaged in Transit, Did Not Fit)
- refund_amount: NUMERIC(10,2)

Table: warehouse_events
Columns:
- id: INTEGER PRIMARY KEY (Auto-increment)
- event_date: DATE (e.g. 2025-03-05 is Warehouse A Delay)
- event_name: VARCHAR(100)
- description: TEXT

Table: reviews
Columns:
- review_id: VARCHAR(10) PRIMARY KEY (Format: REV00001 - REV05000)
- customer_id: VARCHAR(10) FOREIGN KEY references customers(customer_id)
- product_id: VARCHAR(10) FOREIGN KEY references products(product_id)
- rating: INTEGER (1 - 5)
- review_text: TEXT
- review_date: TIMESTAMP (occurs after transaction_date)
"""

class SQLTool:
    """
    Tool responsible for generating safe, read-only SQL queries from user questions,
    validating syntax via dry-runs, and returning structured database records.
    Uses dynamic schema retrieval and SQL statement caching.
    """
    def __init__(self, db: Session):
        self.db = db
        self.client = GroqLLMProvider()
        self.model = settings.GROQ_SQL_MODEL
        self.prompt_tokens = 0
        self.completion_tokens = 0

    def execute_query(self, user_question: str) -> dict:
        """
        Generates and executes a SQL query to answer the user question.
        Check cache first to skip LLM generation on cache hit.
        """
        from app.services.cache_service import RedisCacheService
        cache_service = RedisCacheService()
        
        # 1. Try to get SQL query from Redis Cache
        cached_sql = cache_service.get_cached_sql(user_question)
        is_cached = False
        
        if cached_sql:
            sql_query = cached_sql
            print(f"[SQL CACHE HIT] SQL query served from cache: {sql_query}")
            is_cached = True
        else:
            # Generate SQL query via Groq LLM
            sql_query = self._generate_sql(user_question)
            print(f"Generated SQL: {sql_query}")

        # 2. Safety check: Guard against modifying commands
        if not self._is_read_only(sql_query):
            print("[SECURITY BLOCK] Query rejected. Modification attempted.")
            return {
                "sql_query": sql_query,
                "status": "security_violation",
                "error": "Security Violation: Database modification (DROP, DELETE, UPDATE, ALTER, TRUNCATE, INSERT, CREATE) is strictly prohibited.",
                "results": None,
                "prompt_tokens": self.prompt_tokens,
                "completion_tokens": self.completion_tokens,
                "cached": False
            }

        # 3. Dry-run syntax validation using EXPLAIN
        syntax_ok, error_msg = self._validate_syntax(sql_query)
        if not syntax_ok:
            # Self-correct attempt (once)
            print(f"Syntax validation failed. Attempting self-correction. Error: {error_msg}")
            sql_query = self._generate_sql(user_question, syntax_error=error_msg)
            print(f"Self-corrected SQL: {sql_query}")
            
            # Re-run safety and validation
            if not self._is_read_only(sql_query):
                return {
                    "sql_query": sql_query,
                    "status": "security_violation",
                    "error": "Security Violation: Database modification attempted after self-correction.",
                    "results": None,
                    "prompt_tokens": self.prompt_tokens,
                    "completion_tokens": self.completion_tokens,
                    "cached": False
                }
            syntax_ok, error_msg = self._validate_syntax(sql_query)
            if not syntax_ok:
                return {
                    "sql_query": sql_query,
                    "status": "syntax_error",
                    "error": f"SQL Syntax Validation Failed: {error_msg}",
                    "results": None,
                    "prompt_tokens": self.prompt_tokens,
                    "completion_tokens": self.completion_tokens,
                    "cached": False
                }

        # Cache successful generated SQL
        if not is_cached:
            cache_service.set_cached_sql(user_question, sql_query)

        # 4. Execute the query
        try:
            result = self.db.execute(text(sql_query))
            import datetime
            from decimal import Decimal
            rows = []
            for row in result:
                row_dict = {}
                for key, val in row._mapping.items():
                    if isinstance(val, (datetime.datetime, datetime.date)):
                        row_dict[key] = val.isoformat()
                    elif isinstance(val, Decimal):
                        row_dict[key] = float(val)
                    else:
                        row_dict[key] = val
                rows.append(row_dict)
            return {
                "sql_query": sql_query,
                "status": "success",
                "results": rows,
                "prompt_tokens": self.prompt_tokens,
                "completion_tokens": self.completion_tokens,
                "cached": is_cached,
                "error": None
            }
        except Exception as e:
            try:
                self.db.rollback()
            except Exception:
                pass
            return {
                "sql_query": sql_query,
                "status": "execution_failed",
                "error": f"Execution Error: {e}",
                "prompt_tokens": self.prompt_tokens,
                "completion_tokens": self.completion_tokens,
                "cached": is_cached,
                "results": None
            }

    def _generate_sql(self, question: str, syntax_error: str = None) -> str:
        """Sends prompt to Groq using dynamic schema retrieval."""
        from app.services.schema_indexer import SchemaIndexer
        
        system_prompt = (
            "You are a PostgreSQL expert database analyst. Your task is to output a clean, "
            "syntactically correct PostgreSQL SELECT statement to answer the user's question.\n"
            "Constraints:\n"
            "- Only write SELECT statements.\n"
            "- Never perform DROP, DELETE, UPDATE, INSERT, ALTER, or CREATE operations.\n"
            "- You must return EXACTLY ONE single SELECT statement. Do NOT output multiple SELECT statements or separate queries. Under no circumstances should you separate queries by newlines, whitespace, or semicolons.\n"
            "- Do NOT use UNION or UNION ALL to combine multiple separate queries with different columns or schemas. If the user asks for multiple breakdowns (such as both overall sales and top products), write a single SELECT statement grouped by the primary entity (e.g. product_name) containing the aggregate columns so that all answers can be derived from one tabular dataset.\n"
            "- Do not try to answer parts of the question that ask for rules, guidelines, policies, contracts, or SOPs (such as 'campaign rules') by querying database tables. Those must be ignored here as they are handled by the document search (RAG) system. Focus the SELECT statement strictly on the structured numerical metrics (e.g. sales, quantity, product sales) requested in the query.\n"
            "- Output ONLY the raw SQL query. Do not wrap in markdown (like ```sql) or include explanations.\n"
            "- Ignore parts of the user question that request general company policies, SOPs, rules, procedures, handbooks, or contracts. Those are handled by a separate document search system. Only write SELECT queries for structured database lookups (sales, transactions, products, inventory tables).\n"
            "- In PostgreSQL, column aliases created in the SELECT list cannot be used inside mathematical or logical expressions in the ORDER BY clause (e.g. 'ORDER BY september_sales - february_sales' will fail with an UndefinedColumn error). Instead, repeat the full aggregate expressions (e.g. 'ORDER BY SUM(...) - SUM(...)') or use a CTE/subquery to wrap the select and then order the outer query.\n"
            "- If you select both aggregated values (e.g., SUM(quantity)) and non-aggregated columns (e.g., product_name), you MUST include a GROUP BY clause containing all non-aggregated columns. Failure to do so will result in a database error.\n"
            "- If you reference columns that belong to different tables (such as product_name from products and total_amount/quantity/customer_id from sales), you MUST perform an explicit JOIN (e.g., JOIN sales s ON p.product_id = s.product_id). Never query a column from a table unless it is explicitly listed under that table's columns in the schema.\n"
            "- Database sales and history transaction data is strictly from the year 2025. Do NOT use CURRENT_DATE, CURRENT_YEAR, or date ranges outside 2025. Use date functions directly on table timestamp columns (e.g., EXTRACT(QUARTER FROM s.transaction_date) = 3 for Q3, or EXTRACT(MONTH FROM s.transaction_date) = 3 for March)."
        )

        # Retrieve Top 4 relevant tables dynamically from pgvector
        schema_indexer = SchemaIndexer(self.db)
        relevant_schema = schema_indexer.retrieve_relevant_schemas(question, top_n=4)
        
        prompt = f"""Database Schema:\n{relevant_schema}\n\n"""
        
        if syntax_error:
            prompt += f"Note: Your previous query failed syntax validation with the following error: {syntax_error}\nPlease correct it.\n\n"

        prompt += f"User Question: \"{question}\"\nPostgreSQL Query:"

        response = self.client.generate(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            model=self.model,
            temperature=0.0
        )
        
        # Accumulate token metrics
        self.prompt_tokens += response.usage.prompt_tokens
        self.completion_tokens += response.usage.completion_tokens
        
        sql = response.choices[0].message.content.strip()
        # Clean any accidental markdown wrap
        sql = re.sub(r"^```sql\s*", "", sql, flags=re.IGNORECASE)
        sql = re.sub(r"^```\s*", "", sql, flags=re.IGNORECASE)
        sql = re.sub(r"\s*```$", "", sql, flags=re.IGNORECASE)
        # Remove trailing semicolons
        sql = sql.rstrip(';')
        return sql

    def _is_read_only(self, sql: str) -> bool:
        """Verifies that the query does not contain mutating keywords (read-only guardrail)."""
        unsafe_keywords = ["DROP", "DELETE", "UPDATE", "ALTER", "TRUNCATE", "INSERT", "GRANT", "REVOKE", "CREATE"]
        for kw in unsafe_keywords:
            pattern = rf"\b{kw}\b"
            if re.search(pattern, sql, re.IGNORECASE):
                return False
        return True

    def _validate_syntax(self, sql: str) -> tuple[bool, str]:
        """Runs a dry-run EXPLAIN command on the database to verify SQL syntax validity."""
        try:
            self.db.execute(text(f"EXPLAIN {sql}"))
            return True, None
        except Exception as e:
            try:
                self.db.rollback()
            except Exception:
                pass
            return False, str(e)
