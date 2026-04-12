"""WSGI entry point for Azure App Service"""
import sys
import os
from pathlib import Path

# Ensure we can import from the current directory
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import and export the Flask app for Gunicorn
from app import app

if __name__ == "__main__":
    # This is only used if someone runs this directly, not for Gunicorn
    app.run(host="0.0.0.0", port=8000, debug=False)

