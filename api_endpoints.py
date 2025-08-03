from flask import Flask, jsonify, request
from flask_cors import CORS
import psycopg2
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Allow WordPress to access the API

def get_db_connection():
    """Create database connection."""
    try:
        connection = psycopg2.connect(
            host=os.getenv('PG_HOST', 'localhost'),
            user=os.getenv('PG_USER', 'postgres'),
            password=os.getenv('PG_PASSWORD', ''),
            dbname=os.getenv('PG_DATABASE', 'dbsbm'),
            port=int(os.getenv('PG_PORT', 5432))
        )
        return connection
    except Exception as e:
        logger.error(f"Error connecting to PostgreSQL: {e}")
        return None

@app.route('/api/health')
def health_check():
    """Health check endpoint."""
    return jsonify({"status": "healthy", "service": "betbot-api"})

@app.route('/api/guilds')
def get_guilds():
    """Get active guilds for WordPress."""
    connection = get_db_connection()
    if not connection:
        return jsonify({"error": "Database connection failed"}), 500
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        # Get active guilds with stats
        query = """
        SELECT 
            g.guild_id,
            g.guild_name,
            g.monthly_units,
            g.yearly_units,
            g.created_at,
            g.updated_at
        FROM guilds g
        WHERE g.is_active = 1
        ORDER BY g.updated_at DESC
        """
        
        cursor.execute(query)
        guilds = cursor.fetchall()
        
        # Convert datetime objects to strings for JSON
        for guild in guilds:
            if guild.get('created_at'):
                guild['created_at'] = guild['created_at'].isoformat()
            if guild.get('updated_at'):
                guild['updated_at'] = guild['updated_at'].isoformat()
        
        return jsonify({
            "success": True,
            "guilds": guilds,
            "count": len(guilds)
        })
        
    except Error as e:
        logger.error(f"Database error: {e}")
        return jsonify({"error": "Database error"}), 500
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

@app.route('/api/live-scores')
def get_live_scores():
    """Get live scores for WordPress."""
    connection = get_db_connection()
    if not connection:
        return jsonify({"error": "Database connection failed"}), 500
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        # Get live games grouped by league
        query = """
        SELECT 
            g.game_id,
            g.home_team,
            g.away_team,
            g.home_score,
            g.away_score,
            g.game_status,
            g.game_time,
            g.league_id,
            l.league_name,
            l.league_logo
        FROM games g
        LEFT JOIN leagues l ON g.league_id = l.league_id
        WHERE g.game_status IN ('live', 'halftime', 'scheduled')
        ORDER BY l.league_name, g.game_time
        """
        
        cursor.execute(query)
        games = cursor.fetchall()
        
        # Group games by league
        leagues = {}
        for game in games:
            league_id = game['league_id']
            if league_id not in leagues:
                leagues[league_id] = {
                    'league_id': league_id,
                    'league_name': game['league_name'],
                    'league_logo': game['league_logo'],
                    'games': []
                }
            
            # Convert datetime to string
            if game.get('game_time'):
                game['game_time'] = game['game_time'].isoformat()
            
            leagues[league_id]['games'].append(game)
        
        return jsonify({
            "success": True,
            "leagues": list(leagues.values()),
            "total_games": len(games)
        })
        
    except Error as e:
        logger.error(f"Database error: {e}")
        return jsonify({"error": "Database error"}), 500
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

@app.route('/api/guild/<int:guild_id>')
def get_guild_details(guild_id):
    """Get specific guild details."""
    connection = get_db_connection()
    if not connection:
        return jsonify({"error": "Database connection failed"}), 500
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        # Get guild details
        query = """
        SELECT 
            guild_id,
            guild_name,
            monthly_units,
            yearly_units,
            created_at,
            updated_at
        FROM guilds
        WHERE guild_id = %s AND is_active = 1
        """
        
        cursor.execute(query, (guild_id,))
        guild = cursor.fetchone()
        
        if not guild:
            return jsonify({"error": "Guild not found"}), 404
        
        # Convert datetime objects
        if guild.get('created_at'):
            guild['created_at'] = guild['created_at'].isoformat()
        if guild.get('updated_at'):
            guild['updated_at'] = guild['updated_at'].isoformat()
        
        return jsonify({
            "success": True,
            "guild": guild
        })
        
    except Error as e:
        logger.error(f"Database error: {e}")
        return jsonify({"error": "Database error"}), 500
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

if __name__ == '__main__':
    port = int(os.getenv('API_PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', '0').lower() == 'true'
    
    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug
    )
