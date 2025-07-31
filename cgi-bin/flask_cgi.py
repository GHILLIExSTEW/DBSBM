#!/usr/bin/env python3
import os
import sys
import cgitb
cgitb.enable()

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set environment variables for Bluehost
os.environ.setdefault('FLASK_ENV', 'production')
os.environ.setdefault('FLASK_DEBUG', '0')

try:
    # Import the Flask app (use simple version to avoid logging issues)
    from webapp_simple import app
    
    # Get the request path
    path_info = os.environ.get('PATH_INFO', '/')
    if not path_info or path_info == '/':
        path_info = '/'
    else:
        # Remove the wrapper script name from the path
        path_info = path_info.replace('/flask_cgi.py', '')
        if not path_info:
            path_info = '/'
    
    # Create a test client
    with app.test_client() as client:
        # Make the request
        response = client.get(path_info)
        
        # Get the response content
        content = response.get_data(as_text=True)
        content_type = response.headers.get('Content-Type', 'text/html')
        
        # Send the response
        print(f"Content-Type: {content_type}")
        print()
        print(content)
        
except Exception as e:
    # Fallback error page
    print("Content-Type: text/html")
    print()
    print(f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Flask App Error</title>
    </head>
    <body>
        <h1>❌ Flask App Error</h1>
        <p>Error: {str(e)}</p>
        <p>Path: {os.environ.get('PATH_INFO', '/')}</p>
    </body>
    </html>
    """) 