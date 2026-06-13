import os
import json
from groq import Groq
from app.config import settings

class IntentRouter:
    """
    Service class responsible for classifying incoming user queries into database,
    document retrieval, hybrid, or analytics intents using the Groq API in JSON mode.
    """
    def __init__(self):
        # Initialize Groq client with environment key
        self.client = Groq(api_key=settings.GROQ_API_KEY)
        self.model = settings.GROQ_ROUTER_MODEL

    def route_intent(self, query: str) -> dict:
        """
        Classifies user query into one of: SQL_QUERY, RAG_QUERY, HYBRID_QUERY, ANALYTICS_QUERY, UNSUPPORTED_QUERY.
        
        Returns:
            dict: Structured classification containing 'intent', 'needs_sql', 'needs_rag', and 'explanation'.
        """
        system_instructions = (
            "You are a routing agent for an enterprise business intelligence assistant. "
            "Your job is to analyze the query and return a JSON object classifying the intent. "
            "Do not include any greeting, markdown, or explanation text outside the JSON."
        )

        prompt = f"""Classify the following user query into one of 5 distinct intents:

1. SQL_QUERY:
   - Question can be answered directly using SQL queries on tables (customers, products, sales, returns, reviews, suppliers, current inventory).
   - Examples: "Show top 5 products by revenue", "How many customers in VIP segment?", "List recent returns".

2. RAG_QUERY:
   - Question asks about company policies, rules, SOPs, manuals, or contracts (e.g. inventory SOP, marketing rules, supplier contracts, shipping procedures).
   - Examples: "Summarize the inventory management SOP", "What are the rules for supplier SLA penalties?", "Explain the warehouse manual".

3. HYBRID_QUERY:
   - Question requires BOTH SQL database metrics and RAG context to resolve (e.g. explaining performance gaps or correlating metrics with documents).
   - Examples: "Why did sales decrease in March?", "Which products are affected by the March warehouse delays?".

4. ANALYTICS_QUERY:
   - Question asks for complex calculations, ratios, MoM growth rates, or inventory turnover.
   - Examples: "Compare March sales with February", "Calculate MoM sales growth rates", "What is the inventory turnover ratio?".

5. UNSUPPORTED_QUERY:
   - Off-topic, general programming, or general knowledge questions unrelated to our data.
   - Examples: "Write a quicksort in Python", "What is the capital of France?".

You must output a JSON object with this exact structure:
{{
  "intent": "SQL_QUERY" | "RAG_QUERY" | "HYBRID_QUERY" | "ANALYTICS_QUERY" | "UNSUPPORTED_QUERY",
  "needs_sql": true | false,
  "needs_rag": true | false,
  "explanation": "Brief reasoning for classification"
}}

User Query: "{query}"

JSON response:"""

        try:
            response = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_instructions},
                    {"role": "user", "content": prompt}
                ],
                model=self.model,
                response_format={"type": "json_object"},
                temperature=0.0
            )
            
            result = json.loads(response.choices[0].message.content)
            # Standardize returned keys
            result["needs_sql"] = bool(result.get("needs_sql", False))
            result["needs_rag"] = bool(result.get("needs_rag", False))
            return result
            
        except Exception as e:
            print(f"[ERROR] Intent Router failure: {e}")
            # Safe default fallback
            return {
                "intent": "UNSUPPORTED_QUERY",
                "needs_sql": False,
                "needs_rag": False,
                "explanation": f"Intent router error: {e}"
            }
