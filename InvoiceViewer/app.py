from flask import Flask, render_template, request
from data_loader import InvoiceDataLoader
from pathlib import Path
import os
import pandas as pd

app = Flask(__name__)

# Use Microsoft Fabric semantic model connection when enabled, otherwise fall back to CSV
csv_file = os.path.join(os.path.dirname(__file__), 'data', 'invoices.csv')
use_live = os.getenv('USE_LIVE_DATA', 'False').lower() in ('1', 'true', 'yes')
connection_string = os.getenv('FABRIC_SQL_CONNECTION', '')
table_name = os.getenv('FABRIC_TABLE_NAME', 'invoices')

if use_live:
    data_loader = InvoiceDataLoader(use_live=True, connection_string=connection_string, table_name=table_name)
else:
    data_loader = InvoiceDataLoader(csv_path=csv_file)


@app.route('/')
def index():
    """Home page with navigation"""
    return render_template('index.html')

@app.route('/chronological')
def chronological():
    """Chronological view of invoices"""
    df = data_loader.get_chronological_view()
    
    # Optional filters
    invoice_num = request.args.get('invoice_number')
    if invoice_num:
        df = df[df['INVOICE_NUMBER'].astype(str).str.contains(str(invoice_num), na=False)]
    
    customer = request.args.get('customer')
    if customer:
        customer_col = 'HISTHDR.LAST_NAME' if 'HISTHDR.LAST_NAME' in df.columns else 'LAST_NAME'
        df = df[df[customer_col] == customer]
    
    # Limit to last 200 rows
    df = df.head(200)
    
    # Convert to list of dictionaries for template
    invoices = []
    for _, row in df.iterrows():
        invoices.append({
            'invoice_number': row['INVOICE_NUMBER'],
            'invoice_date': row['HISTHDR.INVOICE_DATE'].strftime('%m/%d/%y') if pd.notna(row['HISTHDR.INVOICE_DATE']) else 'N/A',
            'part_number': row['ITEM_NUMBER'],
            'description': row['DESCRIPTION'],
            'quantity': f"{row['QUANTITY']:.0f}" if pd.notna(row['QUANTITY']) else '0',
            'price': f"${row['SELL_PRICE']:.2f}" if pd.notna(row['SELL_PRICE']) else '$0.00',
            'labor': f"${row['SELL_LABOR']:.2f}" if pd.notna(row['SELL_LABOR']) else '$0.00',
        })
    
    # Get unique customers and invoices for dropdowns
    customers = data_loader.get_unique_customers()
    invoice_options = data_loader.get_unique_invoice_numbers()
    
    return render_template('chronological.html', invoices=invoices, invoice_options=invoice_options, customers=customers)

@app.route('/grouped')
def grouped():
    """Grouped view by customer with parts and labor separated"""
    customer = request.args.get('customer')
    
    # Filter by customer
    if customer:
        customer_df = data_loader.df[data_loader.df['HISTHDR.LAST_NAME'] == customer]
    else:
        customer_df = data_loader.df
    
    # Get parts and labor grouped views
    parts_df = data_loader.get_parts_grouped_view(customer_df)
    labor_df = data_loader.get_labor_grouped_view(customer_df)
    
    # Convert parts to list of dictionaries
    parts = []
    for _, row in parts_df.iterrows():
        parts.append({
            'description': row['Description'],
            'purchase_count': int(row['Purchase Count']),
            'total_quantity': f"{row['Total Quantity']:.0f}" if pd.notna(row['Total Quantity']) else '0',
            'max_price': f"${row['Max Price']:.2f}" if pd.notna(row['Max Price']) else '$0.00',
            'recent_price': f"${row['Most Recent Price']:.2f}" if pd.notna(row['Most Recent Price']) else '$0.00',
        })
    
    # Convert labor to list of dictionaries
    labor = []
    for _, row in labor_df.iterrows():
        labor.append({
            'description': row['Description'],
            'labor_count': int(row['Labor Count']),
            'total_quantity': f"{row['Total Quantity']:.0f}" if pd.notna(row['Total Quantity']) else '0',
            'max_labor': f"${row['Max Labor']:.2f}" if pd.notna(row['Max Labor']) else '$0.00',
            'recent_labor': f"${row['Most Recent Labor']:.2f}" if pd.notna(row['Most Recent Labor']) else '$0.00',
        })
    
    # Get unique customers for dropdown
    customers = data_loader.get_unique_customers()
    
    return render_template('grouped.html', parts=parts, labor=labor, customers=customers, selected_customer=customer)

@app.route('/item')
def item_view():
    """Item lookup view - sales by item number"""
    item_number = request.args.get('item_number')
    
    if item_number:
        # Filter data by item_number and sort by date descending
        filtered_df = data_loader.df[data_loader.df['ITEM_NUMBER'] == item_number].sort_values('HISTHDR.INVOICE_DATE', ascending=False)
        
        # Convert to list of dictionaries
        data = []
        for _, row in filtered_df.iterrows():
            customer = f"{row['HISTHDR.LAST_NAME']}" if pd.notna(row['HISTHDR.LAST_NAME']) else 'N/A'
            date = row['HISTHDR.INVOICE_DATE'].strftime('%m/%d/%y') if pd.notna(row['HISTHDR.INVOICE_DATE']) else 'N/A'
            description = row['DESCRIPTION'] if pd.notna(row['DESCRIPTION']) else 'N/A'
            price = f"${row['SELL_PRICE']:.2f}" if pd.notna(row['SELL_PRICE']) else '$0.00'
            labor = f"${row['SELL_LABOR']:.2f}" if pd.notna(row['SELL_LABOR']) else '$0.00'
            
            data.append({
                'customer': customer,
                'date': date,
                'description': description,
                'price': price,
                'labor': labor
            })
    else:
        data = []
    
    item_numbers = data_loader.get_unique_item_numbers()
    
    return render_template('item.html', data=data, item_numbers=item_numbers, selected_item=item_number)

if __name__ == '__main__':
    # This runs the app on port 8000
    app.run(port=8000) 
