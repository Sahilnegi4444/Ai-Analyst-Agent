import time
import json
import re
from typing import TypedDict, List, Dict, Any, Optional, Union
from langgraph.graph import StateGraph, START, END
from groq import Groq

from app.config import settings
from app.database import SessionLocal
from app.agents.router import IntentRouter
from app.tools.sql_tool import SQLTool
from app.tools.rag_tool import RAGTool
from app.tools.analytics_tool import AnalyticsTool
from app.utils.logger import ObservabilityLogger

# =====================================================================
# LANGGRAPH STATE DEFINITION
# =====================================================================
class AgentState(TypedDict):
    """
    TypedDict representing the state graph context passed between nodes.
    """
    query: str
    intent: Dict[str, Any]
    plan: Dict[str, Any]
    sql_query: Optional[str]
    sql_results: Optional[List[Dict[str, Any]]]
    sql_error: Optional[str]
    rag_chunks: Optional[List[Dict[str, Any]]]
    analytics_results: Optional[Dict[str, Any]]
    final_response: str
    status: str  # 'success', 'insufficient_data', 'unsupported_query', 'error'
    selected_tools: List[str]
    start_time: float
    latency: float

# =====================================================================
# NODE FUNCTIONS
# =====================================================================

def intent_node(state: AgentState) -> AgentState:
    """Classifies the incoming user query into an intent category."""
    router = IntentRouter()
    intent_res = router.route_intent(state["query"])
    return {
        **state,
        "intent": intent_res
    }

def planner_node(state: AgentState) -> AgentState:
    """Evaluates the classified intent and designs a tool routing plan."""
    intent_data = state["intent"]
    intent_type = intent_data.get("intent", "UNSUPPORTED_QUERY")
    
    plan = {
        "needs_sql": intent_data.get("needs_sql", False),
        "needs_rag": intent_data.get("needs_rag", False),
        "needs_analytics": (intent_type == "ANALYTICS_QUERY" or intent_type == "HYBRID_QUERY")
    }
    
    return {
        **state,
        "plan": plan
    }

def sql_node(state: AgentState) -> AgentState:
    """Runs the SQL tool if the plan requires structured database access."""
    if not state["plan"]["needs_sql"]:
        return state

    db = SessionLocal()
    selected_tools = list(state["selected_tools"])
    selected_tools.append("sql_tool")
    
    try:
        sql_tool = SQLTool(db)
        res = sql_tool.execute_query(state["query"])
        
        return {
            **state,
            "sql_query": res.get("sql_query"),
            "sql_results": res.get("results"),
            "sql_error": res.get("error"),
            "selected_tools": selected_tools
        }
    finally:
        db.close()

def rag_node(state: AgentState) -> AgentState:
    """Runs the RAG tool if the plan requires unstructured document context."""
    if not state["plan"]["needs_rag"]:
        return state

    db = SessionLocal()
    selected_tools = list(state["selected_tools"])
    selected_tools.append("rag_tool")
    
    try:
        rag_tool = RAGTool(db)
        res = rag_tool.retrieve_context(state["query"], top_k=3)
        
        return {
            **state,
            "rag_chunks": res.get("chunks", []),
            "selected_tools": selected_tools
        }
    finally:
        db.close()

