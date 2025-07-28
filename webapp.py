import os
import logging
import logging.handlers
import sys
from flask import Flask, jsonify
from werkzeug.middleware.proxy_fix import ProxyFix
from datetime import datetime


class DailyRotatingFileHandler(logging.handlers.TimedRotatingFileHandler):
    """Handler that creates a new log file each day."""

    def __init__(self, filename: str, when: str = "midnight", interval: int = 1, backup_count: int = 30):
        # Ensure the directory exists
        log_dir = os.path.dirname(filename)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)

        super().__init__(filename, when=when, interval=interval, backupCount=backup_count)
        self.suffix = "%Y-%m-%d"
        self.namer = self._namer

    def _namer(self, default_name: str) -> str:
        """Custom namer to use date format in filename."""
        base_name = os.path.splitext(default_name)[0]
        extension = os.path.splitext(default_name)[1]
        return f"{base_name}{extension}"


# Configure logging to use daily files
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        # Daily rotating file handler
        DailyRotatingFileHandler(
            'db_logs/webapp_daily.log',
            when="midnight",
            interval=1,
            backup_count=30
        ),
        # Console handler for critical errors only
        logging.StreamHandler(sys.stdout) if os.getenv(
            'FLASK_DEBUG', '0').lower() == 'true' else None
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


if __name__ == "__main__":
    # Get port from environment or use default
    port = int(os.getenv('WEBAPP_PORT', 25594))

    # Ensure db_logs directory exists
    os.makedirs('db_logs', exist_ok=True)

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
