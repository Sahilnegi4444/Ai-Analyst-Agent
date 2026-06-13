import pandas as pd
import numpy as np
from sqlalchemy.orm import Session
from app.database import engine

class AnalyticsService:
    """
    Service class handling Python/Pandas mathematical calculations on the database.
    Decouples raw numerical computations from LLM agents to prevent mathematical hallucinations.
    """

    @staticmethod
    def get_sales_df() -> pd.DataFrame:
        """Helper to fetch sales records from DB into a Pandas DataFrame."""
        return pd.read_sql("SELECT * FROM sales", con=engine)

    @staticmethod
    def get_products_df() -> pd.DataFrame:
        """Helper to fetch product records from DB into a Pandas DataFrame."""
        return pd.read_sql("SELECT * FROM products", con=engine)

    @staticmethod
    def get_inventory_df() -> pd.DataFrame:
        """Helper to fetch current inventory status from DB into a Pandas DataFrame."""
        return pd.read_sql("SELECT * FROM inventory", con=engine)

    @staticmethod
    def get_suppliers_df() -> pd.DataFrame:
        """Helper to fetch suppliers from DB into a Pandas DataFrame."""
        return pd.read_sql("SELECT * FROM suppliers", con=engine)

    @staticmethod
    def get_inventory_history_df() -> pd.DataFrame:
        """Helper to fetch historical inventory snapshot logs into a Pandas DataFrame."""
        return pd.read_sql("SELECT * FROM inventory_history", con=engine)

    def calculate_sales_summary(self) -> dict:
        """Calculates standard sales KPIs (Total Revenue, Transactions, Quantities, AOV)."""
        sales_df = self.get_sales_df()
        if sales_df.empty:
            return {
                "total_revenue": 0.0,
                "total_transactions": 0,
                "total_quantity_sold": 0,
                "average_order_value": 0.0
            }

        total_revenue = float(sales_df['total_amount'].sum())
        total_transactions = int(len(sales_df))
        total_quantity_sold = int(sales_df['quantity'].sum())
        average_order_value = float(total_revenue / total_transactions) if total_transactions > 0 else 0.0

        return {
            "total_revenue": round(total_revenue, 2),
            "total_transactions": total_transactions,
            "total_quantity_sold": total_quantity_sold,
            "average_order_value": round(average_order_value, 2)
        }

    def calculate_inventory_summary(self) -> dict:
        """Calculates inventory health statistics (Total Stock, Low Stock products, Avg Lead Time)."""
        inventory_df = self.get_inventory_df()
        suppliers_df = self.get_suppliers_df()

        if inventory_df.empty:
            return {
                "total_stock_level": 0,
                "low_stock_products_count": 0,
                "average_lead_time_days": 0.0
            }

        total_stock = int(inventory_df['current_stock'].sum())
        # Low stock defined as current stock <= reorder point
        low_stock_count = int((inventory_df['current_stock'] <= inventory_df['reorder_point']).sum())
        
        avg_lead_time = 0.0
        if not suppliers_df.empty:
            avg_lead_time = float(suppliers_df['lead_time_days'].mean())

        return {
            "total_stock_level": total_stock,
            "low_stock_products_count": low_stock_count,
            "average_lead_time_days": round(avg_lead_time, 2)
        }

    def calculate_monthly_sales_distribution(self) -> dict:
        """Groups sales transactions by month to compute monthly revenue trends."""
        sales_df = self.get_sales_df()
        if sales_df.empty:
            return {}

        sales_df['transaction_date'] = pd.to_datetime(sales_df['transaction_date'])
        # Extract Month name (format: YYYY-MM)
        sales_df['month'] = sales_df['transaction_date'].dt.strftime('%Y-%m')
        
        monthly_rev = sales_df.groupby('month')['total_amount'].sum()
        # Sort chronologically by index
        monthly_rev = monthly_rev.sort_index()
        
        return {str(m): round(float(val), 2) for m, val in monthly_rev.items()}

    def calculate_month_over_month_growth(self) -> dict:
        """Calculates Month-over-Month (MoM) revenue growth rates."""
        monthly_sales = self.calculate_monthly_sales_distribution()
        if not monthly_sales or len(monthly_sales) < 2:
            return {}

        months = sorted(list(monthly_sales.keys()))
        growth_rates = {}
        
        for i in range(1, len(months)):
            prev_month = months[i-1]
            curr_month = months[i]
            prev_val = monthly_sales[prev_month]
            curr_val = monthly_sales[curr_month]
            
            if prev_val > 0:
                growth = ((curr_val - prev_val) / prev_val) * 100
                growth_rates[curr_month] = round(float(growth), 2)
            else:
                growth_rates[curr_month] = 0.0
                
        return growth_rates

    def calculate_inventory_turnover_ratio(self) -> float:
        """
        Calculates the Inventory Turnover Ratio:
        Turnover Ratio = Cost of Goods Sold (COGS) / Average Inventory Value
        """
        sales_df = self.get_sales_df()
        products_df = self.get_products_df()
        history_df = self.get_inventory_history_df()

        if sales_df.empty or products_df.empty or history_df.empty:
            return 0.0

        # Calculate COGS: Sum of (Quantity Sold * Product Unit Cost)
        sales_merged = sales_df.merge(products_df, on='product_id')
        cogs = float((sales_merged['quantity'] * sales_merged['cost']).sum())

        # Calculate Average Inventory Value:
        # Sum (stock_on_hand * product cost) grouped by week, then take the average of all weeks.
        history_merged = history_df.merge(products_df, on='product_id')
        history_merged['inventory_value'] = history_merged['stock_on_hand'] * history_merged['cost']
        
        weekly_totals = history_merged.groupby('week_start_date')['inventory_value'].sum()
        average_inventory_value = float(weekly_totals.mean())

        if average_inventory_value == 0.0:
            return 0.0

        return round(cogs / average_inventory_value, 2)
