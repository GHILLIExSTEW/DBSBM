import os
import json
from flask import Flask, render_template, redirect, url_for, request, jsonify, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv
import sys
from datetime import datetime, timedelta
import asyncio

# Ensure the parent directory is in sys.path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config.leagues import LEAGUE_IDS # Use the source of truth for league data
from data.db_manager import DatabaseManager

load_dotenv()
CACHE_DIR = os.path.join(os.path.dirname(__file__), "data", "cache")

app = Flask(__name__, static_folder="static")
CORS(app, origins=["https://www.betting-server-manager.com", "http://www.betting-server-manager.com"]) # Allow your website to connect

db = DatabaseManager()

def get_league_name_by_id(league_id: str) -> str:
    """Finds the league name from the LEAGUE_IDS config based on the league ID."""
    try:
        # Convert league_id from string to int for comparison
        target_id = int(league_id)
    except (ValueError, TypeError):
        return f"Invalid League ID {league_id}"

    for league_key, league_info in LEAGUE_IDS.items():
        if league_info.get('id') == target_id:
            return league_info.get('name', f"League {league_id}")
    
    return f"League {league_id}"

@app.route("/")
def landing():
    # Fetch all live games from the database
    live_games = asyncio.run(db.fetch_all("""
        SELECT 
            g.id,
            g.league,
            g.league_id,
            g.home_team_name,
            g.away_team_name,
            g.start_time,
            g.status,
            g.score,
            g.odds,
            tl_home.logo_url as home_logo,
            tl_away.logo_url as away_logo,
            ll.logo_url as league_logo
        FROM api_games g
        LEFT JOIN team_logos tl_home ON g.home_team_name = tl_home.team_key AND g.league = tl_home.league
        LEFT JOIN team_logos tl_away ON g.away_team_name = tl_away.team_key AND g.league = tl_away.league
        LEFT JOIN league_logos ll ON g.league = ll.league_key
        WHERE g.status IN ('live', 'in_progress', 'halftime')
        ORDER BY g.league, g.start_time
    """))

    # Group games by league
    league_games = {}
    for game in live_games:
        league_key = (game['league'], game.get('league_id'))
        if league_key not in league_games:
            league_games[league_key] = []
        league_games[league_key].append(game)

    # Get league info for display
    leagues = []
    for (league, league_id), games in league_games.items():
        league_info = {
            'name': league,
            'id': league_id,
            'logo': games[0]['league_logo'] if games and games[0]['league_logo'] else None,
            'games': games
        }
        leagues.append(league_info)

    # Get list of guilds with active games today and their unit totals
    active_guilds = asyncio.run(db.fetch_all("""
        WITH monthly_totals AS (
            SELECT 
                guild_id,
                SUM(CASE 
                    WHEN status = 'won' THEN units * (odds - 1)
                    WHEN status = 'lost' THEN -units
                    ELSE 0 
                END) as monthly_units
            FROM bets
            WHERE DATE(created_at) >= DATE_TRUNC('month', CURRENT_DATE)
            GROUP BY guild_id
        ),
        yearly_totals AS (
            SELECT 
                guild_id,
                SUM(CASE 
                    WHEN status = 'won' THEN units * (odds - 1)
                    WHEN status = 'lost' THEN -units
                    ELSE 0 
                END) as yearly_units
            FROM bets
            WHERE DATE(created_at) >= DATE_TRUNC('year', CURRENT_DATE)
            GROUP BY guild_id
        )
        SELECT DISTINCT 
            g.guild_id,
            g.guild_name,
            COALESCE(mt.monthly_units, 0) as monthly_units,
            COALESCE(yt.yearly_units, 0) as yearly_units
        FROM guilds g
        JOIN bets b ON g.guild_id = b.guild_id
        JOIN api_games ag ON b.game_id = ag.id
        LEFT JOIN monthly_totals mt ON g.guild_id = mt.guild_id
        LEFT JOIN yearly_totals yt ON g.guild_id = yt.guild_id
        WHERE DATE(ag.start_time) = CURRENT_DATE
        ORDER BY g.guild_name
    """))

    return render_template("landing.html", 
                         leagues=leagues,
                         active_guilds=active_guilds,
                         guild_id=None)

@app.route("/servers")
def server_list():
    guilds_data = asyncio.run(db.fetch_all("SELECT guild_id, guild_name FROM guilds ORDER BY guild_name"))
    servers = [{'id': str(g['guild_id']), 'name': g['guild_name']} for g in guilds_data]
    return render_template("server_list.html", servers=servers, guild_id=None)

@app.route("/guild/<guild_id>")
def guild_home(guild_id):
    guild_data = asyncio.run(db.fetch_one("SELECT guild_id, guild_name FROM guilds WHERE guild_id = %s", (guild_id,)))
    if guild_data:
        guild = {'id': str(guild_data['guild_id']), 'name': guild_data['guild_name']}
    else:
        guild = {'id': guild_id, 'name': f'Guild {guild_id}'}
    return render_template("guild_home.html", guild=guild, guild_id=guild_id)

