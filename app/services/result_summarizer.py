import pandas as pd
from typing import List, Dict, Any

class ResultSummarizer:
    """
    Utility class that analyzes and compresses large SQL output record arrays
    into descriptive summaries (counts, column list, numeric stats, top categories,
    and a small preview) to reduce the prompt token footprint.
    """
    @staticmethod
    def should_keep_raw(query: str, num_results: int = 0) -> bool:
        """
        Heuristic to determine if the user query explicitly demands listing full records,
        or if the dataset is small enough that summarization is unnecessary.
        """
        if num_results <= 15:
            return True
            
        query_lower = query.lower()
        # Words suggesting they want lists/records directly or rankings
        keywords = [
            "list", "show", "get", "print", "table", "details", "rows", "records", "raw",
            "top", "best", "worst", "most", "highest", "lowest", "who", "which", "give",
            "first", "last", "ranking"
        ]
        return any(kw in query_lower for kw in keywords)

    @staticmethod
    def summarize(results: List[Dict[str, Any]], query: str) -> Dict[str, Any]:
        """
        Converts the database result set to a Pandas DataFrame and calculates key statistics.
        Returns a concise dictionary summary suitable for injection into LLM prompts.
        """
        if not results:
            return {"rows": 0, "columns": []}

        try:
            df = pd.DataFrame(results)
            num_rows = len(df)
            columns = list(df.columns)

            summary = {
                "rows": num_rows,
                "columns": columns
            }

            # 1. Identify numeric columns (excluding IDs/keys)
            numeric_cols = []
            for col in df.columns:
                if pd.api.types.is_numeric_dtype(df[col]):
                    col_lower = str(col).lower()
                    if not any(x in col_lower for x in ["id", "zip", "code", "index", "phone", "number"]):
                        numeric_cols.append(col)

            # 2. Identify low-cardinality categorical columns (excluding long texts or unique IDs)
            categorical_cols = []
            for col in df.columns:
                if pd.api.types.is_string_dtype(df[col]) or pd.api.types.is_object_dtype(df[col]):
                    col_lower = str(col).lower()
                    if not any(x in col_lower for x in ["id", "email", "name", "desc", "text", "query"]):
                        categorical_cols.append(col)

            # 3. Identify date columns
            date_cols = []
            for col in df.columns:
                col_lower = str(col).lower()
                if "date" in col_lower or "time" in col_lower:
                    date_cols.append(col)

            # Averages and totals
            for col in numeric_cols:
                try:
                    summary[f"total_{col}"] = float(df[col].sum())
                    summary[f"avg_{col}"] = float(df[col].mean())
                    summary[f"min_{col}"] = float(df[col].min())
                    summary[f"max_{col}"] = float(df[col].max())
                except Exception:
                    pass

            # Top categories (up to 5 values)
            for col in categorical_cols:
                try:
                    val_counts = df[col].value_counts()
                    top_categories = val_counts.head(5).to_dict()
                    summary[f"top_{col}"] = top_categories
                except Exception:
                    pass

            # Date range
            for col in date_cols:
                try:
                    dates = pd.to_datetime(df[col], errors='coerce')
                    valid_dates = dates.dropna()
                    if not valid_dates.empty:
                        summary[f"{col}_range"] = {
                            "start": valid_dates.min().strftime('%Y-%m-%d'),
                            "end": valid_dates.max().strftime('%Y-%m-%d')
                        }
                except Exception:
                    pass

            # Return a preview of the first 5 records
            summary["preview_records"] = results[:5]
            return summary
        except Exception as e:
            # Fallback in case of dataframe conversion errors
            return {
                "rows": len(results),
                "error_summarizing": str(e),
                "preview_records": results[:5]
            }