def analytics_node(state: AgentState) -> AgentState:
    """Runs the Python/Pandas analytics calculations if required."""
    if not state["plan"]["needs_analytics"]:
        return state

    selected_tools = list(state["selected_tools"])
    selected_tools.append("analytics_tool")
    analytics_tool = AnalyticsTool()
    
    query_lower = state["query"].lower()
    results = {}
    
    # Intelligently invoke targeted Pandas service calls based on keywords
    if "turnover" in query_lower:
        res = analytics_tool.execute_analytics("inventory_turnover")
        if res.get("status") == "success":
            results.update(res["results"])
            
    if "growth" in query_lower or "rate" in query_lower or "mom" in query_lower:
        res = analytics_tool.execute_analytics("mom_growth")
        if res.get("status") == "success":
            results["mom_growth_rates"] = res["results"]
            
    if "compare" in query_lower or "sales" in query_lower or "revenue" in query_lower or "aov" in query_lower:
        # Load standard monthly distribution or overall summary
        res_dist = analytics_tool.execute_analytics("monthly_sales")
        res_sum = analytics_tool.execute_analytics("sales_summary")
        if res_dist.get("status") == "success":
            results["monthly_sales_distribution"] = res_dist["results"]
        if res_sum.get("status") == "success":
            results["sales_summary_kpis"] = res_sum["results"]
            
    if "inventory" in query_lower or "stock" in query_lower or "warehouse" in query_lower:
        res_inv = analytics_tool.execute_analytics("inventory_summary")
        if res_inv.get("status") == "success":
            results["inventory_summary_kpis"] = res_inv["results"]
            
    # Default fallback: load sales and inventory summaries if empty
    if not results:
        res_sum = analytics_tool.execute_analytics("sales_summary")
        res_inv = analytics_tool.execute_analytics("inventory_summary")
        if res_sum.get("status") == "success":
            results["sales_summary_kpis"] = res_sum["results"]
        if res_inv.get("status") == "success":
            results["inventory_summary_kpis"] = res_inv["results"]

    return {
        **state,
        "analytics_results": results,
        "selected_tools": selected_tools
    }

def generator_node(state: AgentState) -> AgentState:
    """Synthesizes the final answer using Groq, enforcing data-integrity guardrails."""
    # Compute latency
    latency = time.time() - state["start_time"]
    
    intent_type = state["intent"].get("intent", "UNSUPPORTED_QUERY")
    if intent_type == "UNSUPPORTED_QUERY":
        return {
            **state,
            "final_response": "I'm sorry, but I can only assist with retail database operations and company documentation queries.",
            "status": "unsupported_query",
            "latency": round(latency, 4)
        }

    # Data Availability Safety check
    # If the SQL query failed or RAG returned zero chunks (when required), return standard error.
    insufficient_response = json.dumps({
        "status": "insufficient_data",
        "reason": "Requested information does not exist in available sources"
    }, indent=2)

    if state["plan"]["needs_sql"] and (not state["sql_results"] or state["sql_error"]):
        return {
            **state,
            "final_response": insufficient_response,
            "status": "insufficient_data",
            "latency": round(latency, 4)
        }

    if state["plan"]["needs_rag"] and not state["rag_chunks"]:
        return {
            **state,
            "final_response": insufficient_response,
            "status": "insufficient_data",
            "latency": round(latency, 4)
        }

    # Generate synthesis prompt
    client = Groq(api_key=settings.GROQ_API_KEY)
    
    system_prompt = (
        "You are a Senior Business Intelligence and Data Analyst Agent.\n"
        "Your task is to synthesize a professional business response to the user's query.\n"
        "Rules:\n"
        "1. Base your answer strictly on the provided SQL database results, RAG chunks, and Analytics values.\n"
        "2. Do NOT run calculations or do math in your head. Strictly reference the calculated metrics from the Analytics context.\n"
        "3. Cite your sources by filename when referencing RAG documents (e.g. 'Source: inventory_sop.pdf').\n"
        "4. If the provided data is empty or does not contain facts necessary to answer the question, you MUST output EXACTLY this JSON payload and nothing else:\n"
        "{\n"
        "  \"status\": \"insufficient_data\",\n"
        "  \"reason\": \"Requested information does not exist in available sources\"\n"
        "}\n"
        "5. Keep the response factual, concise, and structured with professional markdown formatting."
    )

    context = f"User Question: \"{state['query']}\"\n\n"
    
    if state["sql_query"]:
        results = state["sql_results"] or []
        if len(results) > 50:
            truncated = results[:50]
            context += f"--- SQL Database Context (Truncated to first 50 of {len(results)} rows to save tokens) ---\nQuery: {state['sql_query']}\nResults:\n{json.dumps(truncated, indent=2)}\n\n"
        else:
            context += f"--- SQL Database Context ---\nQuery: {state['sql_query']}\nResults:\n{json.dumps(results, indent=2)}\n\n"
        
    if state["rag_chunks"]:
        formatted_rag = []
        for idx, chunk in enumerate(state["rag_chunks"], 1):
            formatted_rag.append(
                f"Source [{idx}]: {chunk['filename']} (Title: {chunk['title']})\n"
                f"Similarity: {chunk['confidence'] * 100:.2f}%\n"
                f"Content: {chunk['content']}"
            )
        context += f"--- Document RAG Context ---\n" + "\n\n".join(formatted_rag) + "\n\n"
        
    if state["analytics_results"]:
        context += f"--- Pandas Analytics Calculations Context ---\n{json.dumps(state['analytics_results'], indent=2)}\n\n"

    try:
        response = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": context}
            ],
            model=settings.GROQ_GENERATOR_MODEL,  # Higher logic model for synthesis
            temperature=0.0
        )
        
        final_answer = response.choices[0].message.content.strip()
        
        # Check if the model decided to emit insufficient_data JSON
        status = "success"
        if "insufficient_data" in final_answer:
            status = "insufficient_data"
            
        return {
            **state,
            "final_response": final_answer,
            "status": status,
            "latency": round(latency, 4)
        }
    except Exception as e:
        print(f"[ERROR] Generator Node failure: {e}")
        return {
            **state,
            "final_response": f"Error during response generation: {e}",
            "status": "error",
            "latency": round(latency, 4)
        }

