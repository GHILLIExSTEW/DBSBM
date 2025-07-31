#!/usr/bin/env python3
import os
import sys
import cgi
import cgitb
from flask import Flask, jsonify, render_template, request, redirect, url_for
from datetime import datetime

# Enable CGI error reporting
cgitb.enable()

# Create Flask app
app = Flask(__name__)

# Configure for production
app.config['ENV'] = 'production'
app.config['DEBUG'] = False
app.config['SECRET_KEY'] = 'your-secret-key-change-this'

@app.route('/')
def index():
    """Main landing page."""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Bet Tracking AI</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body>
        <div class="container mt-5">
            <h1>Bet Tracking AI</h1>
            <p>Welcome to the Bet Tracking AI system.</p>
            <a href="/dashboard" class="btn btn-primary">Go to Dashboard</a>
        </div>
    </body>
    </html>
    """

@app.route('/dashboard')
def dashboard():
    """Dashboard page."""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Dashboard - Bet Tracking AI</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    </head>
    <body>
        <div class="container-fluid">
            <div class="row">
                <div class="col-12">
                    <div class="text-center py-5" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border-radius: 10px; margin: 2rem 0;">
                        <h1 class="display-4">
                            <i class="fas fa-chart-line"></i>
                            Bet Tracking AI Dashboard
                        </h1>
                        <p class="lead">Track your betting performance and server statistics</p>
                    </div>
                </div>
            </div>
            
            <div class="row">
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-header">
                            <h3><i class="fas fa-server"></i> Active Servers</h3>
                        </div>
                        <div class="card-body">
                            <p class="text-muted">No active servers found. Add your Discord server to start tracking bets!</p>
                        </div>
                    </div>
                </div>
                
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-header">
                            <h3><i class="fas fa-gamepad"></i> Live Games</h3>
                        </div>
                        <div class="card-body">
                            <p class="text-muted">No live games available. Check back later for live scores and updates!</p>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="row mt-4">
                <div class="col-12">
                    <div class="card">
                        <div class="card-header">
                            <h3><i class="fas fa-bolt"></i> Quick Actions</h3>
                        </div>
                        <div class="card-body">
                            <div class="row">
                                <div class="col-md-3 mb-3">
                                    <a href="/" class="btn btn-outline-primary btn-lg w-100">
                                        <i class="fas fa-home"></i><br>Home Page
                                    </a>
                                </div>
                                <div class="col-md-3 mb-3">
                                    <a href="/health" class="btn btn-outline-info btn-lg w-100">
                                        <i class="fas fa-heartbeat"></i><br>System Health
                                    </a>
                                </div>
                                <div class="col-md-3 mb-3">
                                    <a href="/api/status" class="btn btn-outline-warning btn-lg w-100">
                                        <i class="fas fa-cog"></i><br>API Status
                                    </a>
                                </div>
                                <div class="col-md-3 mb-3">
                                    <a href="/server-list" class="btn btn-outline-success btn-lg w-100">
                                        <i class="fas fa-list"></i><br>Server List
                                    </a>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </body>
    </html>
    """

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
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Server List - Bet Tracking AI</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body>
        <div class="container mt-5">
            <h1>Server List</h1>
            <p>No servers found.</p>
            <a href="/dashboard" class="btn btn-primary">Back to Dashboard</a>
        </div>
    </body>
    </html>
    """

if __name__ == "__main__":
    # Get port from environment or use default
    port = int(os.getenv('WEBAPP_PORT', 25594))
    
    print("Starting Flask webapp on port", port)
    print("Environment:", app.config['ENV'])
    print("Debug mode:", app.config['DEBUG'])
    
    try:
        # Listen on all interfaces, on specified port
        app.run(
            host="0.0.0.0",
            port=port,
            debug=app.config['DEBUG'],
            use_reloader=False  # Disable reloader in production
        )
    except Exception as e:
        print("Failed to start Flask webapp:", e)
        sys.exit(1) 