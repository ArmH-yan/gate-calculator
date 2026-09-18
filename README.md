# Gate Calculator

Streamlit app for gate/door BOM (bill of materials) and pricing.

## Setup

```bash
python -m venv venv
venv\Scripts\activate      # Windows
pip install -r requirements.txt
```

## Run

```bash
streamlit run gate_calculator.py
```

## Features

- Editable BOM table with 21 preloaded items
- Quick-edit panel for single-item updates
- Auto-calculated totals per row (Size x Qty x Gin)
- Discount % with rounding up to nearest 1000
- Bilingual labels (English / Armenian)
