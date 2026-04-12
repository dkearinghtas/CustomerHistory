from flask import Flask
import os

app = Flask(__name__)

@app.route('/')
def index():
    """Home page with navigation"""
    return "<h1>InvoiceViewer App</h1><p>App is working! No data loading yet.</p>"

@app.route('/test')
def test_data():
    """Test data loading"""
    try:
        # Test pandas import first
        import pandas as pd
        return f"<h1>Pandas imported successfully</h1><p>Version: {pd.__version__}</p><a href='/test2'>Test data_loader import</a>"
    except Exception as e:
        import traceback
        return f"<h1>Error importing pandas</h1><p>{e}</p><pre>{traceback.format_exc()}</pre>"

@app.route('/test2')
def test_data2():
    """Test data_loader import"""
    try:
        from data_loader import InvoiceDataLoader
        return f"<h1>data_loader imported successfully</h1><a href='/test3'>Test CSV loading</a>"
    except Exception as e:
        import traceback
        return f"<h1>Error importing data_loader</h1><p>{e}</p><pre>{traceback.format_exc()}</pre>"

@app.route('/test3')
def test_data3():
    """Test CSV loading"""
    try:
        import os
        from data_loader import InvoiceDataLoader
        csv_file = os.path.join(os.path.dirname(__file__), 'data', 'invoices.csv')
        return f"<h1>CSV path: {csv_file}</h1><p>Exists: {os.path.exists(csv_file)}</p><p>Size: {os.path.getsize(csv_file) if os.path.exists(csv_file) else 'N/A'}</p><a href='/test4'>Test full loading</a>"
    except Exception as e:
        import traceback
        return f"<h1>Error checking CSV</h1><p>{e}</p><pre>{traceback.format_exc()}</pre>"

@app.route('/test4')
def test_data4():
    """Test full data loading"""
    try:
        from data_loader import InvoiceDataLoader
        import os
        csv_file = os.path.join(os.path.dirname(__file__), 'data', 'invoices.csv')
        loader = InvoiceDataLoader(csv_path=csv_file)
        return f"<h1>Data Loaded!</h1><p>Shape: {loader.df.shape}</p><p>Columns: {list(loader.df.columns)}</p>"
    except Exception as e:
        import traceback
        return f"<h1>Error loading data</h1><p>{e}</p><pre>{traceback.format_exc()}</pre>" 
