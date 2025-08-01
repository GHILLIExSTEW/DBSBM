#!/usr/bin/env python3
import os
import sys
import cgitb
cgitb.enable()

# Add the parent directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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

def get_dashboard_data():
    connection = get_db_connection()
    if not connection:
        return None
    
    try:
        cursor = connection.cursor()
        
        # Get total bets
        cursor.execute("SELECT COUNT(*) FROM bets")
        total_bets = cursor.fetchone()[0]
        
        # Get recent bets
        cursor.execute("SELECT bet_serial, bet_type, units, created_at, guild_id FROM bets ORDER BY created_at DESC LIMIT 10")
        recent_bets = cursor.fetchall()
        
        # Get guild stats
        cursor.execute("SELECT guild_id, is_active, subscription_level FROM guild_settings")
        guilds = cursor.fetchall()
        
        # Get monthly stats
        cursor.execute("SELECT COUNT(*) FROM bets WHERE created_at >= DATE_SUB(NOW(), INTERVAL 30 DAY)")
        monthly_bets = cursor.fetchone()[0]
        
        cursor.close()
        connection.close()
        
        return {
            'total_bets': total_bets,
            'monthly_bets': monthly_bets,
            'recent_bets': recent_bets,
            'guilds': guilds
        }
    except Exception as e:
        return None

# Route to dashboard
if path == '/dashboard':
    data = get_dashboard_data()
    if data:
        print("Content-Type: text/html")
        print()
        print(f"""
        <html>
        <head>
            <title>BetBot Dashboard</title>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                * {{ margin: 0; padding: 0; box-sizing: border-box; }}
                body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; color: white; }}
                .container {{ max-width: 1200px; margin: 0 auto; padding: 20px; }}
                .header {{ text-align: center; margin-bottom: 40px; }}
                .header h1 {{ font-size: 3em; margin-bottom: 10px; text-shadow: 2px 2px 4px rgba(0,0,0,0.3); }}
                .stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 40px; }}
                .stat-card {{ background: rgba(255,255,255,0.1); padding: 30px; border-radius: 15px; backdrop-filter: blur(10px); text-align: center; }}
                .stat-number {{ font-size: 3em; font-weight: bold; margin: 10px 0; }}
                .content-grid {{ display: grid; grid-template-columns: 2fr 1fr; gap: 30px; }}
                .section {{ background: rgba(255,255,255,0.1); padding: 30px; border-radius: 15px; backdrop-filter: blur(10px); }}
                .section h2 {{ margin-bottom: 20px; font-size: 1.5em; }}
                .bet-item {{ background: rgba(255,255,255,0.05); padding: 15px; margin: 10px 0; border-radius: 10px; border-left: 4px solid #4CAF50; }}
                .guild-item {{ background: rgba(255,255,255,0.05); padding: 15px; margin: 10px 0; border-radius: 10px; border-left: 4px solid #2196F3; }}
                .nav {{ text-align: center; margin-top: 30px; }}
                .nav a {{ color: white; text-decoration: none; margin: 0 15px; padding: 10px 20px; background: rgba(255,255,255,0.1); border-radius: 5px; transition: all 0.3s; }}
                .nav a:hover {{ background: rgba(255,255,255,0.2); transform: translateY(-2px); }}
                @media (max-width: 768px) {{
                    .content-grid {{ grid-template-columns: 1fr; }}
                    .stats-grid {{ grid-template-columns: 1fr; }}
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🎯 BetBot Dashboard</h1>
                    <p>Real-time betting analytics and guild management</p>
                </div>
                
                <div class="stats-grid">
                    <div class="stat-card">
                        <h3>💰 Total Bets</h3>
                        <div class="stat-number">{data['total_bets']}</div>
                    </div>
                    <div class="stat-card">
                        <h3>💰 Monthly Bets</h3>
                        <div class="stat-number">{data['monthly_bets']}</div>
                    </div>
                    <div class="stat-card">
                        <h3>👥 Active Guilds</h3>
                        <div class="stat-number">{len(data['guilds'])}</div>
                    </div>
                </div>
                
                <div class="content-grid">
                    <div class="section">
                        <h2>🎯 Recent Bets</h2>
                        {''.join([f'<div class="bet-item"><strong>Bet {bet[0]}</strong> - {bet[1]} ({bet[2]} units) - {bet[4]} - {bet[3]}</div>' for bet in data['recent_bets']])}
                    </div>
                    
                    <div class="section">
                        <h2>⚙️ Guild Settings</h2>
                        {''.join([f'<div class="guild-item"><strong>Guild {guild[0]}</strong><br>Active: {guild[1]}<br>Subscription: {guild[2]}</div>' for guild in data['guilds']])}
                    </div>
                </div>
                
                <div class="nav">
                    <a href="/health">Health Check</a>
                    <a href="/api/stats">API Stats</a>
                    <a href="/api/status">API Status</a>
                    <a href="/live-scores">Live Scores</a>
                </div>
            </div>
        </body>
        </html>
        """)
    else:
        print("Content-Type: text/html")
        print()
        print("<html><body><h1>Database Connection Error</h1></body></html>")
else:
    # Redirect to dashboard
    print("Content-Type: text/html")
    print()
    print("<html><head><meta http-equiv='refresh' content='0;url=/dashboard'></head></html>")
