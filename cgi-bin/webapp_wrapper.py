#!/usr/bin/env python3
import os
import sys
import cgitb
import traceback
from datetime import datetime

# Enable CGI error reporting
cgitb.enable()

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set environment variables for Bluehost
os.environ.setdefault('FLASK_ENV', 'production')
os.environ.setdefault('FLASK_DEBUG', '0')

def create_error_app(error_message):
    """Create a minimal Flask app for error handling."""
    from flask import Flask, jsonify
    
    app = Flask(__name__)
    
    @app.route('/health')
    def health():
        return jsonify({
            'status': 'unhealthy',
            'error': error_message,
            'timestamp': datetime.utcnow().isoformat()
        }), 500
    
    @app.route('/')
    def index():
        return jsonify({
            'error': 'Application failed to start',
            'message': error_message,
            'timestamp': datetime.utcnow().isoformat()
        }), 500
    
    return app

try:
    # Try to import and create the main app
    from webapp import app
    print("✅ Successfully imported webapp", file=sys.stderr)
    
except ImportError as e:
    print(f"❌ Import error: {e}", file=sys.stderr)
    print(f"Traceback: {traceback.format_exc()}", file=sys.stderr)
    app = create_error_app(f"Import error: {str(e)}")
    
except Exception as e:
    print(f"❌ Unexpected error: {e}", file=sys.stderr)
    print(f"Traceback: {traceback.format_exc()}", file=sys.stderr)
    app = create_error_app(f"Unexpected error: {str(e)}")

# Create WSGI application
application = app

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False) 