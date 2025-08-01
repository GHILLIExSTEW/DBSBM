#!/usr/bin/env python3
"""
Web application entry point for the DBSBM bot.
This file redirects to the actual webapp implementation in cgi-bin/.
"""

import os
import sys

# Add the cgi-bin directory to the path
cgi_bin_path = os.path.join(os.path.dirname(__file__), 'cgi-bin')
sys.path.insert(0, cgi_bin_path)

# Import and run the webapp
from webapp_fixed import app

if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=int(os.getenv('WEBAPP_PORT', 25594)),
        debug=False
    ) 