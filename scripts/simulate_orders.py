# ============================================
# BI Sales Prediction - Order Simulation Script
# ============================================
# This script creates realistic sales orders in Odoo
# Run this script while Odoo server is running
#
# Usage:
#   cd "C:\Program Files\Odoo 19.0.20250918\server"
#   & "C:\Program Files\Odoo 19.0.20250918\python\python.exe" odoo\addons\bi_sales_prediction\scripts\simulate_orders.py
# ============================================

import xmlrpc.client
import random
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

# ============================================
# CONFIGURATION - Update these values
# ============================================
ODOO_URL = 'http://localhost:8069'
ODOO_DB = 'OnewaymobileDB'
ODOO_USER = 'admin'
ODOO_PASSWORD = 'admin'  # Change this to your admin password

# Simulation settings
NUM_MONTHS = 12  # Number of months of historical data to create
ORDERS_PER_MONTH_MIN = 3
ORDERS_PER_MONTH_MAX = 8
LINES_PER_ORDER_MIN = 1
LINES_PER_ORDER_MAX = 5

# ============================================
# XMLRPC Connection
# ============================================
def connect_odoo():
    """Establish connection to Odoo via XML-RPC"""
    common = xmlrpc.client.ServerProxy(f'{ODOO_URL}/xmlrpc/2/common')
    
    # Authenticate
    uid = common.authenticate(ODOO_DB, ODOO_USER, ODOO_PASSWORD, {})
    if not uid:
        raise Exception("Authentication failed! Check your credentials.")
    
    print(f"✓ Connected to Odoo as user ID: {uid}")
    
    models = xmlrpc.client.ServerProxy(f'{ODOO_URL}/xmlrpc/2/object')
    return uid, models

def execute(models, uid, model, method, *args, **kwargs):
    """Execute a method on an Odoo model"""
    return models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD, model, method, args, kwargs)

# ============================================
# Helper Functions
# ============================================
def get_or_create_customer(models, uid):
    """Get or create a demo customer"""
    # Search for existing demo customers
    partner_ids = execute(models, uid, 'res.partner', 'search', 
        [['name', 'ilike', 'Demo Customer']], {'limit': 5})
    
    if partner_ids:
        print(f"✓ Found {len(partner_ids)} existing demo customers")
        return partner_ids
    
    # Create demo customers
    demo_customers = [
        {'name': 'Demo Customer - Retail Corp', 'customer_rank': 1, 'email': 'retail@demo.com'},
        {'name': 'Demo Customer - Wholesale Inc', 'customer_rank': 1, 'email': 'wholesale@demo.com'},
        {'name': 'Demo Customer - Enterprise Ltd', 'customer_rank': 1, 'email': 'enterprise@demo.com'},
        {'name': 'Demo Customer - Small Business', 'customer_rank': 1, 'email': 'smallbiz@demo.com'},
        {'name': 'Demo Customer - Startup Hub', 'customer_rank': 1, 'email': 'startup@demo.com'},
    ]
    
    partner_ids = []
    for customer in demo_customers:
        pid = execute(models, uid, 'res.partner', 'create', customer)
        partner_ids.append(pid)
        print(f"  Created customer: {customer['name']}")
    
    print(f"✓ Created {len(partner_ids)} demo customers")
    return partner_ids

def get_or_create_products(models, uid):
    """Get or create demo products"""
    # Search for saleable products
    product_ids = execute(models, uid, 'product.product', 'search', 
        [['sale_ok', '=', True]], {'limit': 10})
    
    if product_ids:
        print(f"✓ Found {len(product_ids)} existing products")
        return product_ids
    
    # Create demo products
    demo_products = [
        {'name': 'Demo Product - Basic', 'type': 'consu', 'list_price': 99.99, 'sale_ok': True},
        {'name': 'Demo Product - Standard', 'type': 'consu', 'list_price': 249.99, 'sale_ok': True},
        {'name': 'Demo Product - Premium', 'type': 'consu', 'list_price': 499.99, 'sale_ok': True},
        {'name': 'Demo Product - Enterprise', 'type': 'consu', 'list_price': 999.99, 'sale_ok': True},
        {'name': 'Demo Service - Consulting', 'type': 'service', 'list_price': 150.00, 'sale_ok': True},
    ]
    
    product_ids = []
    for product in demo_products:
        # Create product template first
        tmpl_id = execute(models, uid, 'product.template', 'create', product)
        # Get the product.product ID
        pid = execute(models, uid, 'product.product', 'search', 
            [['product_tmpl_id', '=', tmpl_id]], {'limit': 1})
        if pid:
            product_ids.append(pid[0])
            print(f"  Created product: {product['name']}")
    
    print(f"✓ Created {len(product_ids)} demo products")
    return product_ids

