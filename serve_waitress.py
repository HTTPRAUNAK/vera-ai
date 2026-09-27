"""
serve_waitress.py - Pure-Python WSGI server using Waitress.
Resolves Windows socket permission errors and handles cloud PORT injection.
"""
import os
import sys
from waitress import serve
from bot import app

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    host = "0.0.0.0" if os.environ.get("PORT") else "127.0.0.1"
    print(f"Starting vera-bot server on http://{host}:{port}")
    serve(app, host=host, port=port)
