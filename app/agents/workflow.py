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
from app.services.result_summarizer import ResultSummarizer

# =====================================================================
# LANGGRAPH STATE DEFINITION
# =====================================================================
class AgentState(TypedDict):
    """
    TypedDict representing the state graph context passed between nodes.
    Includes token counts and detailed performance metrics.
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
    # Extended metrics
    prompt_tokens: int
    completion_tokens: int
    sql_latency: float
    retrieval_latency: float
    analytics_latency: float

# =====================================================================
# NODE FUNCTIONS
# =====================================================================

def intent_node(state: AgentState) -> AgentState:
    """Classifies the incoming user query into an intent category."""
    router = IntentRouter()
    intent_res = router.route_intent(state["query"])
    
    prompt_tokens = state.get("prompt_tokens", 0) + intent_res.get("prompt_tokens", 0)
    completion_tokens = state.get("completion_tokens", 0) + intent_res.get("completion_tokens", 0)
    
    return {
        **state,
        "intent": intent_res,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens
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
    sql_start = time.time()
    db = SessionLocal()
    selected_tools = list(state["selected_tools"])
    selected_tools.append("sql_tool")
    
    try:
        sql_tool = SQLTool(db)
        res = sql_tool.execute_query(state["query"])
        
        sql_latency = time.time() - sql_start
        prompt_tokens = state.get("prompt_tokens", 0) + res.get("prompt_tokens", 0)
        completion_tokens = state.get("completion_tokens", 0) + res.get("completion_tokens", 0)
        
        return {
            **state,
            "sql_query": res.get("sql_query"),
            "sql_results": res.get("results"),
            "sql_error": res.get("error"),
            "selected_tools": selected_tools,
            "sql_latency": round(sql_latency, 4),
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens
        }
    finally:
        db.close()

def rag_node(state: AgentState) -> AgentState:
    """Runs the RAG tool if the plan requires unstructured document context."""
    rag_start = time.time()
    db = SessionLocal()
    selected_tools = list(state["selected_tools"])
    selected_tools.append("rag_tool")
    
    try:
        # Extract entities from SQL results to enrich subsequent RAG search context
        entities = []
        if state.get("sql_results"):
            for row in state["sql_results"][:5]:  # Process up to top 5 rows
                for col in ["product_name", "category", "supplier_name", "segment", "name"]:
                    if col in row and row[col]:
                        val = str(row[col]).strip()
                        if val and val not in entities:
                            entities.append(val)
        
        # Enrich the RAG query with the SQL context
        rag_query = state["query"]
        if entities:
            rag_query += f" (related context: {', '.join(entities)})"
            print(f"[CONTEXT ENRICHMENT] Enriched RAG query: '{rag_query}'")
            
        rag_tool = RAGTool(db)
        res = rag_tool.retrieve_context(rag_query, top_k=3)
        
        retrieval_latency = time.time() - rag_start
        prompt_tokens = state.get("prompt_tokens", 0) + res.get("prompt_tokens", 0)
        completion_tokens = state.get("completion_tokens", 0) + res.get("completion_tokens", 0)
        
        return {
            **state,
            "rag_chunks": res.get("chunks", []),
            "selected_tools": selected_tools,
            "retrieval_latency": round(retrieval_latency, 4),
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens
        }
    finally:
        db.close()

def analytics_node(state: AgentState) -> AgentState:
    """Runs the Python/Pandas analytics calculations if required."""
    analytics_start = time.time()
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

    analytics_latency = time.time() - analytics_start
    return {
        **state,
        "analytics_results": results,
        "selected_tools": selected_tools,
        "analytics_latency": round(analytics_latency, 4)
    }

def generator_node(state: AgentState) -> AgentState:
    """Synthesizes the final answer using Groq, enforcing data-integrity guardrails."""
    # Compute latency
    latency = time.time() - state["start_time"]
    
    intent_type = state["intent"].get("intent", "UNSUPPORTED_QUERY")
    if intent_type == "SECURITY_VIOLATION":
        return {
            **state,
            "final_response": "I cannot perform this operation. Bypassing read-only database controls or attempting to modify/delete records is strictly prohibited.",
            "status": "security_violation",
            "latency": round(latency, 4)
        }

    if intent_type == "UNSUPPORTED_QUERY":
        return {
            **state,
            "final_response": "I'm sorry, but I can only assist with retail database operations and company documentation queries.",
            "status": "unsupported_query",
            "latency": round(latency, 4)
        }

    # 1. Direct Security Block Check
    if state["sql_error"] and "security violation" in state["sql_error"].lower():
        return {
            **state,
            "final_response": "I cannot perform this operation. Bypassing read-only database controls or attempting to modify/delete records is strictly prohibited.",
            "status": "security_violation",
            "latency": round(latency, 4)
        }

    # Data Availability Safety check
    insufficient_response = json.dumps({
        "status": "insufficient_data",
        "reason": "Requested information does not exist in available sources"
    }, indent=2)

    has_sql_data = bool(state["plan"]["needs_sql"] and state["sql_results"] and not state["sql_error"])
    has_rag_data = bool(state["plan"]["needs_rag"] and state["rag_chunks"])

    # If SQL was required but we have no SQL data AND we don't have RAG data to compensate:
    if state["plan"]["needs_sql"] and not has_sql_data:
        if not has_rag_data:
            return {
                **state,
                "final_response": insufficient_response,
                "status": "insufficient_data",
                "latency": round(latency, 4)
            }

    # If RAG was required but we have no RAG data AND we don't have SQL data to compensate:
    if state["plan"]["needs_rag"] and not has_rag_data:
        if not has_sql_data:
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
        "Your task is to synthesize a professional, concise business response to the user's query.\n"
        "Rules:\n"
        "1. Base your answer strictly on the provided SQL database results, RAG chunks, and Analytics values. Focus only on answering the user's question.\n"
        "2. Do NOT run calculations or do math in your head. Strictly reference the calculated metrics from the Analytics context.\n"
        "3. Cite your sources by filename when referencing RAG documents (e.g. 'Source: inventory_sop.pdf').\n"
        "4. Only provide information explicitly requested by the user. Do NOT include unsolicited generic notes or commentary about missing documentation, seasonality, or system limits unless the user's query explicitly asked for explanations or reasons.\n"
        "5. If the user asks for explanations, reasons, or analysis, you MUST describe the specific facts, dates, events, and entities (such as product names, warehouse delay dates, or logistics issues) found in the retrieved RAG chunks to provide a complete answer.\n"
        "6. When referencing specific months, represent them with both their calendar name and their dataset date format (e.g. 'March 2025 (2025-03)' or 'February 2025 (2025-02)').\n"
        "7. Under no circumstances include any system fallback JSON strings, system templates, or hypothetical descriptions (such as how the system would behave when data is missing) in your final text. Keep the output clean, natural, and directly targeted at the query.\n"
        "8. If the provided database results, analytics, and RAG chunks are all completely empty or missing, you must output exactly this JSON and nothing else: {\"status\": \"insufficient_data\", \"reason\": \"Requested information does not exist in available sources\"}.\n"
        "9. Never output raw SQL code blocks, SELECT statements, or SQL queries in your response text. Explain results conceptually in plain, professional English.\n"
        "10. Write in simple, direct, and conversational business English. Avoid overly formal language, legalese, academic jargon, or verbose sentences. Explain facts and statistics simply so any manager or customer can understand instantly.\n"
        "11. Never use technical, developer-facing, or database terms like 'RAG', 'chunks', 'RAG documents', 'RAG context', 'Analytics values', 'Analytics context', 'SQL database results', or 'database context' in your response. Under no circumstances say 'According to the Analytics values' or 'As outlined in the RAG chunks'. State facts and numbers directly (e.g. say 'The average delay is...' or 'According to the inventory SOP...').\n"
        "12. Keep the response extremely concise. Do not write multiple paragraphs unless necessary to separate distinct datasets. Answer in a single, well-structured paragraph or a short bulleted list to minimize token consumption and maximize output quality."
    )

    context = f"User Question: \"{state['query']}\"\n\n"
    
    # 2. Inject compressed or raw SQL results
    if state["sql_query"]:
        results = state["sql_results"] or []
        
        # Decide if we can compress the SQL dataset
        if ResultSummarizer.should_keep_raw(state["query"], len(results)):
            # User wants row-level details explicitly
            if len(results) > 50:
                truncated = results[:50]
                context += f"--- SQL Database Context (Truncated to first 50 of {len(results)} rows to save tokens) ---\nQuery: {state['sql_query']}\nResults:\n{json.dumps(truncated, indent=2)}\n\n"
            else:
                context += f"--- SQL Database Context ---\nQuery: {state['sql_query']}\nResults:\n{json.dumps(results, indent=2)}\n\n"
        else:
            # Compress results to save tokens
            summary = ResultSummarizer.summarize(results, state["query"])
            context += f"--- SQL Database Context (Summarized to save tokens) ---\nQuery: {state['sql_query']}\nResults Summary:\n{json.dumps(summary, indent=2)}\n\n"
        
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
            model=settings.GROQ_GENERATOR_MODEL,
            temperature=0.0
        )
        
        final_answer = response.choices[0].message.content.strip()
        
        # Check if the model decided to emit insufficient_data JSON
        status = "success"
        if "insufficient_data" in final_answer:
            status = "insufficient_data"
            
        prompt_tokens = state.get("prompt_tokens", 0) + response.usage.prompt_tokens
        completion_tokens = state.get("completion_tokens", 0) + response.usage.completion_tokens
            
        return {
            **state,
            "final_response": final_answer,
            "status": status,
            "latency": round(latency, 4),
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens
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
# CONDITIONAL ROUTING LOGIC (LANGGRAPH EDGES)
# =====================================================================

def route_after_planner(state: AgentState) -> str:
    """Routes from planner node to the first active tool or straight to generator."""
    intent_type = state["intent"].get("intent", "UNSUPPORTED_QUERY")
    if intent_type in ["SECURITY_VIOLATION", "UNSUPPORTED_QUERY"]:
        return "generator_node"

    plan = state["plan"]
    if plan.get("needs_sql"):
        return "sql_node"
    elif plan.get("needs_rag"):
        return "rag_node"
    elif plan.get("needs_analytics"):
        return "analytics_node"
    else:
        return "generator_node"

def route_after_sql(state: AgentState) -> str:
    """Routes after sql_node runs, checking RAG or Analytics next."""
    plan = state["plan"]
    if plan.get("needs_rag"):
        return "rag_node"
    elif plan.get("needs_analytics"):
        return "analytics_node"
    else:
        return "generator_node"

def route_after_rag(state: AgentState) -> str:
    """Routes after rag_node runs, checking Analytics next."""
    plan = state["plan"]
    if plan.get("needs_analytics"):
        return "analytics_node"
    else:
        return "generator_node"

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
    
    # Establish edges (conditional edges skip unused nodes entirely)
    workflow.add_edge(START, "intent_node")
    workflow.add_edge("intent_node", "planner_node")
    
    workflow.add_conditional_edges(
        "planner_node",
        route_after_planner,
        {
            "sql_node": "sql_node",
            "rag_node": "rag_node",
            "analytics_node": "analytics_node",
            "generator_node": "generator_node"
        }
    )
    
    workflow.add_conditional_edges(
        "sql_node",
        route_after_sql,
        {
            "rag_node": "rag_node",
            "analytics_node": "analytics_node",
            "generator_node": "generator_node"
        }
    )
    
    workflow.add_conditional_edges(
        "rag_node",
        route_after_rag,
        {
            "analytics_node": "analytics_node",
            "generator_node": "generator_node"
        }
    )
    
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
            cached_res["start_time"] = start_time
            cached_res["latency"] = round(latency, 4)
            cached_res["cached"] = True
            
            # Log cached run
            ObservabilityLogger.log_agent_run(
                user_query=cached_res["query"],
                detected_intent=cached_res["intent"].get("intent", "UNKNOWN"),
                selected_tools=cached_res.get("selected_tools", []),
                generated_sql=cached_res.get("sql_query"),
                execution_status=cached_res.get("status", "success"),
                retrieval_results=cached_res.get("rag_chunks"),
                latency=cached_res["latency"],
                cached=True,
                prompt_tokens=cached_res.get("prompt_tokens", 0),
                completion_tokens=cached_res.get("completion_tokens", 0)
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
            "latency": 0.0,
            # Init metrics
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "sql_latency": 0.0,
            "retrieval_latency": 0.0,
            "analytics_latency": 0.0
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
            cached=False,
            prompt_tokens=final_state.get("prompt_tokens", 0),
            completion_tokens=final_state.get("completion_tokens", 0),
            sql_latency=final_state.get("sql_latency", 0.0),
            retrieval_latency=final_state.get("retrieval_latency", 0.0),
            analytics_latency=final_state.get("analytics_latency", 0.0)
        )
        
        # 3. Store new response state in Redis Cache if successful or expected status
        if final_state.get("status") in ["success", "unsupported_query", "security_violation"]:
            cache_service.set_cached_query(query, final_state)
        
        return final_state
