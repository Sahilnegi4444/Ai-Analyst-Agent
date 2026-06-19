import os
import sys
import json

# Add root directory to python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.agents.workflow import AgentExecutor

query = "what are the sales in June and July . Compare them and also show me the inventory SOP policies."
print(f"Running query: \"{query}\"")
res = AgentExecutor.run(query)

print("\n--- AGENT RESULT ---")
print("Intent:", res["intent"].get("intent"))
print("needs_sql:", res["plan"].get("needs_sql"))
print("needs_rag:", res["plan"].get("needs_rag"))
print("needs_analytics:", res["plan"].get("needs_analytics"))
print("SQL Query:", res.get("sql_query"))
print("SQL Results Count:", len(res.get("sql_results")) if res.get("sql_results") else 0)
print("RAG Chunks Count:", len(res.get("rag_chunks")) if res.get("rag_chunks") else 0)
print("Status:", res.get("status"))
print("\nFinal Response:\n", res.get("final_response"))
