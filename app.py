import os
from flask import Flask, render_template, request
from data_loader import InvoiceDataLoader

app = Flask(__name__)
_loader = None


def get_loader():
    global _loader
    if _loader is None:
        csv_file = os.path.join(os.path.dirname(__file__), 'data', 'invoices.csv')
        _loader = InvoiceDataLoader(csv_path=csv_file)
    return _loader


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/chronological')
def chronological():
    loader = get_loader()
    invoice_number = request.args.get('invoice_number', '').strip()
    customer = request.args.get('customer', '').strip()
    df = loader.get_chronological_view()
    df = df.head(500)

    if invoice_number:
        df = df[df['INVOICE_NUMBER'].astype(str) == invoice_number]
    if customer:
        df = df[df['HISTHDR.LAST_NAME'] == customer]

    invoices = []
    for _, row in df.iterrows():
        invoice_date = row['HISTHDR.INVOICE_DATE']
        if hasattr(invoice_date, 'strftime'):
            invoice_date = invoice_date.strftime('%Y-%m-%d')

        invoices.append({
            'invoice_number': row.get('INVOICE_NUMBER', ''),
            'invoice_date': invoice_date,
            'part_number': row.get('ITEM_NUMBER', ''),
            'description': row.get('DESCRIPTION', ''),
            'quantity': row.get('QUANTITY', ''),
            'price': row.get('SELL_PRICE', ''),
            'labor': row.get('SELL_LABOR', ''),
        })

    return render_template(
        'chronological.html',
        invoices=invoices,
        invoice_options=loader.get_unique_invoice_numbers(),
        customers=loader.get_unique_customers(),
    )


@app.route('/grouped')
def grouped():
    loader = get_loader()
    selected_customer = request.args.get('customer', '').strip()
    
    # Filter the dataframe based on selected customer
    if selected_customer:
        filtered_df = loader.df[loader.df['HISTHDR.LAST_NAME'] == selected_customer]
    else:
        filtered_df = loader.df
    
    # Get grouped views with the filtered dataframe
    parts_df = loader.get_parts_grouped_view(filtered_df)
    labor_df = loader.get_labor_grouped_view(filtered_df)

    parts = [
        {
            'description': row['Description'],
            'purchase_count': row['Purchase Count'],
            'total_quantity': row['Total Quantity'],
            'max_price': row['Max Price'],
            'recent_price': row['Most Recent Price'],
        }
        for _, row in parts_df.iterrows()
    ]

    labor = [
        {
            'description': row['Description'],
            'labor_count': row['Labor Count'],
            'total_quantity': row['Total Quantity'],
            'max_labor': row['Max Labor'],
            'recent_labor': row['Most Recent Labor'],
        }
        for _, row in labor_df.iterrows()
    ]

    return render_template(
        'grouped.html',
        customers=loader.get_unique_customers(),
        selected_customer=selected_customer,
        parts=parts,
        labor=labor,
    )


@app.route('/item')
def item_lookup():
    loader = get_loader()
    selected_item = request.args.get('item_number', '').strip()
    item_numbers = loader.get_unique_item_numbers()
    data = []

    if selected_item:
        df = loader.df[loader.df['ITEM_NUMBER'].astype(str) == selected_item].copy()
        df = df.sort_values('HISTHDR.INVOICE_DATE', ascending=False)
        for _, row in df.iterrows():
            invoice_date = row['HISTHDR.INVOICE_DATE']
            if hasattr(invoice_date, 'strftime'):
                invoice_date = invoice_date.strftime('%Y-%m-%d')

            data.append({
                'customer': row.get('HISTHDR.LAST_NAME', ''),
                'date': invoice_date,
                'description': row.get('DESCRIPTION', ''),
                'price': row.get('SELL_PRICE', ''),
                'labor': row.get('SELL_LABOR', ''),
            })

    return render_template(
        'item.html',
        item_numbers=item_numbers,
        selected_item=selected_item,
        data=data,
    )