@app.route("/live-scores")
def live_scores():
    """Displays a list of leagues with games today."""
    leagues_with_games = asyncio.run(db.fetch_all("""
        SELECT DISTINCT
            g.league as name,
            g.league_id as id,
            ll.logo_url as logo
        FROM api_games g
        LEFT JOIN league_logos ll ON g.league = ll.league_key
        WHERE DATE(g.start_time) = CURRENT_DATE
        ORDER BY g.league
    """))
    return render_template("live_scores.html", leagues=leagues_with_games, guild_id=None)

@app.route("/live-scores/<league_id>")
def live_scores_league_page(league_id):
    """Renders the page for a single league's scores. Data is fetched by JS."""
    league_name = get_league_name_by_id(league_id)
    return render_template("live_scores_league.html", league_id=league_id, league_name=league_name)

@app.route("/api/live-scores/<league_id>")
def api_live_scores_league(league_id):
    """API endpoint to get all of today's games for a specific league."""
    games = asyncio.run(db.fetch_all("""
        SELECT 
            g.id,
            g.home_team_name,
            g.away_team_name,
            g.start_time,
            g.status,
            g.score,
            tl_home.logo_url as home_logo,
            tl_away.logo_url as away_logo
        FROM api_games g
        LEFT JOIN team_logos tl_home ON g.home_team_name = tl_home.team_key AND g.league = tl_home.league
        LEFT JOIN team_logos tl_away ON g.away_team_name = tl_away.team_key AND g.league = tl_away.league
        WHERE g.league_id = %s AND DATE(g.start_time) = CURRENT_DATE
        ORDER BY g.start_time
    """, (league_id,)))

    for game in games:
        if isinstance(game.get('score'), str):
            try:
                game['score'] = json.loads(game['score'])
            except json.JSONDecodeError:
                game['score'] = {'home': '-', 'away': '-'}
        else:
            game['score'] = game.get('score', {'home': '-', 'away': '-'})

        if isinstance(game.get('start_time'), datetime):
            game['start_time_str'] = game['start_time'].strftime('%I:%M %p')
        else:
            game['start_time_str'] = 'TBD'

    league_name = get_league_name_by_id(league_id)
    
    return jsonify({
        'name': league_name,
        'games': games
    })

@app.route("/guild/<guild_id>/player-stats")
def player_stats(guild_id):
    guild_data = asyncio.run(db.fetch_one("SELECT guild_id, guild_name FROM guilds WHERE guild_id = %s", (guild_id,)))
    guild = {'id': str(guild_data['guild_id']), 'name': guild_data['guild_name']} if guild_data else {'id': guild_id, 'name': f'Guild {guild_id}'}
    return render_template("player_stats.html", guild=guild, guild_id=guild_id)

@app.route("/guild/<guild_id>/odds-buster")
def odds_buster(guild_id):
    guild_data = asyncio.run(db.fetch_one("SELECT guild_id, guild_name FROM guilds WHERE guild_id = %s", (guild_id,)))
    guild = {'id': str(guild_data['guild_id']), 'name': guild_data['guild_name']} if guild_data else {'id': guild_id, 'name': f'Guild {guild_id}'}
    return render_template("odds_buster.html", guild=guild, guild_id=guild_id)

@app.route("/guild/<guild_id>/playmaker-stats")
def playmaker_stats(guild_id):
    guild_data = asyncio.run(db.fetch_one("SELECT guild_id, guild_name FROM guilds WHERE guild_id = %s", (guild_id,)))
    guild = {'id': str(guild_data['guild_id']), 'name': guild_data['guild_name']} if guild_data else {'id': guild_id, 'name': f'Guild {guild_id}'}
    
    # Fetch cappers and their stats
    cappers = asyncio.run(db.fetch_all("""
        SELECT 
            c.user_id,
            c.display_name,
            c.banner_color,
            c.bet_won,
            c.bet_loss,
            c.bet_push,
            gu.units_balance,
            gu.lifetime_units,
            u.username,
            u.avatar_url
        FROM cappers c
        JOIN guild_users gu ON c.guild_id = gu.guild_id AND c.user_id = gu.user_id
        JOIN users u ON c.user_id = u.user_id
        WHERE c.guild_id = %s
        ORDER BY (c.bet_won::float / NULLIF(c.bet_won + c.bet_loss, 0)) DESC
    """, (guild_id,)))

    # For each capper, fetch their best bets and most bet on league
    for capper in cappers:
        # Best bets (highest unit wins)
        best_bets = asyncio.run(db.fetch_all("""
            SELECT 
                b.bet_serial,
                b.league,
                b.bet_type,
                b.units,
                b.odds,
                b.bet_details,
                b.created_at
            FROM bets b
            WHERE b.guild_id = %s 
            AND b.user_id = %s 
            AND b.status = 'won'
            ORDER BY b.units * (b.odds - 1) DESC
            LIMIT 5
        """, (guild_id, capper['user_id'])))

        # Most bet on league
        top_league = asyncio.run(db.fetch_one("""
            SELECT 
                league,
                COUNT(*) as bet_count,
                SUM(CASE WHEN status = 'won' THEN 1 ELSE 0 END) as wins,
                SUM(CASE WHEN status = 'lost' THEN 1 ELSE 0 END) as losses
            FROM bets
            WHERE guild_id = %s 
            AND user_id = %s
            GROUP BY league
            ORDER BY bet_count DESC
            LIMIT 1
        """, (guild_id, capper['user_id'])))

        capper['best_bets'] = best_bets
        capper['top_league'] = top_league

    return render_template("playmaker_stats.html", 
                         guild=guild, 
                         guild_id=guild_id,
                         cappers=cappers)