def create_sale_order(models, uid, partner_id, product_ids, order_date):
    """Create a single sale order with random products"""
    # Create the order
    order_vals = {
        'partner_id': partner_id,
        'date_order': order_date.strftime('%Y-%m-%d %H:%M:%S'),
    }
    
    order_id = execute(models, uid, 'sale.order', 'create', order_vals)
    
    # Add random order lines
    num_lines = random.randint(LINES_PER_ORDER_MIN, LINES_PER_ORDER_MAX)
    selected_products = random.sample(product_ids, min(num_lines, len(product_ids)))
    
    for product_id in selected_products:
        # Get product info
        product = execute(models, uid, 'product.product', 'read', 
            [product_id], {'fields': ['name', 'list_price', 'uom_id']})[0]
        
        # Random quantity and slight price variation
        qty = random.randint(1, 10)
        price = product['list_price'] * random.uniform(0.9, 1.1)
        
        line_vals = {
            'order_id': order_id,
            'product_id': product_id,
            'product_uom_qty': qty,
            'price_unit': round(price, 2),
        }
        execute(models, uid, 'sale.order.line', 'create', line_vals)
    
    # Confirm the order
    execute(models, uid, 'sale.order', 'action_confirm', [order_id])
    
    return order_id

def simulate_orders(models, uid, partner_ids, product_ids):
    """Generate orders for the past several months"""
    today = datetime.now()
    total_orders = 0
    total_revenue = 0.0
    
    print("\n📊 Generating sales orders...")
    print("-" * 50)
    
    for month_offset in range(NUM_MONTHS, 0, -1):
        month_date = today - relativedelta(months=month_offset)
        month_name = month_date.strftime('%Y-%m')
        
        # Random number of orders this month (with slight growth trend)
        growth_factor = 1 + (NUM_MONTHS - month_offset) * 0.05
        num_orders = int(random.randint(ORDERS_PER_MONTH_MIN, ORDERS_PER_MONTH_MAX) * growth_factor)
        
        month_revenue = 0.0
        
        for i in range(num_orders):
            # Random day in the month
            day = random.randint(1, 28)
            hour = random.randint(8, 18)
            minute = random.randint(0, 59)
            order_date = month_date.replace(day=day, hour=hour, minute=minute)
            
            # Random customer
            partner_id = random.choice(partner_ids)
            
            # Create order
            order_id = create_sale_order(models, uid, partner_id, product_ids, order_date)
            
            # Get order total
            order = execute(models, uid, 'sale.order', 'read', 
                [order_id], {'fields': ['amount_total', 'name']})[0]
            month_revenue += order['amount_total']
            total_orders += 1
        
        total_revenue += month_revenue
        print(f"  {month_name}: {num_orders} orders, ${month_revenue:,.2f} revenue")
    
    print("-" * 50)
    print(f"\n✅ Simulation Complete!")
    print(f"   Total Orders: {total_orders}")
    print(f"   Total Revenue: ${total_revenue:,.2f}")
    print(f"   Average Order Value: ${total_revenue/total_orders:,.2f}")

def show_summary(models, uid):
    """Show summary of all sales orders"""
    # Count orders by state
    states = ['draft', 'sent', 'sale', 'done', 'cancel']
    print("\n📈 Order Summary by Status:")
    print("-" * 30)
    
    for state in states:
        count = execute(models, uid, 'sale.order', 'search_count', 
            [['state', '=', state]])
        if count > 0:
            print(f"  {state.capitalize()}: {count}")
    
    # Total confirmed revenue
    orders = execute(models, uid, 'sale.order', 'search_read',
        [['state', 'in', ['sale', 'done']]],
        {'fields': ['amount_total']})
    
    total = sum(o['amount_total'] for o in orders)
    print(f"\n💰 Total Confirmed Revenue: ${total:,.2f}")

# ============================================
# Main Execution
# ============================================
def main():
    print("=" * 50)
    print("🚀 Odoo Sales Order Simulation Script")
    print("=" * 50)
    
    try:
        # Connect to Odoo
        uid, models = connect_odoo()
        
        # Get or create demo data
        partner_ids = get_or_create_customer(models, uid)
        product_ids = get_or_create_products(models, uid)
        
        if not partner_ids or not product_ids:
            print("❌ Error: Could not find or create customers/products")
            return
        
        # Run simulation
        simulate_orders(models, uid, partner_ids, product_ids)
        
        # Show summary
        show_summary(models, uid)
        
        print("\n🎉 Done! Refresh your Sales Prediction dashboard to see the data.")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nTroubleshooting:")
        print("  1. Make sure Odoo server is running")
        print("  2. Check ODOO_URL, ODOO_DB, ODOO_USER, ODOO_PASSWORD")
        print("  3. Ensure the user has sales access rights")

if __name__ == '__main__':
    main()
