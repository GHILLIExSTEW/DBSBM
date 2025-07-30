import os
import logging
import logging.handlers
import sys
from flask import Flask, jsonify, render_template, request, redirect, url_for
from werkzeug.middleware.proxy_fix import ProxyFix
from datetime import datetime
import mysql.connector
from mysql.connector import Error
import json


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
app = Flask(__name__, static_folder="bot/static", template_folder="bot/templates")

# Configure for production
app.config['ENV'] = os.getenv('FLASK_ENV', 'production')
app.config['DEBUG'] = os.getenv('FLASK_DEBUG', '0').lower() == 'true'
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-change-this')

# Handle proxy headers (useful for hosting platforms)
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

def get_db_connection():
    """Create database connection."""
    try:
        connection = mysql.connector.connect(
            host=os.getenv('MYSQL_HOST', 'localhost'),
            user=os.getenv('MYSQL_USER', 'dbsbm'),
            password=os.getenv('MYSQL_PASSWORD', ''),
            database=os.getenv('MYSQL_DB', 'dbsbm'),
            port=int(os.getenv('MYSQL_PORT', 3306))
        )
        return connection
    except Error as e:
        logger.error(f"Error connecting to MySQL: {e}")
        return None

def get_active_guilds():
    """Get active guilds with their stats."""
    connection = get_db_connection()
    if not connection:
        return []
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        # Get guilds with their monthly and yearly units
        query = """
        SELECT 
            g.guild_id,
            g.guild_name,
            COALESCE(SUM(CASE 
                WHEN b.created_at >= DATE_SUB(NOW(), INTERVAL 1 MONTH) 
                THEN b.units 
                ELSE 0 
            END), 0) as monthly_units,
            COALESCE(SUM(CASE 
                WHEN b.created_at >= DATE_SUB(NOW(), INTERVAL 1 YEAR) 
                THEN b.units 
                ELSE 0 
            END), 0) as yearly_units
        FROM guilds g
        LEFT JOIN bets b ON g.guild_id = b.guild_id
        WHERE g.is_active = 1
        GROUP BY g.guild_id, g.guild_name
        ORDER BY yearly_units DESC
        LIMIT 10
        """
        
        cursor.execute(query)
        guilds = cursor.fetchall()
        cursor.close()
        return guilds
        
    except Error as e:
        logger.error(f"Error fetching active guilds: {e}")
        return []
    finally:
        if connection.is_connected():
            connection.close()

def get_live_games():
    """Get live games from database."""
    connection = get_db_connection()
    if not connection:
        return []
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        # Get live games with team info and odds
        query = """
        SELECT 
            g.game_id,
            g.league_id,
            g.home_team_id,
            g.away_team_id,
            g.game_time,
            g.status,
            g.home_score,
            g.away_score,
            ht.team_name as home_team_name,
            ht.logo_url as home_logo,
            at.team_name as away_team_name,
            at.logo_url as away_logo,
            l.league_name,
            l.logo_url as league_logo
        FROM games g
        JOIN teams ht ON g.home_team_id = ht.team_id
        JOIN teams at ON g.away_team_id = at.team_id
        JOIN leagues l ON g.league_id = l.league_id
        WHERE g.status IN ('live', 'halftime', 'scheduled')
        AND g.game_time >= DATE_SUB(NOW(), INTERVAL 1 DAY)
        ORDER BY g.game_time ASC
        """
        
        cursor.execute(query)
        games = cursor.fetchall()
        
        # Group games by league
        leagues = {}
        for game in games:
            league_id = game['league_id']
            if league_id not in leagues:
                leagues[league_id] = {
                    'id': league_id,
                    'name': game['league_name'],
                    'logo': game['league_logo'],
                    'games': []
                }
            
            # Format game data
            game_data = {
                'game_id': game['game_id'],
                'home_team_name': game['home_team_name'],
                'home_logo': game['home_logo'],
                'away_team_name': game['away_team_name'],
                'away_logo': game['away_logo'],
                'start_time': game['game_time'],
                'status': game['status'],
                'score': {
                    'home': game['home_score'] or 0,
                    'away': game['away_score'] or 0
                } if game['home_score'] is not None else None
            }
            
            leagues[league_id]['games'].append(game_data)
        
        cursor.close()
        return list(leagues.values())
        
    except Error as e:
        logger.error(f"Error fetching live games: {e}")
        return []
    finally:
        if connection.is_connected():
            connection.close()

@app.route('/')
def index():
    """Main landing page."""
    try:
        leagues = get_live_games()
        active_guilds = get_active_guilds()
        
        return render_template('landing.html', 
                            leagues=leagues, 
                            active_guilds=active_guilds)
    except Exception as e:
        logger.error(f"Error rendering landing page: {e}")
        return render_template('landing.html', leagues=[], active_guilds=[])

