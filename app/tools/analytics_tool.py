from app.services.analytics_service import AnalyticsService
from typing import Dict, Any

class AnalyticsTool:
    """
    Tool wrapping the Pandas-based AnalyticsService calculations.
    Ensures mathematical queries are resolved purely via Pandas rather than LLM text generation.
    """
    def __init__(self):
        self.service = AnalyticsService()

    def execute_analytics(self, calculation_type: str) -> Dict[str, Any]:
        """
        Executes a targeted Pandas mathematical computation.
        
        Args:
            calculation_type (str): Type of analytics. Choices:
                - 'sales_summary'
                - 'inventory_summary'
                - 'mom_growth'
                - 'monthly_sales'
                - 'inventory_turnover'
        
        Returns:
            dict: Structured calculation outputs and status.
        """
        calc_type = calculation_type.lower().strip()
        try:
            if calc_type == 'sales_summary':
                res = self.service.calculate_sales_summary()
            elif calc_type == 'inventory_summary':
                res = self.service.calculate_inventory_summary()
            elif calc_type == 'mom_growth':
                res = self.service.calculate_month_over_month_growth()
            elif calc_type == 'monthly_sales':
                res = self.service.calculate_monthly_sales_distribution()
            elif calc_type == 'inventory_turnover':
                ratio = self.service.calculate_inventory_turnover_ratio()
                res = {"inventory_turnover_ratio": ratio}
            else:
                return {
                    "status": "error",
                    "error": f"Unknown calculation type '{calculation_type}'",
                    "results": None
                }
            
            return {
                "status": "success",
                "results": res,
                "error": None
            }
        except Exception as e:
            print(f"[ERROR] Analytics calculations failure: {e}")
            return {
                "status": "failed",
                "results": None,
                "error": str(e)
            }
