from odoo import models, api, fields
from datetime import datetime, timedelta


class SalesPredictor(models.TransientModel):
    _name = 'bi.sales.predictor'
    _description = 'Sales Prediction Logic'

    @api.model
    def get_prediction_data(self, months_to_predict=6):
        # Import here to avoid issues during module loading
        import pandas as pd
        from sklearn.linear_model import LinearRegression
        import numpy as np
        
        # 1. Fetch Historical Data
        orders = self.env['sale.order'].search([
            ('state', 'in', ['sale', 'done']),
            ('date_order', '!=', False)
        ])
        
        if not orders:
            return {'error': 'No historical sales data found.'}

        # 2. Preprocess Data using Pandas
        data = [{'date': o.date_order, 'amount': o.amount_total} for o in orders]
        df = pd.DataFrame(data)
        df['date'] = pd.to_datetime(df['date'])
        
        # Group by month - keep the period for labels
        df['month_period'] = df['date'].dt.to_period('M')
        monthly_sales = df.groupby('month_period')['amount'].sum().reset_index()
        monthly_sales = monthly_sales.sort_values('month_period')
        
        # Create numeric index for regression
        monthly_sales['month_index'] = range(len(monthly_sales))

        # 3. Train Model (Simple Linear Regression)
        X = monthly_sales[['month_index']].values
        y = monthly_sales['amount'].values
        
        model = LinearRegression()
        model.fit(X, y)

        # 4. Predict Future
        last_index = monthly_sales['month_index'].max()
        last_period = monthly_sales['month_period'].max()
        
        future_indices = np.array([[last_index + i] for i in range(1, months_to_predict + 1)])
        predictions = model.predict(future_indices)

        # 5. Format for Frontend (Chart.js)
        # Historical labels from periods
        historical_labels = [str(p) for p in monthly_sales['month_period']]
        
        # Future labels - generate next months
        future_labels = []
        current_period = last_period
        for i in range(months_to_predict):
            current_period = current_period + 1
            future_labels.append(str(current_period))
        
        return {
            'labels': historical_labels + future_labels,
            'historical': monthly_sales['amount'].tolist(),
            'predicted': [None] * len(historical_labels) + predictions.tolist()
        }

    @api.model
    def get_dashboard_data(self):
        """Get comprehensive dashboard data including KPIs, top products, customers, etc."""
        import pandas as pd
        from datetime import datetime
        
        today = datetime.now()
        current_year = today.year
        current_month = today.month
        
        # Get all confirmed orders
        orders = self.env['sale.order'].search([
            ('state', 'in', ['sale', 'done']),
            ('date_order', '!=', False)
        ])
        
        if not orders:
            return {
                'kpis': {
                    'total_revenue': 0,
                    'monthly_revenue': 0,
                    'yearly_revenue': 0,
                    'total_orders': 0,
                    'monthly_orders': 0,
                    'total_customers': 0,
                    'avg_order_value': 0,
                },
                'top_products': [],
                'top_customers': [],
                'monthly_revenue_chart': {'labels': [], 'data': []},
                'orders_by_status': [],
            }
        
        # Calculate KPIs
        total_revenue = sum(o.amount_total for o in orders)
        total_orders = len(orders)
        
        # Monthly revenue (current month)
        monthly_orders = orders.filtered(
            lambda o: o.date_order.year == current_year and o.date_order.month == current_month
        )
        monthly_revenue = sum(o.amount_total for o in monthly_orders)
        
        # Yearly revenue (current year)
        yearly_orders = orders.filtered(lambda o: o.date_order.year == current_year)
        yearly_revenue = sum(o.amount_total for o in yearly_orders)
        
        # Unique customers
        customer_ids = set(o.partner_id.id for o in orders)
        total_customers = len(customer_ids)
        
        # Average order value
        avg_order_value = total_revenue / total_orders if total_orders > 0 else 0
        
        # Top 10 Products by Revenue
        product_sales = {}
        for order in orders:
            for line in order.order_line:
                product_name = line.product_id.name or 'Unknown'
                if product_name not in product_sales:
                    product_sales[product_name] = {'quantity': 0, 'revenue': 0}
                product_sales[product_name]['quantity'] += line.product_uom_qty
                product_sales[product_name]['revenue'] += line.price_subtotal
        
        top_products = sorted(
            [{'name': k, 'quantity': v['quantity'], 'revenue': v['revenue']} 
             for k, v in product_sales.items()],
            key=lambda x: x['revenue'],
            reverse=True
        )[:10]
        
        # Top 10 Customers by Revenue
        customer_sales = {}
        for order in orders:
            customer_name = order.partner_id.name or 'Unknown'
            if customer_name not in customer_sales:
                customer_sales[customer_name] = {'orders': 0, 'revenue': 0}
            customer_sales[customer_name]['orders'] += 1
            customer_sales[customer_name]['revenue'] += order.amount_total
        
        top_customers = sorted(
            [{'name': k, 'orders': v['orders'], 'revenue': v['revenue']} 
             for k, v in customer_sales.items()],
            key=lambda x: x['revenue'],
            reverse=True
        )[:10]
        
        # Monthly Revenue Chart (last 12 months)
        data = [{'date': o.date_order, 'amount': o.amount_total} for o in orders]
        df = pd.DataFrame(data)
        df['date'] = pd.to_datetime(df['date'])
        df['month_period'] = df['date'].dt.to_period('M')
        monthly_data = df.groupby('month_period')['amount'].sum().reset_index()
        monthly_data = monthly_data.sort_values('month_period').tail(12)
        
        monthly_revenue_chart = {
            'labels': [str(p) for p in monthly_data['month_period']],
            'data': monthly_data['amount'].tolist()
        }
        
        # Orders by Status
        all_orders = self.env['sale.order'].search([])
        status_count = {}
        status_labels = {
            'draft': 'Quotation',
            'sent': 'Quotation Sent',
            'sale': 'Sales Order',
            'done': 'Locked',
            'cancel': 'Cancelled'
        }
        for order in all_orders:
            status = status_labels.get(order.state, order.state)
            status_count[status] = status_count.get(status, 0) + 1
        
        orders_by_status = [{'status': k, 'count': v} for k, v in status_count.items()]
        
        return {
            'kpis': {
                'total_revenue': round(total_revenue, 2),
                'monthly_revenue': round(monthly_revenue, 2),
                'yearly_revenue': round(yearly_revenue, 2),
                'total_orders': total_orders,
                'monthly_orders': len(monthly_orders),
                'total_customers': total_customers,
                'avg_order_value': round(avg_order_value, 2),
            },
            'top_products': top_products,
            'top_customers': top_customers,
            'monthly_revenue_chart': monthly_revenue_chart,
            'orders_by_status': orders_by_status,
        }