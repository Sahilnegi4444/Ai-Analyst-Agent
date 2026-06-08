import os
import pandas as pd
import numpy as np

def run_validation():
    print("Starting automated verification of generated dataset...")

    # Paths
    customers_path = 'data/customers.csv'
    products_path = 'data/products.csv'
    campaigns_path = 'data/marketing_campaigns.csv'
    inventory_path = 'data/inventory.csv'
    inventory_history_path = 'data/inventory_history.csv'
    sales_path = 'data/sales.csv'
    suppliers_path = 'data/suppliers.csv'
    returns_path = 'data/returns.csv'
    events_path = 'data/warehouse_events.csv'
    reviews_path = 'data/reviews.csv'

    pdf_files = [
        'data/documents/inventory_sop.pdf',
        'data/documents/marketing_policy.pdf',
        'data/documents/supplier_contract.pdf',
        'data/documents/monthly_executive_report_march.pdf',
        'data/documents/warehouse_manual.pdf'
    ]

    # Check file existence
    all_paths = [
        customers_path, products_path, campaigns_path, inventory_path,
        inventory_history_path, sales_path, suppliers_path, returns_path,
        events_path, reviews_path
    ] + pdf_files

    for path in all_paths:
        assert os.path.exists(path), f"File missing: {path}"
        print(f"Verified existence of {path}")

    # Load tables
    customers = pd.read_csv(customers_path)
    products = pd.read_csv(products_path)
    campaigns = pd.read_csv(campaigns_path)
    inventory = pd.read_csv(inventory_path)
    inventory_history = pd.read_csv(inventory_history_path)
    sales = pd.read_csv(sales_path)
    suppliers = pd.read_csv(suppliers_path)
    returns = pd.read_csv(returns_path)
    events = pd.read_csv(events_path)
    reviews = pd.read_csv(reviews_path)

    # Convert dates/datetimes
    sales['transaction_date'] = pd.to_datetime(sales['transaction_date'])
    inventory_history['week_start_date'] = pd.to_datetime(inventory_history['week_start_date'])
    returns['return_date'] = pd.to_datetime(returns['return_date'])
    reviews['review_date'] = pd.to_datetime(reviews['review_date'])

    # 1. Assert Row Counts
    print("\n--- Row Count Checks ---")
    assert len(customers) == 5000, f"Expected 5,000 customers, found {len(customers)}"
    print(f"[OK] Customers count: {len(customers)}")
    
    assert len(products) == 100, f"Expected 100 products, found {len(products)}"
    print(f"[OK] Products count: {len(products)}")
    
    assert len(campaigns) == 5, f"Expected 5 campaigns, found {len(campaigns)}"
    print(f"[OK] Campaigns count: {len(campaigns)}")
    
    assert len(inventory) == 100, f"Expected 100 inventory entries, found {len(inventory)}"
    print(f"[OK] Current inventory records count: {len(inventory)}")
    
    assert len(sales) == 50000, f"Expected 50,000 sales records, found {len(sales)}"
    print(f"[OK] Sales records count: {len(sales)}")

    assert len(suppliers) == 10, f"Expected 10 suppliers, found {len(suppliers)}"
    print(f"[OK] Suppliers count: {len(suppliers)}")

    assert len(returns) == 2000, f"Expected 2,000 returns, found {len(returns)}"
    print(f"[OK] Returns count: {len(returns)}")

    assert len(events) == 3, f"Expected 3 events, found {len(events)}"
    print(f"[OK] Warehouse events count: {len(events)}")

    assert len(reviews) == 5000, f"Expected 5,000 reviews, found {len(reviews)}"
    print(f"[OK] Reviews count: {len(reviews)}")

    # 2. Check Product A Details
    print("\n--- Product A Verification ---")
    prod_a = products[products['product_name'] == 'Product A']
    assert len(prod_a) == 1, "Product A not found in products table!"
    prod_a_id = prod_a.iloc[0]['product_id']
    print(f"[OK] Product A identified as: {prod_a_id}")

    # 3. Check March inventory shortage and 0 sales for Product A
    print("\n--- March Inventory Shortage for Product A Verification ---")
    march_inventory_a = inventory_history[
        (inventory_history['product_id'] == prod_a_id) & 
        (inventory_history['week_start_date'].dt.month == 3)
    ]
    assert (march_inventory_a['stock_on_hand'] == 0).all(), "Product A stock was not 0 in all March weeks!"
    assert (march_inventory_a['status'] == 'Out of Stock').all(), "Product A status was not 'Out of Stock' in March!"
    print("[OK] Product A stock is 0 (Out of Stock) for all weeks of March 2025 in inventory history.")

    march_sales_a = sales[
        (sales['product_id'] == prod_a_id) & 
        (sales['transaction_date'].dt.month == 3)
    ]
    assert len(march_sales_a) == 0, f"Product A was sold in March! Sales count: {len(march_sales_a)}"
    print("[OK] Product A has 0 sales in March 2025 due to inventory shortage.")

    # 4. Check June marketing campaign sales boost (June vs. baseline)
    print("\n--- June Campaign Verification ---")
    sales['month'] = sales['transaction_date'].dt.month
    monthly_sales_counts = sales.groupby('month').size()
    
    baseline_months = [1, 2, 4, 5, 7, 8, 9, 10, 11]
    baseline_avg_sales = monthly_sales_counts.loc[baseline_months].mean()
    june_sales = monthly_sales_counts.loc[6]
    june_boost = (june_sales - baseline_avg_sales) / baseline_avg_sales * 100
    
    print(f"Baseline Avg Monthly Sales: {baseline_avg_sales:.2f}")
    print(f"June Sales: {june_sales}")
    print(f"June Boost relative to Baseline: {june_boost:.2f}%")
    assert 20 <= june_boost <= 40, f"June boost is outside expected range (~30%): {june_boost:.2f}%"
    print("[OK] June sales show the expected ~30% boost.")

    # 5. Check December seasonal spike
    print("\n--- December Seasonal Spike Verification ---")
    december_sales = monthly_sales_counts.loc[12]
    december_spike = (december_sales - baseline_avg_sales) / baseline_avg_sales * 100
    print(f"December Sales: {december_sales}")
    print(f"December Spike relative to Baseline: {december_spike:.2f}%")
    assert 70 <= december_spike <= 95, f"December spike is outside expected range (~80%): {december_spike:.2f}%"
    print("[OK] December sales show the expected ~80% spike.")

    # 6. Check Region-based customer behaviors
    print("\n--- Regional Behavior Verification ---")
    sales_merged = sales.merge(customers[['customer_id', 'region']], on='customer_id', how='left')
    sales_merged = sales_merged.merge(products[['product_id', 'price']], on='product_id', how='left')
    
    # North: Strong Q4 sales
    north_sales = sales_merged[sales_merged['region'] == 'North']
    north_q4_sales_frac = len(north_sales[north_sales['month'].isin([10, 11, 12])]) / len(north_sales)
    
    non_north_sales = sales_merged[sales_merged['region'] != 'North']
    non_north_q4_sales_frac = len(non_north_sales[non_north_sales['month'].isin([10, 11, 12])]) / len(non_north_sales)
    
    print(f"North Q4 sales fraction: {north_q4_sales_frac:.4f}")
    print(f"Non-North Q4 sales fraction: {non_north_q4_sales_frac:.4f}")
    assert north_q4_sales_frac > non_north_q4_sales_frac * 1.15, "North Q4 sales are not significantly stronger!"
    print("[OK] North region exhibits strong Q4 sales behavior.")

    # South: Strong summer sales (months 6, 7, 8)
    south_sales = sales_merged[sales_merged['region'] == 'South']
    south_summer_sales_frac = len(south_sales[south_sales['month'].isin([6, 7, 8])]) / len(south_sales)
    
    non_south_sales = sales_merged[sales_merged['region'] != 'South']
    non_south_summer_sales_frac = len(non_south_sales[non_south_sales['month'].isin([6, 7, 8])]) / len(non_south_sales)
    
    print(f"South Summer sales fraction: {south_summer_sales_frac:.4f}")
    print(f"Non-South Summer sales fraction: {non_south_summer_sales_frac:.4f}")
    assert south_summer_sales_frac > non_south_summer_sales_frac * 1.15, "South Summer sales are not significantly stronger!"
    print("[OK] South region exhibits strong summer sales behavior.")

    # East: Consistent demand
    east_sales = sales_merged[sales_merged['region'] == 'East']
    east_monthly_counts = east_sales.groupby('month').size()
    east_cv = east_monthly_counts.std() / east_monthly_counts.mean()
    print(f"East monthly sales CV: {east_cv:.4f}")
    assert east_cv < 0.25, f"East monthly sales variation is too high: {east_cv:.4f}"
    print("[OK] East region exhibits consistent monthly demand.")

    # West: High premium purchases (price > 200)
    west_sales = sales_merged[sales_merged['region'] == 'West']
    west_premium_frac = len(west_sales[west_sales['price'] > 200]) / len(west_sales)
    
    non_west_sales = sales_merged[sales_merged['region'] != 'West']
    non_west_premium_frac = len(non_west_sales[non_west_sales['price'] > 200]) / len(non_west_sales)
    
    print(f"West premium purchase fraction (price > $200): {west_premium_frac:.4f}")
    print(f"Non-West premium purchase fraction (price > $200): {non_west_premium_frac:.4f}")
    assert west_premium_frac > non_west_premium_frac * 1.5, "West premium purchases are not significantly higher!"
    print("[OK] West region exhibits high premium purchase behavior.")

    # 7. Referential Integrity & Validity Checks
    print("\n--- Referential Integrity Checks ---")
    
    # 7.1 Returns Checks
    returns_sales = returns.merge(sales, on='transaction_id', how='left', suffixes=('_ret', '_sales'))
    assert not returns_sales['transaction_id'].isnull().any(), "Some return transactions not found in sales!"
    assert (returns_sales['product_id_ret'] == returns_sales['product_id_sales']).all(), "Returned product does not match sales product!"
    assert (np.abs(returns_sales['refund_amount'] - returns_sales['total_amount']) < 0.01).all(), "Refund amount does not match transaction total amount!"
    returns_sales['transaction_date'] = pd.to_datetime(returns_sales['transaction_date'])
    assert (returns_sales['return_date'] >= returns_sales['transaction_date']).all(), "Return date is before transaction date!"
    print("[OK] Returns table referential integrity verified.")

    # 7.2 Reviews Checks
    reviews_sales = reviews.merge(sales, on=['customer_id', 'product_id'], how='left')
    assert not reviews_sales['transaction_id'].isnull().any(), "Found reviews by customers who never purchased the product!"
    reviews_sales['transaction_date'] = pd.to_datetime(reviews_sales['transaction_date'])
    min_tx_dates = reviews_sales.groupby('review_id')['transaction_date'].min().reset_index()
    reviews_check = reviews.merge(min_tx_dates, on='review_id')
    assert (reviews_check['review_date'] >= reviews_check['transaction_date']).all(), "Some reviews are dated before the purchase date!"
    assert reviews['rating'].between(1, 5).all(), "Some review ratings are out of the 1-5 range!"
    print("[OK] Reviews table referential integrity verified.")

    # 7.3 Products and Suppliers Check
    assert products['supplier_id'].isin(suppliers['supplier_id']).all(), "Some products have invalid supplier IDs!"
    print("[OK] Products table links correctly to Suppliers table.")

    # 7.4 PDF size check
    for pdf_path in pdf_files:
        size = os.path.getsize(pdf_path)
        assert size > 1000, f"PDF file {pdf_path} is too small or empty (size: {size} bytes)!"
    print("[OK] Business PDF documents generated and validated successfully.")

    print("\n==============================================")
    print("ALL VERIFICATIONS PASSED SUCCESSFULLY!")
    print("==============================================")

if __name__ == '__main__':
    run_validation()
