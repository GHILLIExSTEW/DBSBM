#!/usr/bin/env python3
import os
import sys
import cgitb
cgitb.enable()

# Get the request path
path = os.environ.get('PATH_INFO', '/')

# Database connection function
def get_db_connection():
    import mysql.connector
    try:
        connection = mysql.connector.connect(
            host='na05-sql.pebblehost.com',
            user='customer_990306_Server_database',
            password='NGNrWmR@IypQb4k@tzgk+NnI',
            database='customer_990306_Server_database',
            port=3306)
        return connection
    except Exception as e:
        return None

def get_live_games():
    connection = get_db_connection()
    if not connection:
        return []
    
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT id, home_team_name, away_team_name, status, start_time FROM games WHERE status IN ('LIVE', 'HT', '1H', '2H') ORDER BY start_time DESC LIMIT 10")
        games = cursor.fetchall()
        cursor.close()
        connection.close()
        return games
    except Exception as e:
        return []

if path == '/live-scores':
    games = get_live_games()
    print("Content-Type: text/html")
    print()
    print(f"""
    <html>
    <head>
        <title>Live Scores - BetBot</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; color: white; }}
            .container {{ max-width: 1200px; margin: 0 auto; padding: 20px; }}
            .header {{ text-align: center; margin-bottom: 40px; }}
            .header h1 {{ font-size: 3em; margin-bottom: 10px; text-shadow: 2px 2px 4px rgba(0,0,0,0.3); }}
            .game-card {{ background: rgba(255,255,255,0.1); padding: 20px; margin: 15px 0; border-radius: 15px; backdrop-filter: blur(10px); }}
            .game-teams {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }}
            .team {{ font-size: 1.2em; font-weight: bold; }}
            .game-status {{ text-align: center; font-size: 0.9em; opacity: 0.8; }}
            .nav {{ text-align: center; margin-top: 30px; }}
            .nav a {{ color: white; text-decoration: none; margin: 0 15px; padding: 10px 20px; background: rgba(255,255,255,0.1); border-radius: 5px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>⚽ Live Scores</h1>
                <p>Real-time game updates</p>
            </div>
            
            {''.join([f'''
            <div class="game-card">
                <div class="game-teams">
                    <div class="team">{game[1]}</div>
                    <div class="team">vs</div>
                    <div class="team">{game[2]}</div>
                </div>
                <div class="game-status">Status: {game[3]} | Time: {game[4]}</div>
            </div>
            ''' for game in games])}
            
            <div class="nav">
                <a href="/dashboard">Dashboard</a>
                <a href="/health">Health Check</a>
            </div>
        </div>
    </body>
    </html>
    """)
