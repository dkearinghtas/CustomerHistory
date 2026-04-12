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
        # Try importing data_loader here
        from data_loader import InvoiceDataLoader
        csv_file = os.path.join(os.path.dirname(__file__), 'data', 'invoices.csv')
        loader = InvoiceDataLoader(csv_path=csv_file)
        return f"<h1>Data Loaded!</h1><p>Shape: {loader.df.shape}</p><p>Columns: {list(loader.df.columns)}</p><a href='/'>Back</a>"
    except Exception as e:
        import traceback
        return f"<h1>Error loading data</h1><p>{e}</p><pre>{traceback.format_exc()}</pre><a href='/'>Back</a>" 
