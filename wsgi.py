"""WSGI entry point for Azure App Service"""
import sys
import os

print("wsgi.py starting...")
sys.stdout.flush()

# Ensure we can import from the current directory
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("Path set:", sys.path[0])
sys.stdout.flush()

try:
    print("Attempting to import app...")
    sys.stdout.flush()
    from app import app
    print("Success! app imported")
    sys.stdout.flush()
    
    if __name__ == "__main__":
        print("Starting Flask app...")
        sys.stdout.flush()
        app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)
except Exception as e:
    print(f"ERROR: Failed to import app: {e}")
    import traceback
    traceback.print_exc()
    sys.stdout.flush()
    raise
