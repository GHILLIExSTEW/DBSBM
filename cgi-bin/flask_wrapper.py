#!/usr/bin/env python3
import os
import sys
import cgitb
import urllib.request
import urllib.parse
cgitb.enable()

# Get the request path
path_info = os.environ.get('PATH_INFO', '/')
if not path_info or path_info == '/':
    path_info = '/'
else:
    # Remove the wrapper script name from the path
    path_info = path_info.replace('/flask_wrapper.py', '')
    if not path_info:
        path_info = '/'

query_string = os.environ.get('QUERY_STRING', '')

# Construct the URL to the running Flask app - using the correct port from logs
flask_url = f"http://127.0.0.1:25594{path_info}"
if query_string:
    flask_url += f"?{query_string}"

# Debug information
print(f"Content-Type: text/plain")
print()
print(f"Debug Info:")
print(f"PATH_INFO: {os.environ.get('PATH_INFO', 'None')}")
print(f"Processed path: {path_info}")
print(f"Flask URL: {flask_url}")
print(f"Query string: {query_string}")

try:
    # Forward the request to the Flask app
    response = urllib.request.urlopen(flask_url)
    
    # Get the response
    content = response.read()
    content_type = response.headers.get('Content-Type', 'text/html')
    
    # Send the response
    print(f"Content-Type: {content_type}")
    print()
    print(content.decode('utf-8'))
    
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
        <p>Make sure the Flask app is running on port 25594</p>
        <p>Path: {path_info}</p>
    </body>
    </html>
    """) 