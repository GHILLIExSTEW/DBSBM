#!/usr/bin/env python3
"""
WordPress + Flask Integration Setup Script
This script helps set up the recommended WordPress + Flask API approach.
"""

import os
import json
from pathlib import Path

def create_flask_api():
    """Create Flask API endpoints for WordPress integration."""
    
    api_code = '''from flask import Flask, jsonify, request
from flask_cors import CORS
import mysql.connector
from mysql.connector import Error
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
'''
    
    with open('api_endpoints.py', 'w') as f:
        f.write(api_code)
    
    print("Created api_endpoints.py - Flask API for WordPress integration")

def create_wordpress_templates():
    """Create WordPress page templates."""
    
    # Live Scores Page Template
    live_scores_template = '''<?php
/*
Template Name: Live Scores
*/

get_header(); ?>

<div class="live-scores-container">
    <div class="hero-section">
        <h1 class="hero-title">
            <i class="fas fa-trophy"></i>
            <?php the_title(); ?>
        </h1>
        <p class="hero-subtitle">Real-time sports scores and updates</p>
    </div>

    <div id="live-scores-widget">
        <div class="loading">
            <div class="spinner"></div>
            <p>Loading live scores...</p>
        </div>
    </div>
</div>

<style>
.live-scores-container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 20px;
}

.hero-section {
    text-align: center;
    margin-bottom: 40px;
}

.hero-title {
    font-size: 2.5rem;
    color: #333;
    margin-bottom: 10px;
}

.hero-subtitle {
    font-size: 1.2rem;
    color: #666;
}

.loading {
    text-align: center;
    padding: 40px;
}

.spinner {
    border: 4px solid #f3f3f3;
    border-top: 4px solid #3498db;
    border-radius: 50%;
    width: 40px;
    height: 40px;
    animation: spin 1s linear infinite;
    margin: 0 auto 20px;
}

@keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}

/* League Cards */
.league-card {
    background: rgba(255, 255, 255, 0.1);
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255, 255, 255, 0.2);
    border-radius: 15px;
    padding: 20px;
    margin-bottom: 20px;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
}

.league-header {
    display: flex;
    align-items: center;
    margin-bottom: 15px;
}

.league-logo {
    width: 40px;
    height: 40px;
    margin-right: 15px;
    border-radius: 50%;
}

.league-name {
    font-size: 1.5rem;
    font-weight: bold;
    color: #333;
    margin: 0;
}

.league-name a {
    color: inherit;
    text-decoration: none;
}

.league-name a:hover {
    color: #3498db;
}

.games-container {
    display: grid;
    gap: 10px;
}

.game-card {
    background: rgba(255, 255, 255, 0.05);
    border-radius: 10px;
    padding: 15px;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.game-teams {
    flex: 1;
}

.game-score {
    font-weight: bold;
    font-size: 1.2rem;
    color: #333;
}

.game-status {
    padding: 4px 8px;
    border-radius: 12px;
    font-size: 0.8rem;
    font-weight: bold;
}

.status-live {
    background: #e74c3c;
    color: white;
}

.status-halftime {
    background: #f39c12;
    color: white;
}

.status-scheduled {
    background: #3498db;
    color: white;
}

.empty-state {
    text-align: center;
    padding: 60px 20px;
    color: #666;
}

.empty-state i {
    font-size: 3rem;
    margin-bottom: 20px;
    color: #ccc;
}
</style>

<script>
// API configuration
const API_BASE_URL = '<?php echo get_option("betbot_api_url", "http://app.yourdomain.com"); ?>';

// Fetch and render live scores
async function loadLiveScores() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/live-scores`);
        const data = await response.json();
        
        if (data.success) {
            renderLiveScores(data.leagues);
        } else {
            showError('Failed to load live scores');
        }
    } catch (error) {
        console.error('Error loading live scores:', error);
        showError('Error loading live scores');
    }
}

function renderLiveScores(leagues) {
    const container = document.getElementById('live-scores-widget');
    
    if (!leagues || leagues.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-clock"></i>
                <h3>No Live Games</h3>
                <p>There are currently no live games. Check back later!</p>
            </div>
        `;
        return;
    }
    
    let html = '';
    
    leagues.forEach(league => {
        html += `
            <div class="league-card">
                <div class="league-header">
                    ${league.league_logo ? `<img src="${league.league_logo}" alt="${league.league_name}" class="league-logo">` : ''}
                    <h3 class="league-name">
                        <a href="/league/${league.league_id}">${league.league_name}</a>
                    </h3>
                </div>
                <div class="games-container">
        `;
        
        if (league.games && league.games.length > 0) {
            league.games.forEach(game => {
                const statusClass = `status-${game.game_status}`;
                html += `
                    <div class="game-card">
                        <div class="game-teams">
                            <div>${game.home_team} vs ${game.away_team}</div>
                            <small>${formatGameTime(game.game_time)}</small>
                        </div>
                        <div class="game-score">
                            ${game.home_score} - ${game.away_score}
                        </div>
                        <div class="game-status ${statusClass}">
                            ${game.game_status.toUpperCase()}
                        </div>
                    </div>
                `;
            });
        } else {
            html += `
                <div class="empty-state">
                    <p>No games scheduled for this league</p>
                </div>
            `;
        }
        
        html += `
                </div>
            </div>
        `;
    });
    
    container.innerHTML = html;
}

function formatGameTime(timeString) {
    if (!timeString) return '';
    const date = new Date(timeString);
    return date.toLocaleString();
}

function showError(message) {
    const container = document.getElementById('live-scores-widget');
    container.innerHTML = `
        <div class="empty-state">
            <i class="fas fa-exclamation-triangle"></i>
            <h3>Error</h3>
            <p>${message}</p>
        </div>
    `;
}

// Load data on page load
document.addEventListener('DOMContentLoaded', function() {
    loadLiveScores();
    
    // Auto-refresh every 30 seconds
    setInterval(loadLiveScores, 30000);
});
</script>

<?php get_footer(); ?>
'''
    
    # Guild Dashboard Template
    guild_dashboard_template = '''<?php
/*
Template Name: Guild Dashboard
*/

get_header(); ?>

<div class="guild-dashboard">
    <div class="hero-section">
        <h1 class="hero-title">
            <i class="fas fa-users"></i>
            Guild Dashboard
        </h1>
        <p class="hero-subtitle">Track your guild performance and statistics</p>
    </div>

    <div id="guilds-widget">
        <div class="loading">
            <div class="spinner"></div>
            <p>Loading guild data...</p>
        </div>
    </div>
</div>

<style>
.guild-dashboard {
    max-width: 1200px;
    margin: 0 auto;
    padding: 20px;
}

.hero-section {
    text-align: center;
    margin-bottom: 40px;
}

.hero-title {
    font-size: 2.5rem;
    color: #333;
    margin-bottom: 10px;
}

.hero-subtitle {
    font-size: 1.2rem;
    color: #666;
}

.loading {
    text-align: center;
    padding: 40px;
}

.spinner {
    border: 4px solid #f3f3f3;
    border-top: 4px solid #3498db;
    border-radius: 50%;
    width: 40px;
    height: 40px;
    animation: spin 1s linear infinite;
    margin: 0 auto 20px;
}

@keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}

/* Guild Cards */
.guilds-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 20px;
    margin-top: 20px;
}

.guild-card {
    background: rgba(255, 255, 255, 0.1);
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255, 255, 255, 0.2);
    border-radius: 15px;
    padding: 20px;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
    transition: transform 0.3s ease;
}

.guild-card:hover {
    transform: translateY(-5px);
}

.guild-name {
    font-size: 1.5rem;
    font-weight: bold;
    color: #333;
    margin-bottom: 15px;
}

.guild-stats {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 15px;
    margin-bottom: 15px;
}

.stat-item {
    text-align: center;
}

.stat-label {
    font-size: 0.9rem;
    color: #666;
    margin-bottom: 5px;
}

.stat-value {
    font-size: 1.5rem;
    font-weight: bold;
    color: #333;
}

.stat-positive {
    color: #27ae60;
}

.stat-negative {
    color: #e74c3c;
}

.guild-actions {
    display: flex;
    gap: 10px;
    margin-top: 15px;
}

.btn {
    padding: 8px 16px;
    border-radius: 8px;
    text-decoration: none;
    font-weight: bold;
    transition: all 0.3s ease;
}

.btn-primary {
    background: #3498db;
    color: white;
}

.btn-primary:hover {
    background: #2980b9;
}

.btn-secondary {
    background: #95a5a6;
    color: white;
}

.btn-secondary:hover {
    background: #7f8c8d;
}

.empty-state {
    text-align: center;
    padding: 60px 20px;
    color: #666;
}

.empty-state i {
    font-size: 3rem;
    margin-bottom: 20px;
    color: #ccc;
}
</style>

<script>
// API configuration
const API_BASE_URL = '<?php echo get_option("betbot_api_url", "http://app.yourdomain.com"); ?>';

// Fetch and render guilds
async function loadGuilds() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/guilds`);
        const data = await response.json();
        
        if (data.success) {
            renderGuilds(data.guilds);
        } else {
            showError('Failed to load guild data');
        }
    } catch (error) {
        console.error('Error loading guilds:', error);
        showError('Error loading guild data');
    }
}

function renderGuilds(guilds) {
    const container = document.getElementById('guilds-widget');
    
    if (!guilds || guilds.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-users"></i>
                <h3>No Active Guilds</h3>
                <p>No active guilds found. Create a guild to get started!</p>
            </div>
        `;
        return;
    }
    
    let html = '<div class="guilds-grid">';
    
    guilds.forEach(guild => {
        const monthlyClass = guild.monthly_units >= 0 ? 'stat-positive' : 'stat-negative';
        const yearlyClass = guild.yearly_units >= 0 ? 'stat-positive' : 'stat-negative';
        
        html += `
            <div class="guild-card">
                <h3 class="guild-name">${guild.guild_name}</h3>
                <div class="guild-stats">
                    <div class="stat-item">
                        <div class="stat-label">Monthly Units</div>
                        <div class="stat-value ${monthlyClass}">
                            ${guild.monthly_units >= 0 ? '+' : ''}${guild.monthly_units}
                        </div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-label">Yearly Units</div>
                        <div class="stat-value ${yearlyClass}">
                            ${guild.yearly_units >= 0 ? '+' : ''}${guild.yearly_units}
                        </div>
                    </div>
                </div>
                <div class="guild-actions">
                    <a href="/guild/${guild.guild_id}" class="btn btn-primary">View Details</a>
                    <a href="/guild/${guild.guild_id}/live-scores" class="btn btn-secondary">Live Scores</a>
                </div>
            </div>
        `;
    });
    
    html += '</div>';
    container.innerHTML = html;
}

function showError(message) {
    const container = document.getElementById('guilds-widget');
    container.innerHTML = `
        <div class="empty-state">
            <i class="fas fa-exclamation-triangle"></i>
            <h3>Error</h3>
            <p>${message}</p>
        </div>
    `;
}

// Load data on page load
document.addEventListener('DOMContentLoaded', function() {
    loadGuilds();
    
    // Auto-refresh every 60 seconds
    setInterval(loadGuilds, 60000);
});
</script>

<?php get_footer(); ?>
'''
    
    # Create templates directory
    templates_dir = Path('wordpress_templates')
    templates_dir.mkdir(exist_ok=True)
    
    # Write templates
    with open(templates_dir / 'page-live-scores.php', 'w') as f:
        f.write(live_scores_template)
    
    with open(templates_dir / 'page-guild-dashboard.php', 'w') as f:
        f.write(guild_dashboard_template)
    
    print(f"Created WordPress templates in {templates_dir}/")

