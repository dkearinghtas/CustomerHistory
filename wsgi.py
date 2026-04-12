"""WSGI entry point for Azure App Service"""
import sys
import os

# Ensure we can import from the current directory
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import and export the Flask app for Gunicorn
from app import app

