import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Force mock providers for unit tests to ensure they run offline
os.environ["EMBEDDING_PROVIDER"] = "mock"
os.environ["RERANKER_PROVIDER"] = "mock"
os.environ["JINA_API_KEY"] = "mock_key"
os.environ["GROQ_API_KEY"] = "mock_key"

# Add project root to python path so we can import the app module
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.database import SessionLocal
from app.services.memory_service import ChatMemoryService
from app.models import ChatMessage

class MockGroq:
    def __init__(self, api_key=None, **kwargs):
        self.chat = MagicMock()
        self.chat.completions = MagicMock()
        self.chat.completions.create = self.mock_create

    def mock_create(self, messages, model, **kwargs):
        mock_resp = MagicMock()
        mock_choice = MagicMock()
        mock_message = MagicMock()
        mock_message.content = "What is the average rating of suppliers from Germany?"
        mock_choice.message = mock_message
        mock_resp.choices = [mock_choice]
        return mock_resp

class TestMemoryService(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.groq_patcher = patch('app.services.memory_service.Groq', MockGroq)
        cls.groq_patcher.start()

    @classmethod
    def tearDownClass(cls):
        cls.groq_patcher.stop()

    def setUp(self):
        self.db = SessionLocal()
        self.service = ChatMemoryService()
        self.session_id = "test-session-123"

    def tearDown(self):
        # Clean up test messages from database
        try:
            self.db.query(ChatMessage).filter(ChatMessage.session_id == self.session_id).delete()
            self.db.commit()
        except Exception:
            self.db.rollback()
        self.db.close()

    def test_add_and_get_history(self):
        # 1. Add user message
        msg1 = self.service.add_message(self.db, self.session_id, "user", "Show suppliers from Germany")
        self.assertIsNotNone(msg1.id)
        self.assertEqual(msg1.session_id, self.session_id)
        self.assertEqual(msg1.sender, "user")
        self.assertEqual(msg1.text, "Show suppliers from Germany")

        # 2. Add assistant response
        msg2 = self.service.add_message(
            self.db,
            self.session_id,
            "agent",
            "Here are the suppliers: Supplier A (Germany, rating: 4.5).",
            intent="SQL_QUERY",
            status="success"
        )
        self.assertIsNotNone(msg2.id)
        self.assertEqual(msg2.intent, "SQL_QUERY")
        self.assertEqual(msg2.status, "success")

        # 3. Retrieve history
        history = self.service.get_history(self.db, self.session_id)
        self.assertEqual(len(history), 2)
        self.assertEqual(history[0].sender, "user")
        self.assertEqual(history[1].sender, "agent")

    def test_query_contextualization(self):
        # 1. Setup mock history items
        msg1 = ChatMessage(sender="user", text="Show suppliers from Germany")
        msg2 = ChatMessage(sender="agent", text="Here are the suppliers: Supplier A (Germany, rating: 4.5).")
        
        # 2. Contextualize query
        rewritten = self.service.contextualize_query("What is their rating?", [msg1, msg2])
        self.assertEqual(rewritten, "What is the average rating of suppliers from Germany?")