def create_wordpress_plugin():
    """Create a WordPress plugin for Bet Bot Manager integration."""
    
    plugin_code = '''<?php
/*
Plugin Name: Bet Bot Manager Integration
Description: Integrates Flask web portal with WordPress
Version: 1.0
Author: Your Name
*/

// Prevent direct access
if (!defined('ABSPATH')) {
    exit;
}

// Add admin menu
function betbot_admin_menu() {
    add_options_page(
        'Bet Bot Manager Settings',
        'Bet Bot Manager',
        'manage_options',
        'betbot-settings',
        'betbot_settings_page'
    );
}
add_action('admin_menu', 'betbot_admin_menu');

// Settings page
function betbot_settings_page() {
    if (isset($_POST['submit'])) {
        update_option('betbot_api_url', sanitize_text_field($_POST['api_url']));
        echo '<div class="notice notice-success"><p>Settings saved!</p></div>';
    }
    
    $api_url = get_option('betbot_api_url', 'http://app.yourdomain.com');
    ?>
    <div class="wrap">
        <h1>Bet Bot Manager Settings</h1>
        <form method="post">
            <table class="form-table">
                <tr>
                    <th scope="row">API URL</th>
                    <td>
                        <input type="url" name="api_url" value="<?php echo esc_attr($api_url); ?>" class="regular-text" />
                        <p class="description">The URL of your Flask API (e.g., http://app.yourdomain.com)</p>
                    </td>
                </tr>
            </table>
            <?php submit_button(); ?>
        </form>
    </div>
    <?php
}

// Add shortcodes
add_shortcode('live_scores', 'betbot_live_scores_shortcode');
add_shortcode('guild_stats', 'betbot_guild_stats_shortcode');

function betbot_live_scores_shortcode($atts) {
    $api_url = get_option('betbot_api_url', 'http://app.yourdomain.com');
    
    ob_start();
    ?>
    <div id="betbot-live-scores">
        <div class="loading">Loading live scores...</div>
    </div>
    
    <script>
    // Live scores shortcode JavaScript
    fetch('<?php echo esc_url($api_url); ?>/api/live-scores')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Render live scores
                renderLiveScores(data.leagues);
            }
        })
        .catch(error => {
            console.error('Error:', error);
        });
    </script>
    <?php
    return ob_get_clean();
}

function betbot_guild_stats_shortcode($atts) {
    $api_url = get_option('betbot_api_url', 'http://app.yourdomain.com');
    
    ob_start();
    ?>
    <div id="betbot-guild-stats">
        <div class="loading">Loading guild statistics...</div>
    </div>
    
    <script>
    // Guild stats shortcode JavaScript
    fetch('<?php echo esc_url($api_url); ?>/api/guilds')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Render guild stats
                renderGuildStats(data.guilds);
            }
        })
        .catch(error => {
            console.error('Error:', error);
        });
    </script>
    <?php
    return ob_get_clean();
}

// Enqueue scripts and styles
function betbot_enqueue_scripts() {
    wp_enqueue_script('betbot-api', plugin_dir_url(__FILE__) . 'js/betbot-api.js', array(), '1.0', true);
    wp_enqueue_style('betbot-styles', plugin_dir_url(__FILE__) . 'css/betbot-styles.css', array(), '1.0');
}
add_action('wp_enqueue_scripts', 'betbot_enqueue_scripts');
'''
    
    # Create plugin directory structure
    plugin_dir = Path('betbot-wordpress-plugin')
    plugin_dir.mkdir(exist_ok=True)
    
    # Create subdirectories
    (plugin_dir / 'js').mkdir(exist_ok=True)
    (plugin_dir / 'css').mkdir(exist_ok=True)
    
    # Write main plugin file
    with open(plugin_dir / 'betbot-integration.php', 'w') as f:
        f.write(plugin_code)
    
    # Create JavaScript file
    js_code = '''// Bet Bot Manager API JavaScript
function renderLiveScores(leagues) {
    const container = document.getElementById('betbot-live-scores');
    if (!container) return;
    
    if (!leagues || leagues.length === 0) {
        container.innerHTML = '<p>No live games available.</p>';
        return;
    }
    
    let html = '';
    leagues.forEach(league => {
        html += `<div class="league-card">
            <h3>${league.league_name}</h3>
            <div class="games">`;
        
        league.games.forEach(game => {
            html += `<div class="game">
                <span>${game.home_team} vs ${game.away_team}</span>
                <span>${game.home_score} - ${game.away_score}</span>
                <span class="status ${game.game_status}">${game.game_status}</span>
            </div>`;
        });
        
        html += `</div></div>`;
    });
    
    container.innerHTML = html;
}

function renderGuildStats(guilds) {
    const container = document.getElementById('betbot-guild-stats');
    if (!container) return;
    
    if (!guilds || guilds.length === 0) {
        container.innerHTML = '<p>No guild data available.</p>';
        return;
    }
    
    let html = '<div class="guilds-grid">';
    guilds.forEach(guild => {
        html += `<div class="guild-card">
            <h3>${guild.guild_name}</h3>
            <div class="stats">
                <div>Monthly: ${guild.monthly_units}</div>
                <div>Yearly: ${guild.yearly_units}</div>
            </div>
        </div>`;
    });
    html += '</div>';
    
    container.innerHTML = html;
}
'''
    
    with open(plugin_dir / 'js' / 'betbot-api.js', 'w') as f:
        f.write(js_code)
    
    # Create CSS file
    css_code = '''/* Bet Bot Manager Styles */
.league-card {
    background: #f9f9f9;
    border: 1px solid #ddd;
    border-radius: 8px;
    padding: 15px;
    margin-bottom: 15px;
}

.game {
    display: flex;
    justify-content: space-between;
    padding: 8px 0;
    border-bottom: 1px solid #eee;
}

.status {
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 12px;
    font-weight: bold;
}

.status.live {
    background: #e74c3c;
    color: white;
}

.status.halftime {
    background: #f39c12;
    color: white;
}

.status.scheduled {
    background: #3498db;
    color: white;
}

.guilds-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 15px;
}

.guild-card {
    background: #f9f9f9;
    border: 1px solid #ddd;
    border-radius: 8px;
    padding: 15px;
}

.loading {
    text-align: center;
    padding: 20px;
    color: #666;
}
'''
    
    with open(plugin_dir / 'css' / 'betbot-styles.css', 'w') as f:
        f.write(css_code)
    
    print(f"Created WordPress plugin in {plugin_dir}/")