@app.route("/guild/<guild_id>/settings")
def guild_settings(guild_id):
    guild_data = asyncio.run(db.fetch_one("SELECT guild_id, guild_name FROM guilds WHERE guild_id = %s", (guild_id,)))
    guild = {'id': str(guild_data['guild_id']), 'name': guild_data['guild_name']} if guild_data else {'id': guild_id, 'name': f'Guild {guild_id}'}
    
    # Fetch guild settings
    settings = asyncio.run(db.fetch_one("""
        SELECT 
            gs.*,
            g.subscription_status,
            g.subscription_end_date
        FROM guild_settings gs
        JOIN guilds g ON gs.guild_id = g.guild_id
        WHERE gs.guild_id = %s
    """, (guild_id,)))

    # Fetch guild roles and channels for display
    roles = asyncio.run(db.fetch_all("""
        SELECT 
            role_id,
            role_name
        FROM guild_roles
        WHERE guild_id = %s
    """, (guild_id,)))

    channels = asyncio.run(db.fetch_all("""
        SELECT 
            channel_id,
            channel_name,
            channel_type
        FROM guild_channels
        WHERE guild_id = %s
    """, (guild_id,)))

    # Check if user is admin
    is_admin = asyncio.run(db.fetch_one("""
        SELECT is_admin
        FROM guild_users
        WHERE guild_id = %s AND user_id = %s
    """, (guild_id, request.args.get('user_id'))))

    return render_template("guild_settings.html", 
                         guild=guild, 
                         guild_id=guild_id,
                         settings=settings,
                         roles=roles,
                         channels=channels,
                         is_admin=is_admin.get('is_admin', False) if is_admin else False,
                         is_paid=settings.get('is_paid', False) if settings else False)

@app.route("/guild/<guild_id>/subscriptions")
def guild_subscriptions(guild_id):
    guild_data = asyncio.run(db.fetch_one("SELECT guild_id, guild_name FROM guilds WHERE guild_id = %s", (guild_id,)))
    guild = {'id': str(guild_data['guild_id']), 'name': guild_data['guild_name']} if guild_data else {'id': guild_id, 'name': f'Guild {guild_id}'}
    return render_template("subscriptions.html", guild=guild, guild_id=guild_id)

@app.route("/guild/<guild_id>/public")
def guild_public(guild_id):
    guild_data = asyncio.run(db.fetch_one("SELECT guild_id, guild_name FROM guilds WHERE guild_id = %s", (guild_id,)))
    guild = {'id': str(guild_data['guild_id']), 'name': guild_data['guild_name']} if guild_data else {'id': guild_id, 'name': f'Guild {guild_id}'}
    return render_template("guild_public.html", guild=guild, guild_id=guild_id)

@app.route("/live-scores/<league_id>")
def live_scores_league(league_id):
    try:
        league_name = get_league_name_by_id(league_id)
        # Fetch games for the specific league from the database
        games = asyncio.run(db.fetch_all("""
            SELECT 
                g.id,
                g.home_team_name,
                g.away_team_name,
                g.status,
                g.score,
                tl_home.logo_url as home_logo,
                tl_away.logo_url as away_logo
            FROM api_games g
            LEFT JOIN team_logos tl_home ON g.home_team_name = tl_home.team_key AND g.league = tl_home.league
            LEFT JOIN team_logos tl_away ON g.away_team_name = tl_away.team_key AND g.league = tl_away.league
            WHERE g.league_id = %s AND g.status IN ('live', 'in_progress', 'halftime')
            ORDER BY g.start_time
        """, (league_id,)))

        # Parse score from JSON string
        for game in games:
            if isinstance(game.get('score'), str):
                try:
                    game['score'] = json.loads(game['score'])
                except json.JSONDecodeError:
                    game['score'] = {'home': '-', 'away': '-'}

        return render_template("live_scores_league.html", league_id=league_id, league_name=league_name, games=games)
    except Exception as e:
        return f"Error loading live scores for league {league_id}: {e}", 500

@app.route('/static/<path:filename>')
def static_files(filename):
    print("Serving static file:", filename)
    return send_from_directory('static', filename)