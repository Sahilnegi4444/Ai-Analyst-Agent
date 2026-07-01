import os
import sys
import json
import time
from typing import List
import re

# Add workspace root to python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from app.agents.workflow import AgentExecutor

class Evaluator:
    """
    Evaluation framework executing benchmarks on the AI Data Analyst Agent.
    Computes key performance indicators: SQL Accuracy, Retrieval Accuracy,
    Answer Accuracy, Hallucination Rates, and Latency profiles.
    """
    def __init__(self, dataset_path: str = "app/evaluation/dataset.json"):
        self.dataset_path = dataset_path
        self.test_cases = self._load_dataset()

    def _load_dataset(self) -> List[dict]:
        if not os.path.exists(self.dataset_path):
            print(f"[ERROR] Evaluation dataset not found at {self.dataset_path}")
            return []
        with open(self.dataset_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def run_evaluations(self) -> dict:
        print(f"Starting evaluations on {len(self.test_cases)} benchmark queries...")
        results = []
        
        for case in self.test_cases:
            print(f"\nEvaluating Case {case['id']}: '{case['query']}'")
            start_time = time.time()
            
            # Invoke agent workflow
            agent_res = AgentExecutor.run(case["query"])
            latency = time.time() - start_time
            
            # Extract outputs
            intent = agent_res.get("intent", {}).get("intent", "UNKNOWN")
            sql_query = agent_res.get("sql_query")
            sql_results = agent_res.get("sql_results")
            sql_error = agent_res.get("sql_error")
            rag_chunks = agent_res.get("rag_chunks") or []
            final_response = agent_res.get("final_response", "")
            status = agent_res.get("status", "success")

            # 1. SQL Accuracy metric
            sql_acc = 1.0
            if case["expected_sql_keywords"]:
                if not sql_query or sql_error:
                    sql_acc = 0.0
                else:
                    matched = sum(1 for kw in case["expected_sql_keywords"] if kw.lower() in sql_query.lower())
                    sql_acc = matched / len(case["expected_sql_keywords"])

            # 2. Retrieval Accuracy metric (RAG)
            retrieval_acc = 1.0
            if case["expected_sources"]:
                if not rag_chunks:
                    retrieval_acc = 0.0
                else:
                    retrieved_filenames = [chunk["filename"].lower() for chunk in rag_chunks]
                    matched = sum(1 for src in case["expected_sources"] if src.lower() in retrieved_filenames)
                    retrieval_acc = matched / len(case["expected_sources"])

            # 3. Answer Accuracy metric (Facts validation)
            answer_acc = 0.0
            if case["expected_facts"]:
                matched = sum(1 for fact in case["expected_facts"] if fact.lower() in final_response.lower())
                answer_acc = matched / len(case["expected_facts"])

            # 4. Hallucination Rate check
            # Heuristic: if final answer is not marked insufficient_data, check if numbers present in response
            # exist in database results or analytics results.
            hallucinated = 0.0
            if status != "insufficient_data" and status != "unsupported_query":
                numbers_in_response = re.findall(r"\b\d+[\.,]?\d*\b", final_response)
                # Filter out standard years/indices
                numbers_in_response = [n for n in numbers_in_response if n not in ["2025", "1", "2", "3", "4", "5", "0"]]
                
                if numbers_in_response:
                    # Collect all ground truth numbers
                    ground_truth_str = ""
                    if sql_results:
                        ground_truth_str += json.dumps(sql_results)
                    if agent_res.get("analytics_results"):
                        ground_truth_str += json.dumps(agent_res["analytics_results"])
                        
                    unsupported_numbers = 0
                    for num in numbers_in_response:
                        clean_num = num.replace(",", "")
                        if clean_num not in ground_truth_str and f"{float(clean_num):.2f}" not in ground_truth_str:
                            # Might be a rounded decimal or genuine hallucination
                            unsupported_numbers += 1
                    if unsupported_numbers > len(numbers_in_response) * 0.5:
                        hallucinated = 1.0  # High likelihood of hallucinated metrics

            results.append({
                "id": case["id"],
                "query": case["query"],
                "intent_match": (intent == case["expected_intent"]),
                "sql_accuracy": sql_acc,
                "retrieval_accuracy": retrieval_acc,
                "answer_accuracy": answer_acc,
                "hallucinated": hallucinated,
                "latency": latency
            })
            
            print(f"-> Intent Match: {intent == case['expected_intent']} | SQL Acc: {sql_acc:.2f} | RAG Acc: {retrieval_acc:.2f} | Answer Acc: {answer_acc:.2f} | Latency: {latency:.4f}s")
            
        return self._summarize_report(results)

    def _summarize_report(self, results: List[dict]) -> dict:
        total = len(results)
        if total == 0:
            return {}

        avg_intent_match = sum(1 for r in results if r["intent_match"]) / total * 100
        avg_sql_acc = sum(r["sql_accuracy"] for r in results) / total * 100
        avg_retrieval_acc = sum(r["retrieval_accuracy"] for r in results) / total * 100
        avg_answer_acc = sum(r["answer_accuracy"] for r in results) / total * 100
        avg_hallucination_rate = sum(r["hallucinated"] for r in results) / total * 100
        avg_latency = sum(r["latency"] for r in results) / total

        print("\n==============================================")
        print("            EVALUATION REPORT SUMMARY         ")
        print("==============================================")
        print(f"Total Test Cases Run        : {total}")
        print(f"Intent Classification Acc   : {avg_intent_match:.2f}%")
        print(f"SQL Validation Accuracy     : {avg_sql_acc:.2f}%")
        print(f"RAG Retrieval Accuracy      : {avg_retrieval_acc:.2f}%")
        print(f"Final Answer Fact Accuracy  : {avg_answer_acc:.2f}%")
        print(f"Detected Hallucination Rate : {avg_hallucination_rate:.2f}%")
        print(f"Average Invocation Latency  : {avg_latency:.4f} seconds")
        print("==============================================")
        
        report = {
            "total_runs": total,
            "intent_accuracy": round(avg_intent_match, 2),
            "sql_accuracy": round(avg_sql_acc, 2),
            "retrieval_accuracy": round(avg_retrieval_acc, 2),
            "answer_accuracy": round(avg_answer_acc, 2),
            "hallucination_rate": round(avg_hallucination_rate, 2),
            "average_latency_seconds": round(avg_latency, 4)
        }
        
        # Save report
        os.makedirs("data", exist_ok=True)
        with open("data/evaluation_report.json", "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
            
        return report

if __name__ == '__main__':
    evaluator = Evaluator()
    evaluator.run_evaluations()
