"""WSGI entry point for Azure App Service"""
import sys
import os

# Ensure we can import from the current directory
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from app import app
    
    if __name__ == "__main__":
        # For local testing
        app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)
except Exception as e:
    print(f"Failed to import app: {e}")
    import traceback
    traceback.print_exc()
    raise
