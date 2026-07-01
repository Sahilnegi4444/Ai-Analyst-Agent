from pydantic import BaseModel, Field
from typing import Dict

class SalesSummary(BaseModel):
    """
    Pydantic schema representing high-level sales KPIs.
    """
    total_revenue: float = Field(..., description="Sum of all transaction totals.")
    total_transactions: int = Field(..., description="Number of sales records.")
    total_quantity_sold: int = Field(..., description="Sum of item quantities purchased.")
    average_order_value: float = Field(..., description="Average price paid per transaction.")

class InventorySummary(BaseModel):
    """
    Pydantic schema representing high-level inventory KPIs.
    """
    total_stock_level: int = Field(..., description="Sum of current stock levels across catalog.")
    low_stock_products_count: int = Field(..., description="Number of products currently at or below reorder points.")
    average_lead_time_days: float = Field(..., description="Average vendor lead time across suppliers.")

class AnalyticsReport(BaseModel):
    """
    Pydantic schema representing a complete mathematical business report.
    """
    sales: SalesSummary = Field(..., description="Sales performance summary.")
    inventory: InventorySummary = Field(..., description="Inventory health summary.")
    monthly_sales_distribution: Dict[str, float] = Field(..., description="Monthly revenue breakdown.")
    month_over_month_growth: Dict[str, float] = Field(..., description="MoM sales growth percentages.")