# =====================================================================
# LANGGRAPH WORKFLOW SETUP
# =====================================================================

def create_agent_workflow():
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("intent_node", intent_node)
    workflow.add_node("planner_node", planner_node)
    workflow.add_node("sql_node", sql_node)
    workflow.add_node("rag_node", rag_node)
    workflow.add_node("analytics_node", analytics_node)
    workflow.add_node("generator_node", generator_node)
    
    # Establish links
    workflow.add_edge(START, "intent_node")
    workflow.add_edge("intent_node", "planner_node")
    workflow.add_edge("planner_node", "sql_node")
    workflow.add_edge("sql_node", "rag_node")
    workflow.add_edge("rag_node", "analytics_node")
    workflow.add_edge("analytics_node", "generator_node")
    workflow.add_edge("generator_node", END)
    
    return workflow.compile()

# Compile the graph singleton
agent_app = create_agent_workflow()

class AgentExecutor:
    """
    Interface wrapper to execute the compiled LangGraph workflow,
    handle query response caching via Redis, and record observability logs.
    """
    @staticmethod
    def run(query: str) -> dict:
        from app.services.cache_service import RedisCacheService
        cache_service = RedisCacheService()
        
        start_time = time.time()
        
        # 1. Try fetching from Redis Cache
        cached_res = cache_service.get_cached_query(query)
        if cached_res is not None:
            latency = time.time() - start_time
            # Populate latency metrics and cached flag
            cached_res["start_time"] = start_time
            cached_res["latency"] = round(latency, 4)
            cached_res["cached"] = True
            
            # Log cached run to observability
            ObservabilityLogger.log_agent_run(
                user_query=cached_res["query"],
                detected_intent=cached_res["intent"].get("intent", "UNKNOWN"),
                selected_tools=cached_res.get("selected_tools", []),
                generated_sql=cached_res.get("sql_query"),
                execution_status=cached_res.get("status", "success"),
                retrieval_results=cached_res.get("rag_chunks"),
                latency=cached_res["latency"],
                cached=True
            )
            return cached_res
            
        # 2. Cache Miss: Run full LangGraph agent workflow
        initial_state: AgentState = {
            "query": query,
            "intent": {},
            "plan": {},
            "sql_query": None,
            "sql_results": None,
            "sql_error": None,
            "rag_chunks": None,
            "analytics_results": None,
            "final_response": "",
            "status": "success",
            "selected_tools": [],
            "start_time": start_time,
            "latency": 0.0
        }
        
        final_state = agent_app.invoke(initial_state)
        
        # Compute execution latency
        latency = time.time() - start_time
        final_state["latency"] = round(latency, 4)
        final_state["cached"] = False
        
        # Log to observability logger
        ObservabilityLogger.log_agent_run(
            user_query=final_state["query"],
            detected_intent=final_state["intent"].get("intent", "UNKNOWN"),
            selected_tools=final_state["selected_tools"],
            generated_sql=final_state["sql_query"],
            execution_status=final_state["status"],
            retrieval_results=final_state["rag_chunks"],
            latency=final_state["latency"],
            cached=False
        )
        
        # 3. Store new response state in Redis Cache
        cache_service.set_cached_query(query, final_state)
        
        return final_state
