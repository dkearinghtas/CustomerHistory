# Invoice Viewer Flask App

A Flask web application to view and analyze invoice data in two ways:
- **Chronological View**: All invoices sorted by date (newest first) with search capability
- **Grouped View**: Purchase counts by customer and product

## Setup Instructions

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Add Your CSV Data
Place your CSV file in the `data/` folder and name it `invoices.csv`:
```
InvoiceViewer/
├── data/
│   └── invoices.csv  ← Put your file here
├── app.py
├── data_loader.py
└── ...
```

### 3. Run the App
```bash
python app.py
```

The app will start on `http://localhost:5000`

## Features

### Chronological View
- Displays all invoices sorted by date (newest first)
- Columns: Invoice Number, Invoice Date, Part Number, Description, Quantity, Price, Labor
- Filter by Invoice Number

### Grouped View
- Shows how many times each product was purchased per customer
- Displays total quantity, total price, and total labor per group
- Filter by Customer name

## Column Mapping

The app uses the following columns from your CSV:
- Invoice Number: `INVOICE_NUMBER`
- Invoice Date: `HISTHDR.INVOICE_DATE`
- Part Number: `ITEM_NUMBER`
- Description: `DESCRIPTION`
- Quantity: `QUANTITY`
- Price: `SELL_PRICE`
- Labor: `SELL_LABOR`

## Live Data (Microsoft Fabric Semantic Model)

You can now run the app against a Fabric semantic model table using the following environment variables:

- `USE_LIVE_DATA=true` (or `1`, `yes`)
- `FABRIC_SQL_CONNECTION` = ODBC/SQL connection string to Fabric table endpoint
- `FABRIC_TABLE_NAME` = table name (default: `invoices`)

Example:

```powershell
setx USE_LIVE_DATA true
setx FABRIC_SQL_CONNECTION "Driver={ODBC Driver 18 for SQL Server};Server=your_server;Database=your_db;UID=your_user;PWD=your_pass;Encrypt=yes;TrustServerCertificate=no;"
setx FABRIC_TABLE_NAME "invoice_semantic_table"
```

Then run:

```bash
python app.py
```

For local CSV fallback, set `USE_LIVE_DATA=false` (default) and keep `data/invoices.csv` in place.

## Files

- `app.py` - Main Flask application with routes
- `data_loader.py` - CSV loading and data processing
- `requirements.txt` - Python dependencies
- `templates/` - HTML templates
  - `index.html` - Home page
  - `chronological.html` - Chronological view
  - `grouped.html` - Grouped view
- `static/` - CSS styling
