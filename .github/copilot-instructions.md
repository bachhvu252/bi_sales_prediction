# BI Sales Prediction - Copilot Instructions

## Project Overview

This is an **Odoo 17+ module** (`bi_sales_prediction`) that provides machine learning-based sales forecasting using historical sale order data.

## Architecture

```
bi_sales_prediction/
├── __manifest__.py      # Module metadata, dependencies, assets registration
├── models/
│   └── sales_predictor.py  # Core ML logic (TransientModel)
└── static/src/           # Frontend assets (JS/XML/CSS for OWL components)
```

### Key Components

- **SalesPredictor** (`models/sales_predictor.py`): A `TransientModel` that:
  - Fetches confirmed sale orders via Odoo ORM (`sale.order`)
  - Aggregates data monthly using pandas
  - Trains a `LinearRegression` model from scikit-learn
  - Returns Chart.js-compatible data structure for frontend visualization

## Odoo-Specific Patterns

### Model Conventions
- Use `TransientModel` for temporary/wizard-like operations (no persistent storage)
- Model names follow `module.name` pattern: `bi.sales.predictor`
- Use `@api.model` decorator for methods not tied to specific records
- Access other models via `self.env['model.name']`

### Manifest Structure
- Dependencies declared in `depends`: `['base', 'sale', 'web']`
- Python packages in `external_dependencies.python`: `['pandas', 'sklearn']`
- Frontend assets registered under `assets.web.assets_backend`

### Data Access Pattern
```python
# Standard Odoo search pattern
orders = self.env['sale.order'].search([
    ('state', 'in', ['sale', 'done']),
    ('field', 'operator', value)
])
```

## Development Workflow

### Install External Dependencies
```bash
pip install pandas scikit-learn
```

### Module Installation/Update
```bash
# In Odoo directory
python odoo-bin -u bi_sales_prediction -d <database_name>
```

### Frontend Assets
- Place OWL components in `static/src/js/`
- XML templates in `static/src/xml/`
- Styles in `static/src/css/`
- Assets auto-load via manifest `web.assets_backend` glob patterns

## Data Flow

1. **Backend**: `get_prediction_data()` → queries `sale.order` → pandas aggregation → sklearn prediction
2. **Frontend**: Calls RPC to `bi.sales.predictor` → receives `{labels, historical, predicted}` → renders Chart.js

## Adding New Features

When extending predictions:
- Add new methods to `SalesPredictor` class with `@api.model` decorator
- Return data as JSON-serializable dicts for frontend consumption
- For new models, create files in `models/` and import in `models/__init__.py`
