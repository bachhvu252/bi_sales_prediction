{
    'name': 'BI Sales Prediction',
    'version': '1.0',
    'category': 'Sales',
    'summary': 'Predict future sales using Machine Learning',
    'depends': ['base', 'sale', 'web'],
    'external_dependencies': {
       'python': ['pandas', 'sklearn'],
    },
    'data': [
        'views/sales_prediction_menu.xml',
    ],
    'demo': [
        'data/demo_data.xml',
    ],
    'assets': {
        'web.assets_backend': [
            '/web/static/lib/Chart/Chart.js',
            'bi_sales_prediction/static/src/xml/sales_dashboard.xml',
            'bi_sales_prediction/static/src/js/sales_dashboard.js',
            'bi_sales_prediction/static/src/css/style.css',
        ],
    },
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}