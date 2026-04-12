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

# Lazy-load data loader to speed up application startup
_data_loader = None

def get_data_loader():
    """Lazy-load data loader on first use"""
    global _data_loader
    if _data_loader is None:
        print("Loading data loader...")
        if use_live:
            _data_loader = InvoiceDataLoader(use_live=True, connection_string=connection_string, table_name=table_name)
        else:
            _data_loader = InvoiceDataLoader(csv_path=csv_file)
        print("Data loader loaded successfully!")
    return _data_loader

# Create shorthand for backward compatibility
@property
def data_loader_property():
    return get_data_loader()

# Store property for use in routes
app.data_loader_getter = get_data_loader


@app.route('/')
def index():
    """Home page with navigation"""
    return render_template('index.html') 