@app.route('/server-list')
def server_list():
    """Server list page."""
    try:
        active_guilds = get_active_guilds()
        return render_template('server_list.html', guilds=active_guilds)
    except Exception as e:
        logger.error(f"Error rendering server list: {e}")
        return render_template('server_list.html', guilds=[])

@app.route('/guild/<int:guild_id>')
def guild_home(guild_id):
    """Guild home page."""
    try:
        # Get guild info
        connection = get_db_connection()
        if connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT * FROM guilds WHERE guild_id = %s", (guild_id,))
            guild = cursor.fetchone()
            cursor.close()
            connection.close()
            
            if guild:
                return render_template('guild_home.html', guild=guild)
        
        return redirect(url_for('index'))
    except Exception as e:
        logger.error(f"Error rendering guild home: {e}")
        return redirect(url_for('index'))

@app.route('/guild/<int:guild_id>/live-scores')
def live_scores(guild_id):
    """Live scores page for a specific guild."""
    try:
        leagues = get_live_games()
        return render_template('live_scores.html', 
                            guild_id=guild_id, 
                            leagues=leagues)
    except Exception as e:
        logger.error(f"Error rendering live scores: {e}")
        return render_template('live_scores.html', 
                            guild_id=guild_id, 
                            leagues=[])

@app.route('/guild/<int:guild_id>/player-stats')
def player_stats(guild_id):
    """Player stats page."""
    try:
        return render_template('player_stats.html', guild_id=guild_id)
    except Exception as e:
        logger.error(f"Error rendering player stats: {e}")
        return render_template('player_stats.html', guild_id=guild_id)

@app.route('/guild/<int:guild_id>/odds-buster')
def odds_buster(guild_id):
    """Odds buster page."""
    try:
        return render_template('odds_buster.html', guild_id=guild_id)
    except Exception as e:
        logger.error(f"Error rendering odds buster: {e}")
        return render_template('odds_buster.html', guild_id=guild_id)

@app.route('/guild/<int:guild_id>/playmaker-stats')
def playmaker_stats(guild_id):
    """Playmaker stats page."""
    try:
        return render_template('playmaker_stats.html', guild_id=guild_id)
    except Exception as e:
        logger.error(f"Error rendering playmaker stats: {e}")
        return render_template('playmaker_stats.html', guild_id=guild_id)

@app.route('/guild/<int:guild_id>/settings')
def guild_settings(guild_id):
    """Guild settings page."""
    try:
        # Get guild info
        connection = get_db_connection()
        if connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT * FROM guilds WHERE guild_id = %s", (guild_id,))
            guild = cursor.fetchone()
            cursor.close()
            connection.close()
            
            if guild:
                return render_template('guild_settings.html', guild=guild)
        
        return redirect(url_for('index'))
    except Exception as e:
        logger.error(f"Error rendering guild settings: {e}")
        return redirect(url_for('index'))

@app.route('/guild/<int:guild_id>/subscriptions')
def subscriptions(guild_id):
    """Subscriptions page."""
    try:
        return render_template('subscriptions.html', guild_id=guild_id)
    except Exception as e:
        logger.error(f"Error rendering subscriptions: {e}")
        return render_template('subscriptions.html', guild_id=guild_id)

@app.route('/league/<int:league_id>/scores')
def live_scores_league(league_id):
    """Live scores for a specific league."""
    try:
        # Get league info and games
        connection = get_db_connection()
        if connection:
            cursor = connection.cursor(dictionary=True)
            
            # Get league info
            cursor.execute("SELECT * FROM leagues WHERE league_id = %s", (league_id,))
            league = cursor.fetchone()
            
            if league:
                # Get games for this league
                cursor.execute("""
                    SELECT 
                        g.*,
                        ht.team_name as home_team_name,
                        ht.logo_url as home_logo,
                        at.team_name as away_team_name,
                        at.logo_url as away_logo
                    FROM games g
                    JOIN teams ht ON g.home_team_id = ht.team_id
                    JOIN teams at ON g.away_team_id = at.team_id
                    WHERE g.league_id = %s
                    AND g.game_time >= DATE_SUB(NOW(), INTERVAL 7 DAY)
                    ORDER BY g.game_time DESC
                """, (league_id,))
                games = cursor.fetchall()
                
                cursor.close()
                connection.close()
                
                return render_template('live_scores_league.html', 
                                    league=league, 
                                    games=games)
        
        return redirect(url_for('index'))
    except Exception as e:
        logger.error(f"Error rendering league scores: {e}")
        return redirect(url_for('index'))

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
