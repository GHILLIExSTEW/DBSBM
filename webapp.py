import os
import logging
import sys
from flask import Flask, jsonify
from werkzeug.middleware.proxy_fix import ProxyFix

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/webapp.log', encoding='utf-8') if os.path.exists('logs') else logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__, static_folder="bot/static")

# Configure for production
app.config['ENV'] = os.getenv('FLASK_ENV', 'production')
app.config['DEBUG'] = os.getenv('FLASK_DEBUG', '0').lower() == 'true'

# Handle proxy headers (useful for hosting platforms)
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

@app.route('/')
def index():
    """Main page for the webapp."""
    return jsonify({
        'status': 'online',
        'service': 'betting-bot-webapp',
        'version': '1.0.0'
    })

@app.route('/health')
def health_check():
    """Health check endpoint for monitoring."""
    return jsonify({
        'status': 'healthy',
        'service': 'betting-bot-webapp'
    })

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    logger.error(f"Internal server error: {error}")
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == "__main__":
    # Get port from environment or use default
    port = int(os.getenv('WEBAPP_PORT', 25594))

    # Ensure logs directory exists
    os.makedirs('logs', exist_ok=True)

    logger.info(f"Starting Flask webapp on port {port}")
    logger.info(f"Environment: {app.config['ENV']}")
    logger.info(f"Debug mode: {app.config['DEBUG']}")

    try:
        # Listen on all interfaces, on specified port
        app.run(
            host="0.0.0.0",
            port=port,
            debug=app.config['DEBUG'],
            use_reloader=False  # Disable reloader in production
        )
    except Exception as e:
        logger.error(f"Failed to start Flask webapp: {e}")
        sys.exit(1)
