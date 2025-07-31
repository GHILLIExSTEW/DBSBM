#!/usr/bin/env python3
import os
import sys
import cgitb
cgitb.enable()

print("Content-Type: text/html")
print()
print("""
<!DOCTYPE html>
<html>
<head>
    <title>CGI Test</title>
</head>
<body>
    <h1>✅ CGI is Working!</h1>
    <p>If you can see this page, CGI is working correctly.</p>
    <p>Python version: """ + sys.version + """</p>
    <p>Current directory: """ + os.getcwd() + """</p>
    <p><a href="/cgi-bin/flask_cgi.py">Test Flask CGI</a></p>
</body>
</html>
""") 