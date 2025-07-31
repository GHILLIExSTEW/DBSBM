#!/usr/bin/env python3
import os
import sys
import cgitb
from flask import Flask, jsonify, render_template
from datetime import datetime

# Enable CGI error reporting
cgitb.enable()

# Create Flask app
app = Flask(__name__, static_folder="bot/static", template_folder="bot/templates")

# Configure for production
app.config['ENV'] = 'production'
app.config['DEBUG'] = False
app.config['SECRET_KEY'] = 'your-secret-key-change-this'

@app.route('/')
def index():
    """Main landing page."""
    return render_template('landing.html', leagues=[], active_guilds=[])

@app.route('/health')
def health():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'service': 'betting-bot-webapp'
    })

@app.route('/api/status')
def api_status():
    """API status endpoint."""
    return jsonify({
        'status': 'operational',
        'version': '1.0.0',
        'environment': app.config['ENV'],
        'debug': app.config['DEBUG']
    })

@app.route('/server-list')
def server_list():
    """Server list page."""
    return render_template('server_list.html', guilds=[])

@app.route('/dashboard')
def dashboard():
    """Dashboard page."""
    return render_template('landing.html', leagues=[], active_guilds=[])

# Create WSGI application for Bluehost
application = app

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=False) 