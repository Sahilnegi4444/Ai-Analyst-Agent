import os
import pandas as pd
import numpy as np
from faker import Faker
from datetime import datetime, timedelta

def main():
    print("Initializing updated synthetic retail dataset generator...")
    # Set random seed for reproducibility
    np.random.seed(42)
    fake = Faker()
    Faker.seed(42)

    # Ensure data directory exists in the workspace
    os.makedirs('data', exist_ok=True)

    # ---------------------------------------------------------
    # 1. Generate Suppliers Table (10 suppliers)
    # ---------------------------------------------------------
    print("Generating 10 suppliers...")
    supplier_ids = [f"S{i:02d}" for i in range(1, 11)]
    countries = ['USA', 'China', 'Vietnam', 'Mexico', 'Germany', 'India', 'Japan', 'Canada', 'UK', 'Brazil']
    
    suppliers_df = pd.DataFrame({
        'supplier_id': supplier_ids,
        'supplier_name': [fake.company() + " Ltd" for _ in range(10)],
        'lead_time_days': np.random.randint(3, 15, size=10),
        'country': countries,
        'rating': np.round(np.random.uniform(3.5, 5.0, size=10), 2)
    })
    suppliers_df.to_csv('data/suppliers.csv', index=False)
    print("Saved data/suppliers.csv")

    # ---------------------------------------------------------
    # 2. Generate Customers Table (5,000 customers)
    # ---------------------------------------------------------
    print("Generating 5,000 customers...")
    customer_ids = [f"C{i:04d}" for i in range(1, 5001)]
    
    signup_dates = [fake.date_between(start_date='-3y', end_date='-1y') for _ in range(5000)]
    segments = np.random.choice(['Standard', 'Premium', 'VIP'], size=5000, p=[0.7, 0.2, 0.1])
    genders = np.random.choice(['M', 'F', 'O'], size=5000, p=[0.48, 0.48, 0.04])
    
    states_cities = [
        ('NY', 'New York'), ('CA', 'Los Angeles'), ('CA', 'San Francisco'),
        ('TX', 'Houston'), ('TX', 'Austin'), ('IL', 'Chicago'),
        ('FL', 'Miami'), ('WA', 'Seattle'), ('MA', 'Boston'), ('CO', 'Denver')
    ]
    selected_states_cities = [states_cities[np.random.choice(len(states_cities))] for _ in range(5000)]
    
    state_region_map = {
        'NY': 'North',
        'MA': 'North',
        'FL': 'South',
        'TX': 'South',
        'IL': 'East',
        'CO': 'East',
        'CA': 'West',
        'WA': 'West'
    }

    customers_df = pd.DataFrame({
        'customer_id': customer_ids,
        'name': [fake.name() for _ in range(5000)],
        'email': [fake.unique.email() for _ in range(5000)],
        'signup_date': signup_dates,
        'segment': segments,
        'gender': genders,
        'state': [sc[0] for sc in selected_states_cities],
        'city': [sc[1] for sc in selected_states_cities],
    })
    customers_df['region'] = customers_df['state'].map(state_region_map)
    
    customers_df.to_csv('data/customers.csv', index=False)
    print("Saved data/customers.csv")

    # ---------------------------------------------------------
    # 3. Generate Products Table (100 products)
    # ---------------------------------------------------------
    print("Generating 100 products...")
    product_ids = [f"P{i:03d}" for i in range(1, 101)]
    categories = ['Electronics', 'Apparel', 'Home & Kitchen', 'Beauty', 'Sports']
    product_categories = np.random.choice(categories, size=100, p=[0.2, 0.25, 0.25, 0.15, 0.15])

    # Ensure Product A is P001 and belongs to 'Electronics'
    product_categories[0] = 'Electronics'

    category_product_words = {
        'Electronics': ['Headphones', 'Smartwatch', 'Charger', 'Tablet', 'Speaker', 'Camera', 'Keyboard', 'Mouse', 'Monitor', 'Laptop'],
        'Apparel': ['T-Shirt', 'Jeans', 'Jacket', 'Sweater', 'Socks', 'Sneakers', 'Dress', 'Hat', 'Belt', 'Scarf'],
        'Home & Kitchen': ['Blender', 'Coffee Maker', 'Toaster', 'Air Fryer', 'Knife Set', 'Pan', 'Mug', 'Plate', 'Cushion', 'Lamp'],
        'Beauty': ['Lipstick', 'Mascara', 'Foundation', 'Perfume', 'Face Wash', 'Moisturizer', 'Shampoo', 'Conditioner', 'Sunscreen', 'Serum'],
        'Sports': ['Dumbbells', 'Yoga Mat', 'Water Bottle', 'Running Shoes', 'Backpack', 'Bicycle', 'Tennis Racket', 'Golf Balls', 'Resistance Bands', 'Jump Rope']
    }

    product_names = []
    for i, cat in enumerate(product_categories):
        if i == 0:
            product_names.append("Product A")
        else:
            words = category_product_words[cat]
            product_names.append(f"{fake.word().capitalize()} {np.random.choice(words)}")

    prices = np.random.exponential(scale=150, size=100) + 10
    prices = np.clip(prices, 10, 1200).round(2)
    costs = (prices * np.random.uniform(0.4, 0.7, size=100)).round(2)
    product_suppliers = np.random.choice(supplier_ids, size=100)

    products_df = pd.DataFrame({
        'product_id': product_ids,
        'product_name': product_names,
        'category': product_categories,
        'price': prices,
        'cost': costs,
        'supplier_id': product_suppliers
    })
    products_df.to_csv('data/products.csv', index=False)
    print("Saved data/products.csv")

    # ---------------------------------------------------------
    # 4. Generate Marketing Campaigns Table (5 campaigns)
    # ---------------------------------------------------------
    print("Generating marketing campaigns...")
    campaigns_data = [
        {
            'campaign_id': 'MC001',
            'campaign_name': 'New Year Clearance',
            'start_date': '2025-01-01',
            'end_date': '2025-01-15',
            'discount_percent': 0.15,
            'target_category': 'Apparel'
        },
        {
            'campaign_id': 'MC002',
            'campaign_name': 'Spring Renewal',
            'start_date': '2025-03-10',
            'end_date': '2025-03-25',
            'discount_percent': 0.10,
            'target_category': 'Home & Kitchen'
        },
        {
            'campaign_id': 'MC003',
            'campaign_name': 'June Summer Savings',
            'start_date': '2025-06-01',
            'end_date': '2025-06-30',
            'discount_percent': 0.20,
            'target_category': 'All'
        },
        {
            'campaign_id': 'MC004',
            'campaign_name': 'Back to School',
            'start_date': '2025-08-15',
            'end_date': '2025-09-05',
            'discount_percent': 0.15,
            'target_category': 'Electronics'
        },
        {
            'campaign_id': 'MC005',
            'campaign_name': 'December Holiday Extravaganza',
            'start_date': '2025-12-05',
            'end_date': '2025-12-25',
            'discount_percent': 0.25,
            'target_category': 'All'
        }
    ]
    campaigns_df = pd.DataFrame(campaigns_data)
    campaigns_df.to_csv('data/marketing_campaigns.csv', index=False)
    print("Saved data/marketing_campaigns.csv")

    # ---------------------------------------------------------
    # 5. Generate Inventory Tables
    # ---------------------------------------------------------
    print("Generating current inventory...")
    warehouses = ['WH-East', 'WH-West', 'WH-Central']
    warehouse_locs = np.random.choice(warehouse_locs := warehouses, size=100)
    current_stocks = np.random.randint(50, 500, size=100)
    reorder_points = np.random.randint(20, 100, size=100)
    reorder_quantities = np.random.randint(100, 300, size=100)

    inventory_df = pd.DataFrame({
        'product_id': product_ids,
        'warehouse_location': warehouse_locs,
        'current_stock': current_stocks,
        'reorder_point': reorder_points,
        'reorder_quantity': reorder_quantities
    })
    inventory_df.to_csv('data/inventory.csv', index=False)
    print("Saved data/inventory.csv")

    print("Generating weekly inventory history for 2025...")
    weeks = pd.date_range(start='2025-01-01', end='2025-12-31', freq='W-SUN')
    weekly_records = []
    
    for p_id in product_ids:
        is_prod_a = (p_id == 'P001')
        base_stock = np.random.randint(150, 400)
        reorder_pt = inventory_df.loc[inventory_df['product_id'] == p_id, 'reorder_point'].values[0]
        reorder_qty = inventory_df.loc[inventory_df['product_id'] == p_id, 'reorder_quantity'].values[0]
        stock = base_stock
        
        for wk in weeks:
            wk_str = wk.strftime('%Y-%m-%d')
            
            # March Inventory Shortage for Product A
            if is_prod_a and wk.month == 3:
                stock = 0
                status = 'Out of Stock'
            else:
                weekly_consumption = np.random.randint(10, 40)
                if wk.month == 6:
                    weekly_consumption = int(weekly_consumption * 1.30)
                if wk.month == 12:
                    weekly_consumption = int(weekly_consumption * 1.80)
                
                stock -= weekly_consumption
                if stock <= reorder_pt:
                    stock += reorder_qty
                
                stock = max(stock, 5)
                if stock <= reorder_pt:
                    status = 'Low Stock'
                else:
                    status = 'In Stock'
            
            weekly_records.append({
                'product_id': p_id,
                'week_start_date': wk_str,
                'stock_on_hand': stock,
                'status': status
            })

    weekly_inventory_df = pd.DataFrame(weekly_records)
    weekly_inventory_df.to_csv('data/inventory_history.csv', index=False)
    print("Saved data/inventory_history.csv")

    # ---------------------------------------------------------
    # 6. Generate Sales Records (50,000 sales) with Regional Rules
    # ---------------------------------------------------------
    print("Generating 50,000 sales records with regional behaviors...")
    
    # 6.1 Sample dates in 2025 based on seasonal weights
    dates_2025 = pd.date_range(start='2025-01-01', end='2025-12-31')
    weights = np.ones(len(dates_2025))
    weights[dates_2025.month == 6] = 1.30
    weights[dates_2025.month == 12] = 1.80
    probs = weights / weights.sum()
    
    transaction_dates = np.random.choice(dates_2025, size=50000, p=probs)
    transaction_dates = pd.DatetimeIndex(transaction_dates).sort_values()
    
    transaction_datetimes = []
    for dt in transaction_dates:
        hrs = np.random.randint(8, 22)
        mins = np.random.randint(0, 60)
        secs = np.random.randint(0, 60)
        transaction_datetimes.append(dt.replace(hour=hrs, minute=mins, second=secs))

    # 6.2 Customer selection matching regions
    # - North: Strong Q4 sales (multiplier 2.0 in Q4: Oct, Nov, Dec)
    # - South: Strong Summer sales (multiplier 2.0 in Summer: Jun, Jul, Aug)
    # - East: Consistent demand (multiplier 1.0)
    customer_ids_arr = np.array(customer_ids)
    customer_regions = customers_df['region'].values
    
    # Precompute customer weights for baseline, Q4, and Summer
    w_baseline = np.ones(5000)
    w_q4 = np.where(customer_regions == 'North', 2.0, 1.0)
    w_q4 /= w_q4.sum()
    
    w_summer = np.where(customer_regions == 'South', 2.0, 1.0)
    w_summer /= w_summer.sum()
    
    w_baseline /= w_baseline.sum()
    
    sales_customer_ids = [None] * 50000
    
    # Group indices
    months = np.array([dt.month for dt in transaction_datetimes])
    q4_idx = np.where(np.isin(months, [10, 11, 12]))[0]
    summer_idx = np.where(np.isin(months, [6, 7, 8]))[0]
    baseline_idx = np.where(~np.isin(months, [6, 7, 8, 10, 11, 12]))[0]
    
    # Vectorized sampling of customers
    sampled_q4_cust = np.random.choice(customer_ids_arr, size=len(q4_idx), p=w_q4)
    sampled_summer_cust = np.random.choice(customer_ids_arr, size=len(summer_idx), p=w_summer)
    sampled_baseline_cust = np.random.choice(customer_ids_arr, size=len(baseline_idx), p=w_baseline)
    
    for idx, cust_id in zip(q4_idx, sampled_q4_cust):
        sales_customer_ids[idx] = cust_id
    for idx, cust_id in zip(summer_idx, sampled_summer_cust):
        sales_customer_ids[idx] = cust_id
    for idx, cust_id in zip(baseline_idx, sampled_baseline_cust):
        sales_customer_ids[idx] = cust_id

    # Create mapping of customer ID to region for fast lookup
    customer_region_map = customers_df.set_index('customer_id')['region'].to_dict()
    sales_regions = [customer_region_map[cid] for cid in sales_customer_ids]

    # 6.3 Product selection matching rules (March shortage & West premium purchase)
    # Base popularity weights for products
    product_weights = np.random.exponential(scale=2.0, size=100) + 0.1
    product_weights /= product_weights.sum()

    # Precompute the 4 configurations of product weights:
    # 1. Normal (non-March, non-West)
    pw_normal = product_weights.copy()
    pw_normal /= pw_normal.sum()
    
    # 2. West (non-March, West): price > 200 items get 3.0x multiplier
    pw_west = product_weights.copy()
    pw_west[products_df['price'].values > 200] *= 3.0
    pw_west /= pw_west.sum()
    
    # 3. March (March, non-West): P001 (index 0) gets 0.0 weight
    pw_march = product_weights.copy()
    pw_march[0] = 0.0
    pw_march /= pw_march.sum()
    
    # 4. March West (March, West): P001 gets 0.0, price > 200 gets 3.0x
    pw_march_west = product_weights.copy()
    pw_march_west[0] = 0.0
    pw_march_west[products_df['price'].values > 200] *= 3.0
    pw_march_west /= pw_march_west.sum()

    sales_product_ids = [None] * 50000
    
    # Determine configuration for each transaction
    # Let's get groups
    is_march = (months == 3)
    is_west = (np.array(sales_regions) == 'West')
    
    g_normal_idx = np.where(~is_march & ~is_west)[0]
    g_west_idx = np.where(~is_march & is_west)[0]
    g_march_idx = np.where(is_march & ~is_west)[0]
    g_march_west_idx = np.where(is_march & is_west)[0]
    
    sampled_normal_prod = np.random.choice(product_ids, size=len(g_normal_idx), p=pw_normal)
    sampled_west_prod = np.random.choice(product_ids, size=len(g_west_idx), p=pw_west)
    sampled_march_prod = np.random.choice(product_ids, size=len(g_march_idx), p=pw_march)
    sampled_march_west_prod = np.random.choice(product_ids, size=len(g_march_west_idx), p=pw_march_west)
    
    for idx, p_id in zip(g_normal_idx, sampled_normal_prod):
        sales_product_ids[idx] = p_id
    for idx, p_id in zip(g_west_idx, sampled_west_prod):
        sales_product_ids[idx] = p_id
    for idx, p_id in zip(g_march_idx, sampled_march_prod):
        sales_product_ids[idx] = p_id
    for idx, p_id in zip(g_march_west_idx, sampled_march_west_prod):
        sales_product_ids[idx] = p_id

    # Quantities (mostly 1 or 2 items per order)
    quantities = np.random.choice([1, 2, 3, 4, 5], size=50000, p=[0.55, 0.25, 0.12, 0.06, 0.02])

    product_price_map = products_df.set_index('product_id')['price'].to_dict()
    product_category_map = products_df.set_index('product_id')['category'].to_dict()

    unit_prices = np.array([product_price_map[pid] for pid in sales_product_ids])
    discount_applied = np.zeros(50000)

    # Apply campaign discounts
    campaign_details = [
        ('2025-01-01', '2025-01-15', 'Apparel', 0.15),
        ('2025-03-10', '2025-03-25', 'Home & Kitchen', 0.10),
        ('2025-06-01', '2025-06-30', 'All', 0.20),
        ('2025-08-15', '2025-09-05', 'Electronics', 0.15),
        ('2025-12-05', '2025-12-25', 'All', 0.25)
    ]

    for start, end, target, disc in campaign_details:
        start_dt = datetime.strptime(start, '%Y-%m-%d')
        end_dt = datetime.strptime(end, '%Y-%m-%d').replace(hour=23, minute=59, second=59)
        
        date_mask = np.array([(dt >= start_dt and dt <= end_dt) for dt in transaction_datetimes])
        if target == 'All':
            cat_mask = np.ones(50000, dtype=bool)
        else:
            cat_mask = np.array([product_category_map[pid] == target for pid in sales_product_ids])
            
        combined_mask = date_mask & cat_mask
        discount_applied = np.where(combined_mask, disc, discount_applied)

    total_amounts = (unit_prices * quantities * (1.0 - discount_applied)).round(2)
    payment_methods = np.random.choice(['Credit Card', 'PayPal', 'Debit Card', 'Cash'], size=50000, p=[0.55, 0.25, 0.15, 0.05])

    sales_df = pd.DataFrame({
        'transaction_id': [f"T{i:05d}" for i in range(1, 50001)],
        'transaction_date': [dt.strftime('%Y-%m-%d %H:%M:%S') for dt in transaction_datetimes],
        'customer_id': sales_customer_ids,
        'product_id': sales_product_ids,
        'quantity': quantities,
        'unit_price': unit_prices,
        'discount_applied': discount_applied,
        'total_amount': total_amounts,
        'payment_method': payment_methods
    })
    
    sales_df.to_csv('data/sales.csv', index=False)
    print("Saved data/sales.csv")

    # ---------------------------------------------------------
    # 7. Generate Returns Table (~4% of sales)
    # ---------------------------------------------------------
    print("Generating returns table (~4% of sales)...")
    # Sample transactions to return
    return_indices = np.random.choice(50000, size=2000, replace=False)
    return_indices.sort()
    
    return_ids = [f"R{i:05d}" for i in range(1, 2001)]
    ref_transactions = sales_df.iloc[return_indices]
    
    return_dates = []
    for t_date_str in ref_transactions['transaction_date']:
        t_date = datetime.strptime(t_date_str, '%Y-%m-%d %H:%M:%S')
        r_delay_days = np.random.randint(1, 15)
        r_delay_hours = np.random.randint(0, 24)
        r_date = t_date + timedelta(days=r_delay_days, hours=r_delay_hours)
        # cap return date to 2025-12-31 for consistency
        if r_date > datetime(2025, 12, 31, 23, 59, 59):
            r_date = datetime(2025, 12, 31, 23, 59, 59)
        return_dates.append(r_date.strftime('%Y-%m-%d %H:%M:%S'))

    reasons = ['Defective', 'Changed Mind', 'Incorrect Size', 'Damaged in Transit', 'Did Not Fit']
    return_reasons = np.random.choice(reasons, size=2000, p=[0.20, 0.35, 0.25, 0.10, 0.10])
    
    returns_df = pd.DataFrame({
        'return_id': return_ids,
        'transaction_id': ref_transactions['transaction_id'].values,
        'product_id': ref_transactions['product_id'].values,
        'return_date': return_dates,
        'reason': return_reasons,
        'refund_amount': ref_transactions['total_amount'].values
    })
    returns_df.to_csv('data/returns.csv', index=False)
    print("Saved data/returns.csv")

    # ---------------------------------------------------------
    # 8. Generate Warehouse Events Table
    # ---------------------------------------------------------
    print("Generating warehouse events table...")
    events_data = [
        {
            'event_date': '2025-03-05',
            'event_name': 'Warehouse A Delay',
            'description': 'Equipment breakdown in Warehouse A causing processing delays of up to 48 hours for inbound shipments.'
        },
        {
            'event_date': '2025-08-10',
            'event_name': 'Inventory Audit',
            'description': 'Annual mid-year physical stock audit. All shipping and receiving halted for 24 hours.'
        },
        {
            'event_date': '2025-11-20',
            'event_name': 'Shipping Congestion',
            'description': 'Peak pre-holiday carrier congestion leading to minor transit delays at regional distribution hubs.'
        }
    ]
    warehouse_events_df = pd.DataFrame(events_data)
    warehouse_events_df.to_csv('data/warehouse_events.csv', index=False)
    print("Saved data/warehouse_events.csv")

    # ---------------------------------------------------------
    # 9. Generate Reviews Table (~10% of sales)
    # ---------------------------------------------------------
    print("Generating reviews table (~10% of sales)...")
    review_indices = np.random.choice(50000, size=5000, replace=False)
    review_indices.sort()
    
    ref_sales_reviews = sales_df.iloc[review_indices]
    review_ids = [f"REV{i:05d}" for i in range(1, 5001)]
    
    review_dates = []
    for t_date_str in ref_sales_reviews['transaction_date']:
        t_date = datetime.strptime(t_date_str, '%Y-%m-%d %H:%M:%S')
        rev_delay_days = np.random.randint(1, 31)
        rev_date = t_date + timedelta(days=rev_delay_days)
        if rev_date > datetime(2025, 12, 31, 23, 59, 59):
            rev_date = datetime(2025, 12, 31, 23, 59, 59)
        review_dates.append(rev_date.strftime('%Y-%m-%d %H:%M:%S'))

    ratings_choices = [1, 2, 3, 4, 5]
    ratings_probs = [0.05, 0.08, 0.15, 0.32, 0.40]
    review_ratings = np.random.choice(ratings_choices, size=5000, p=ratings_probs)
    
    review_templates = {
        5: [
            "Absolutely fantastic! Exceeded my expectations.",
            "Incredible quality. Will definitely purchase again.",
            "Perfect. Highly recommend to everyone.",
            "Really great value for money. Very happy!",
            "Super fast shipping and top notch quality."
        ],
        4: [
            "Very good quality, matches description nicely.",
            "Decent purchase, works well for its purpose.",
            "Satisfied with this. Pretty close to what I expected.",
            "Nice product. Would buy again.",
            "Overall positive experience. A solid product."
        ],
        3: [
            "It is average. Nothing outstanding.",
            "Decent for the price but has minor issues.",
            "Okay product. Quality could be slightly better.",
            "Works fine, but not quite as premium as pictured.",
            "Standard product, performs as expected."
        ],
        2: [
            "Disappointed. Quality is subpar.",
            "Not as described, does not work very well.",
            "Expected more for this price. Quite cheap feeling.",
            "Below average performance. Would not recommend.",
            "Felt a bit flimsy and failed to meet expectations."
        ],
        1: [
            "Terrible! Broke within a couple of days.",
            "Complete waste of money. Do not buy!",
            "Poor quality and horrible experience.",
            "Avoid this at all costs. Very cheap construction.",
            "Absolute garbage. Did not work at all."
        ]
    }
    
    review_texts = [np.random.choice(review_templates[r]) for r in review_ratings]
    
    reviews_df = pd.DataFrame({
        'review_id': review_ids,
        'customer_id': ref_sales_reviews['customer_id'].values,
        'product_id': ref_sales_reviews['product_id'].values,
        'rating': review_ratings,
        'review_text': review_texts,
        'review_date': review_dates
    })
    reviews_df.to_csv('data/reviews.csv', index=False)
    print("Saved data/reviews.csv")
    
    print("Successfully generated all synthetic datasets!")

if __name__ == '__main__':
    main()