def create_deployment_instructions():
    """Create deployment instructions."""
    
    instructions = '''# WordPress + Flask Integration Deployment Instructions

## Step 1: Set Up WordPress on Bluehost

1. **Install WordPress:**
   - Log into Bluehost cPanel
   - Go to "Website" → "Install WordPress"
   - Follow the installation wizard
   - Choose a theme (recommend a modern, responsive theme)

2. **Install Required Plugins:**
   - Go to WordPress Admin → Plugins → Add New
   - Install and activate:
     - Advanced Custom Fields
     - Custom Post Types UI
     - WP REST API

## Step 2: Deploy Flask API

1. **Upload Flask API files:**
   - Upload `api_endpoints.py` to your Bluehost account
   - Create a subdomain (e.g., `app.yourdomain.com`) or use a subdirectory
   - Set up Python environment on Bluehost

2. **Configure environment variables:**
   ```bash
   # Create .env file
   MYSQL_HOST=localhost
   MYSQL_USER=your_username
   MYSQL_PASSWORD=your_password
   MYSQL_DB=your_database
   API_PORT=5000
   FLASK_DEBUG=0
   ```

3. **Install Python dependencies:**
   ```bash
   pip install flask flask-cors mysql-connector-python
   ```

4. **Test the API:**
   ```bash
   python api_endpoints.py
   ```
   Visit: `http://app.yourdomain.com:5000/api/health`

## Step 3: Install WordPress Plugin

1. **Upload the plugin:**
   - Zip the `betbot-wordpress-plugin` folder
   - Go to WordPress Admin → Plugins → Add New → Upload Plugin
   - Upload and activate the plugin

2. **Configure the plugin:**
   - Go to Settings → Bet Bot Manager
   - Set the API URL (e.g., `http://app.yourdomain.com:5000`)
   - Save settings

## Step 4: Create WordPress Pages

1. **Create Live Scores Page:**
   - Go to Pages → Add New
   - Title: "Live Scores"
   - Template: "Live Scores" (if using custom templates)
   - Or use shortcode: `[live_scores]`

2. **Create Guild Dashboard Page:**
   - Go to Pages → Add New
   - Title: "Guild Dashboard"
   - Template: "Guild Dashboard" (if using custom templates)
   - Or use shortcode: `[guild_stats]`

## Step 5: Upload Custom Templates (Optional)

1. **Upload page templates:**
   - Upload `wordpress_templates/page-live-scores.php` to your theme directory
   - Upload `wordpress_templates/page-guild-dashboard.php` to your theme directory
   - These will appear as template options when creating pages

## Step 6: Test the Integration

1. **Test API endpoints:**
   - Visit: `http://app.yourdomain.com:5000/api/guilds`
   - Visit: `http://app.yourdomain.com:5000/api/live-scores`

2. **Test WordPress pages:**
   - Visit your live scores page
   - Visit your guild dashboard page
   - Check browser console for any errors

## Troubleshooting

### Common Issues:

1. **API not accessible from WordPress:**
   - Check CORS settings in Flask API
   - Verify API URL in WordPress settings
   - Check firewall/security settings

2. **Database connection errors:**
   - Verify MySQL credentials in .env file
   - Check if database exists and has correct tables
   - Test database connection manually

3. **WordPress pages not loading data:**
   - Check browser console for JavaScript errors
   - Verify API endpoints are working
   - Check WordPress plugin settings

### Debug Steps:

1. **Test API directly:**
   ```bash
   curl http://app.yourdomain.com:5000/api/health
   ```

2. **Check WordPress debug log:**
   - Enable WP_DEBUG in wp-config.php
   - Check error logs in wp-content/debug.log

3. **Test database connection:**
   ```python
   import mysql.connector
   connection = mysql.connector.connect(
       host='localhost',
       user='your_username',
       password='your_password',
       database='your_database'
   )
   print("Database connected successfully!")
   ```

## Next Steps

1. **Customize the design** to match your WordPress theme
2. **Add more API endpoints** as needed
3. **Implement caching** for better performance
4. **Add authentication** if required
5. **Set up monitoring** and logging

## Support

If you encounter issues:
1. Check the browser console for JavaScript errors
2. Verify API endpoints are accessible
3. Test database connectivity
4. Review WordPress error logs
'''
    
    with open('WORDPRESS_DEPLOYMENT.md', 'w', encoding='utf-8') as f:
        f.write(instructions)
    
    print("Created WORDPRESS_DEPLOYMENT.md with detailed instructions")

def main():
    """Main function to set up WordPress + Flask integration."""
    
    print("Setting up WordPress + Flask integration...")
    print()
    
    # Create Flask API
    create_flask_api()
    print()
    
    # Create WordPress templates
    create_wordpress_templates()
    print()
    
    # Create WordPress plugin
    create_wordpress_plugin()
    print()
    
    # Create deployment instructions
    create_deployment_instructions()
    print()
    
    print("WordPress + Flask integration setup complete!")
    print()
    print("Files created:")
    print("- api_endpoints.py (Flask API)")
    print("- wordpress_templates/ (WordPress page templates)")
    print("- betbot-wordpress-plugin/ (WordPress plugin)")
    print("- WORDPRESS_DEPLOYMENT.md (Deployment instructions)")
    print()
    print("Next steps:")
    print("1. Set up WordPress on Bluehost")
    print("2. Deploy the Flask API")
    print("3. Install the WordPress plugin")
    print("4. Create pages using the templates or shortcodes")
    print("5. Test the integration")

if __name__ == '__main__':
    main() 