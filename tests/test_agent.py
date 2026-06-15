import unittest
import os
import sys

# Add project root to python path so we can import the app module
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.database import SessionLocal
from app.agents.router import IntentRouter
from app.tools.sql_tool import SQLTool
from app.tools.rag_tool import RAGTool
from app.services.analytics_service import AnalyticsService

class TestAIAnalystAgent(unittest.TestCase):
    """
    Unit testing suite to verify agent components (Intent Router, SQL Guardrails,
    RAG Retrieval, and Pandas Calculations) for correctness and reliability.
    """
    def setUp(self):
        # Open a database session connection for standard data checks
        self.db = SessionLocal()

    def tearDown(self):
        # Guarantee session clean closing
        self.db.close()

    def test_intent_router(self):
        """Tests that the intent router correctly identifies SQL, RAG, and Analytics queries."""
        router = IntentRouter()
        
        # Test SQL classification
        res1 = router.route_intent("Show top 5 products by revenue.")
        self.assertEqual(res1.get("intent"), "SQL_QUERY")
        self.assertTrue(res1.get("needs_sql"))
        self.assertFalse(res1.get("needs_rag"))
        
        # Test RAG classification
        res2 = router.route_intent("Summarize the inventory management SOP.")
        self.assertEqual(res2.get("intent"), "RAG_QUERY")
        self.assertFalse(res2.get("needs_sql"))
        self.assertTrue(res2.get("needs_rag"))

        # Test Analytics classification
        res3 = router.route_intent("What is the inventory turnover ratio?")
        self.assertEqual(res3.get("intent"), "ANALYTICS_QUERY")

    def test_sql_guardrails(self):
        """Tests that the SQL tool correctly blocks malicious/mutating SQL commands."""
        sql_tool = SQLTool(self.db)
        
        # Verify read-only query is allowed
        self.assertTrue(sql_tool._is_read_only("SELECT * FROM sales LIMIT 5"))
        
        # Verify modifying keywords are blocked (regardless of capitalization)
        self.assertFalse(sql_tool._is_read_only("DELETE FROM sales WHERE customer_id = 'C0001'"))
        self.assertFalse(sql_tool._is_read_only("DROP TABLE customers CASCADE"))
        self.assertFalse(sql_tool._is_read_only("UPDATE products SET price = 1000 WHERE product_id = 'P001'"))
        self.assertFalse(sql_tool._is_read_only("TRUNCATE TABLE reviews"))
        self.assertFalse(sql_tool._is_read_only("alter table sales add column score integer"))

    def test_rag_retrieval(self):
        """Tests that the RAG retrieval returns correct documents with high confidence."""
        rag_tool = RAGTool(self.db)
        res = rag_tool.retrieve_context("What is the procedure for inventory reordering?", top_k=2)
        
        self.assertEqual(res.get("status"), "success")
        chunks = res.get("chunks", [])
        self.assertGreater(len(chunks), 0)
        
        # Verify all source fields exist and scores are in [0, 1]
        for chunk in chunks:
            self.assertIn("filename", chunk)
            self.assertIn("title", chunk)
            self.assertIn("content", chunk)
            self.assertIn("confidence", chunk)
            self.assertTrue(0.0 <= chunk["confidence"] <= 1.0)

    def test_analytics_calculations(self):
        """Tests that the AnalyticsService computes correct Pandas mathematical formulas."""
        service = AnalyticsService()
        
        # Verify Sales Summary KPIs
        sales_sum = service.calculate_sales_summary()
        self.assertIn("total_revenue", sales_sum)
        self.assertIn("total_transactions", sales_sum)
        self.assertGreater(sales_sum["total_revenue"], 0)
        self.assertEqual(sales_sum["total_transactions"], 50000)

        # Verify Inventory Summary KPIs
        inv_sum = service.calculate_inventory_summary()
        self.assertIn("total_stock_level", inv_sum)
        self.assertIn("low_stock_products_count", inv_sum)
        self.assertGreater(inv_sum["total_stock_level"], 0)

        # Verify monthly revenue trends and MoM growth calculations
        monthly = service.calculate_monthly_sales_distribution()
        growth = service.calculate_month_over_month_growth()
        self.assertIn("2025-06", monthly)
        self.assertIn("2025-12", monthly)
        if len(monthly) > 1:
            self.assertGreater(len(growth), 0)

        # Verify Inventory Turnover ratio is calculation-bounded
        ratio = service.calculate_inventory_turnover_ratio()
        self.assertGreater(ratio, 0.0)

    def test_response_caching(self):
        """Tests that agent queries are cached and served from Redis cache or memory fallback."""
        from app.agents.workflow import AgentExecutor
        from app.services.cache_service import RedisCacheService
        
        cache_service = RedisCacheService()
        query = "What is the inventory turnover ratio?"
        
        if cache_service.enabled or cache_service.memory_fallback:
            # Clear key first to ensure cache miss on first call
            normalized = query.strip().lower()
            cache_key = f"cache:query:{normalized}"
            if cache_service.enabled:
                cache_service.client.delete(cache_key)
            elif cache_service.memory_fallback:
                if cache_key in cache_service.memory_cache:
                    del cache_service.memory_cache[cache_key]
            
            # First execution (Cache Miss)
            res1 = AgentExecutor.run(query)
            self.assertEqual(res1.get("cached"), False)
            
            # Second execution (Cache Hit)
            res2 = AgentExecutor.run(query)
            self.assertEqual(res2.get("cached"), True)
            self.assertEqual(res2.get("final_response"), res1.get("final_response"))
            self.assertLess(res2.get("latency"), res1.get("latency"))
        else:
            # Clean fallback execution test
            res = AgentExecutor.run(query)
            self.assertIn("cached", res)
            self.assertEqual(res.get("cached"), False)

if __name__ == '__main__':
    unittest.main()
