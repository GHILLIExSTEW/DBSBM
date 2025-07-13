import discord
from discord import app_commands
from discord.ext import commands
import aiohttp
import os
from datetime import datetime, timedelta
import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

class Odds(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.odds_api_key = os.getenv("ODDS_API_KEY")
        
        # Log the API key status (without exposing the actual key)
        if self.odds_api_key:
            logger.info("Odds API key configured successfully")
        else:
            logger.warning("Odds API key not found in environment variables")
        
        # Map your sports to Odds API sport keys
        self.sport_mapping = {
            "soccer": "soccer_epl",  # Default to EPL for soccer
            "basketball": "basketball_nba",
            "football": "americanfootball_nfl", 
            "hockey": "icehockey_nhl",
            "baseball": "baseball_mlb",
            "tennis": "tennis_atp_singles",
            "mma": "mma_mixed_martial_arts",
            "golf": "golf_pga_championship",
            "cricket": "cricket_test_match",
            "rugby": "rugbyleague_nrl",
            "australian_rules": "aussierules_afl",
            "darts": "darts_pdc_world_championship"
        }
        
        # Map your league names to Odds API sport keys
        self.league_sport_mapping = {
            # Soccer/Football
            "EPL": "soccer_epl",
            "Premier League": "soccer_epl",
            "WorldCup": "soccer_uefa_champs_league",  # FIFA Club World Cup
            "Champions League": "soccer_uefa_champs_league",
            "UEFA Champions League": "soccer_uefa_champs_league",
            "La Liga": "soccer_spain_la_liga",
            "Bundesliga": "soccer_germany_bundesliga",
            "Serie A": "soccer_italy_serie_a",
            "Ligue 1": "soccer_france_ligue_1",
            "MLS": "soccer_usa_mls",
            "A-League": "soccer_australia_aleague",
            "J League": "soccer_japan_j_league",
            "Brazil Série A": "soccer_brazil_campeonato",
            "Denmark Superliga": "soccer_denmark_superliga",
            "Veikkausliiga": "soccer_finland_veikkausliiga",
            "League of Ireland": "soccer_league_of_ireland",
            "Eliteserien": "soccer_norway_eliteserien",
            "La Liga 2": "soccer_spain_segunda_division",
            "Allsvenskan": "soccer_sweden_allsvenskan",
            "Superettan": "soccer_sweden_superettan",
            "UEFA Euro": "soccer_uefa_european_championship",
            
            # Basketball
            "NBA": "basketball_nba",
            "WNBA": "basketball_wnba",
            "NCAA": "basketball_ncaab",
            "EuroLeague": "basketball_euroleague",
            "Champions League": "basketball_champions_league",
            "Eurocup": "basketball_eurocup",
            "BIG3": "basketball_big3",
            "NIT": "basketball_nit",
            
            # American Football
            "NFL": "americanfootball_nfl",
            "NCAA": "americanfootball_ncaaf",
            "CFL": "americanfootball_cfl",
            "XFL": "americanfootball_xfl",
            "AFL": "americanfootball_afl",
            
            # Ice Hockey
            "NHL": "icehockey_nhl",
            "KHL": "icehockey_khl",
            
            # Baseball
            "MLB": "baseball_mlb",
            "NPB": "baseball_npb",
            "KBO": "baseball_kbo",
            "CPBL": "baseball_cpbl",
            "LIDOM": "baseball_lidom",
            "World Baseball Classic": "baseball_world_baseball_classic",
            "Italy": "baseball_italy",
            "Netherlands": "baseball_netherlands",
            "Spain": "baseball_spain",
            
            # Tennis
            "ATP": "tennis_atp_singles",
            "WTA": "tennis_wta_singles",
            "ATP French Open": "tennis_atp_french_open",
            "WTA French Open": "tennis_wta_french_open",
            "ATP US Open": "tennis_atp_us_open",
            "WTA US Open": "tennis_wta_us_open",
            "ATP Wimbledon": "tennis_atp_wimbledon",
            "WTA Wimbledon": "tennis_wta_wimbledon",
            "ATP Australian Open": "tennis_atp_australian_open",
            "WTA Australian Open": "tennis_wta_australian_open",
            
            # MMA
            "UFC": "mma_ufc",
            "MMA": "mma_mixed_martial_arts",
            
            # Golf
            "PGA Championship": "golf_pga_championship",
            "Masters Tournament": "golf_masters_tournament",
            "US Open": "golf_us_open",
            "The Open": "golf_the_open_championship",
            "Ryder Cup": "golf_ryder_cup",
            "Presidents Cup": "golf_presidents_cup",
            
            # Cricket
            "Test Matches": "cricket_test_match",
            "ODI": "cricket_odi",
            "T20": "cricket_t20",
            "IPL": "cricket_ipl",
            "Big Bash League": "cricket_big_bash_league",
            "Caribbean Premier League": "cricket_caribbean_premier_league",
            
            # Rugby
            "NRL": "rugbyleague_nrl",
            "Super Rugby": "rugby_union_super_rugby",
            "Six Nations": "rugby_union_six_nations",
            "Rugby Championship": "rugby_union_rugby_championship",
            "Heineken Cup": "rugby_union_heineken_cup",
            
            # Australian Rules Football
            "AFL": "aussierules_afl",
            
            # Darts
            "PDC": "darts_pdc_world_championship",
            "PDC World Championship": "darts_pdc_world_championship",
            
            # Handball
            "EHF": "handball_ehf_champions_league",
            
            # Motorsport
            "Formula 1": "motorsport_f1",
            "Formula 1": "motorsport_formula_1",
            "NASCAR": "motorsport_nascar",
            "IndyCar": "motorsport_indycar",
            "MotoGP": "motorsport_motogp",
            
            # Volleyball
            "Volleyball": "volleyball_volleyball",
            
            # Table Tennis
            "Table Tennis": "table_tennis_table_tennis",
            
            # Badminton
            "Badminton": "badminton_badminton",
            
            # Snooker
            "Snooker": "snooker_snooker",
            
            # Boxing
            "Boxing": "boxing_boxing",
            
            # Esports
            "CS:GO": "esports_csgo",
            "Dota 2": "esports_dota2",
            "League of Legends": "esports_lol",
            "Overwatch": "esports_overwatch",
            "Rocket League": "esports_rocket_league",
            "Valorant": "esports_valorant"
        }
    
    @app_commands.command(name="odds", description="Get current odds for upcoming games from your database")
    @app_commands.describe(
        hours="How many hours ahead to look for games (default: 24)"
    )
    async def odds(self, interaction: discord.Interaction, hours: int = 24):
        """Get odds for upcoming games from your database"""
        
        if not self.odds_api_key:
            await interaction.response.send_message("❌ Odds API key not configured!", ephemeral=True)
            return
        
        # Defer the response since API calls can take time
        await interaction.response.defer()
        
        try:
            # Get upcoming games from your database
            upcoming_games = await self.get_upcoming_games(hours)
            
            if not upcoming_games:
                await interaction.followup.send(f"❌ No upcoming games found in your database for the next {hours} hours.")
                return
            
            # Fetch odds for these games
            embeds = await self.fetch_odds_for_games(upcoming_games)
            
            if not embeds:
                await interaction.followup.send("❌ No odds data found for the upcoming games.")
                return
            
            # Send the embeds (Discord allows up to 10 per message)
            for i in range(0, len(embeds), 10):
                batch = embeds[i:i+10]
                await interaction.followup.send(embeds=batch)
                
        except Exception as e:
            logger.error(f"Error fetching odds: {e}")
            await interaction.followup.send(f"❌ Error fetching odds: {str(e)}")
    
    async def get_upcoming_games(self, hours_ahead: int) -> List[Dict]:
        """Get upcoming games from api_games table"""
        try:
            # Get database connection from bot
            db_manager = getattr(self.bot, 'db_manager', None)
            if not db_manager:
                raise Exception("Database manager not available")
            
            # Query upcoming games
            now = datetime.utcnow()
            future_time = now + timedelta(hours=hours_ahead)
            
            logger.info(f"Querying games between {now} and {future_time}")
            
            query = """
                SELECT 
                    api_game_id, sport, league_name, home_team_name, away_team_name, 
                    start_time, status
                FROM api_games 
                WHERE start_time BETWEEN %s AND %s
                AND status NOT IN ('Match Finished', 'Finished', 'FT', 'Ended', 'Game Finished', 'Final')
                ORDER BY start_time ASC 
                LIMIT 20
            """
            
            games = await db_manager.fetch_all(query, (now, future_time))
            logger.info(f"Found {len(games)} upcoming games in database")
            
            # Log some sample games for debugging
            for i, game in enumerate(games[:3]):
                logger.info(f"Game {i+1}: {game.get('home_team_name')} vs {game.get('away_team_name')} - {game.get('league_name')} - {game.get('start_time')}")
            
            return games
            
        except Exception as e:
            logger.error(f"Error getting upcoming games: {e}")
            return []
    
    async def fetch_odds_for_games(self, games: List[Dict]) -> List[discord.Embed]:
        """Fetch odds for specific games and return list of embeds"""
        embeds = []
        
        logger.info(f"Processing {len(games)} games for odds")
        
        for game in games:
            try:
                # Map sport/league to Odds API sport key
                odds_sport_key = self.get_odds_sport_key(game)
                if not odds_sport_key:
                    logger.warning(f"Could not map sport for game: {game.get('home_team_name')} vs {game.get('away_team_name')} - {game.get('league_name')}")
                    continue
                
                logger.info(f"Fetching odds for {game.get('home_team_name')} vs {game.get('away_team_name')} using sport key: {odds_sport_key}")
                
                # Fetch odds for this sport
                odds_data = await self.fetch_odds_from_api(odds_sport_key)
                if not odds_data:
                    logger.warning(f"No odds data returned for sport: {odds_sport_key}")
                    continue
                
                logger.info(f"Found {len(odds_data)} games in odds data for {odds_sport_key}")
                
                # Find matching game in odds data
                matching_odds = self.find_matching_game_odds(game, odds_data)
                if matching_odds:
                    logger.info(f"Found matching odds for {game.get('home_team_name')} vs {game.get('away_team_name')}")
                    embed = await self.create_odds_embed(game, matching_odds)
                    embeds.append(embed)
                else:
                    logger.warning(f"No matching odds found for {game.get('home_team_name')} vs {game.get('away_team_name')}")
                
            except Exception as e:
                logger.error(f"Error processing game {game.get('api_game_id')}: {e}")
                continue
        
        logger.info(f"Created {len(embeds)} odds embeds")
        return embeds
    
    def get_odds_sport_key(self, game: Dict) -> Optional[str]:
        """Map game sport/league to Odds API sport key"""
        sport = game.get('sport', '').lower()
        league_name = game.get('league_name', '')
        
        # Try league mapping first
        if league_name in self.league_sport_mapping:
            return self.league_sport_mapping[league_name]
        
        # Fall back to sport mapping
        if sport in self.sport_mapping:
            return self.sport_mapping[sport]
        
        return None
    
    async def fetch_odds_from_api(self, sport_key: str) -> Optional[List[Dict]]:
        """Fetch odds from The Odds API"""
        url = (
            f"https://api.the-odds-api.com/v4/sports/{sport_key}/odds"
            f"?apiKey={self.odds_api_key}&regions=us&markets=h2h&oddsFormat=american"
        )
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    # Log response headers for debugging
                    remaining = resp.headers.get('x-requests-remaining', 'unknown')
                    used = resp.headers.get('x-requests-used', 'unknown')
                    logger.info(f"Odds API response - Remaining: {remaining}, Used: {used}")
                    
                    if resp.status == 429:
                        logger.warning("Rate limited by Odds API - try again later")
                        return None
                    elif resp.status == 401:
                        logger.error("Odds API authentication failed - check your API key")
                        return None
                    elif resp.status == 403:
                        logger.error("Odds API access forbidden - check your subscription")
                        return None
                    elif resp.status != 200:
                        error_text = await resp.text()
                        logger.error(f"Odds API error {resp.status}: {error_text}")
                        return None
                    
                    data = await resp.json()
                    if isinstance(data, list):
                        logger.info(f"Successfully fetched {len(data)} games from Odds API for {sport_key}")
                        return data
                    else:
                        logger.warning(f"Unexpected response format from Odds API: {type(data)}")
                        return None
                    
        except Exception as e:
            logger.error(f"Error fetching odds from API: {e}")
            return None
    
    def find_matching_game_odds(self, game: Dict, odds_data: List[Dict]) -> Optional[Dict]:
        """Find matching game in odds data by team names"""
        home_team = game.get('home_team_name', '').lower()
        away_team = game.get('away_team_name', '').lower()
        
        for odds_game in odds_data:
            odds_home = odds_game.get('home_team', '').lower()
            odds_away = odds_game.get('away_team', '').lower()
            
            # Try exact match first
            if (home_team == odds_home and away_team == odds_away) or \
               (home_team == odds_away and away_team == odds_home):
                return odds_game
            
            # Try partial matches (handle team name variations)
            if self.teams_match(home_team, away_team, odds_home, odds_away):
                return odds_game
        
        return None
    
    def teams_match(self, home1: str, away1: str, home2: str, away2: str) -> bool:
        """Check if team names match (handling variations)"""
        # Simple matching - you can enhance this with more sophisticated logic
        home1_words = set(home1.split())
        away1_words = set(away1.split())
        home2_words = set(home2.split())
        away2_words = set(away2.split())
        
        # Check if there's significant overlap in team names
        home_match = len(home1_words & home2_words) >= 2 or len(home1_words & away2_words) >= 2
        away_match = len(away1_words & away2_words) >= 2 or len(away1_words & home2_words) >= 2
        
        return home_match and away_match
    
    async def create_odds_embed(self, game: Dict, odds_data: Dict) -> discord.Embed:
        """Create a Discord embed for odds data"""
        # Sport icons
        sport_icons = {
            "soccer": "⚽",
            "basketball": "🏀", 
            "football": "🏈",
            "hockey": "🏒",
            "baseball": "⚾",
            "tennis": "🎾",
            "mma": "🥊",
            "golf": "⛳",
            "cricket": "🏏",
            "rugby": "🏉",
            "australian_rules": "🏉",
            "darts": "🎯",
            "handball": "🤾",
            "motorsport": "🏎️",
            "volleyball": "🏐",
            "table_tennis": "🏓",
            "badminton": "🏸",
            "snooker": "🎱",
            "boxing": "🥊",
            "esports": "🎮"
        }
        
        sport = game.get('sport', '').lower()
        sport_icon = sport_icons.get(sport, "🏆")
        
        # Parse game time
        start_time = game.get('start_time')
        if isinstance(start_time, str):
            start_time = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
        
        time_str = f"<t:{int(start_time.timestamp())}:F>"
        time_relative = f"<t:{int(start_time.timestamp())}:R>"
        
        embed = discord.Embed(
            title=f"{sport_icon} {game['home_team_name']} vs {game['away_team_name']}",
            description=f"**Start Time:** {time_str} ({time_relative})\n**League:** {game.get('league_name', 'Unknown')}",
            color=0x00ff00,
            timestamp=datetime.utcnow()
        )
        
        # Add odds from top bookmakers
        top_bookmakers = ["fanduel", "draftkings", "betmgm"]
        odds_fields = []
        
        for bookmaker in odds_data.get("bookmakers", []):
            if bookmaker["key"] in top_bookmakers and len(odds_fields) < 3:
                market = next((m for m in bookmaker["markets"] if m["key"] == "h2h"), None)
                if market:
                    odds_str = "\n".join([
                        f"**{outcome['name']}:** {outcome['price']:+d}" 
                        for outcome in market["outcomes"]
                    ])
                    odds_fields.append(f"**{bookmaker['title']}**\n{odds_str}")
        
        if odds_fields:
            embed.add_field(
                name="💰 Current Odds",
                value="\n\n".join(odds_fields),
                inline=False
            )
        else:
            embed.add_field(
                name="💰 Odds",
                value="No odds available",
                inline=False
            )
        
        embed.set_footer(text="Data from The Odds API | Use /odds to check again")
        
        return embed

    @app_commands.command(name="sports", description="List all available sports and leagues for odds")
    async def sports(self, interaction: discord.Interaction):
        """List all available sports and leagues for odds"""
        
        embed = discord.Embed(
            title="🏆 Available Sports & Leagues for Odds",
            description="Here are all the sports and leagues supported by the `/odds` command:",
            color=0x00ff00,
            timestamp=datetime.utcnow()
        )
        
        # Group sports by category
        categories = {
            "⚽ Soccer/Football": [
                "EPL", "Premier League", "WorldCup", "Champions League", "La Liga", 
                "Bundesliga", "Serie A", "Ligue 1", "MLS", "A-League", "J League",
                "Brazil Série A", "UEFA Euro"
            ],
            "🏀 Basketball": [
                "NBA", "WNBA", "NCAA", "EuroLeague", "BIG3", "NIT"
            ],
            "🏈 American Football": [
                "NFL", "NCAA", "CFL", "XFL", "AFL"
            ],
            "🏒 Ice Hockey": [
                "NHL", "KHL"
            ],
            "⚾ Baseball": [
                "MLB", "NPB", "KBO", "CPBL", "LIDOM", "World Baseball Classic"
            ],
            "🎾 Tennis": [
                "ATP", "WTA", "ATP French Open", "WTA French Open", "ATP US Open", 
                "WTA US Open", "ATP Wimbledon", "WTA Wimbledon", "ATP Australian Open", 
                "WTA Australian Open"
            ],
            "🥊 MMA": [
                "UFC", "MMA"
            ],
            "⛳ Golf": [
                "PGA Championship", "Masters Tournament", "US Open", "The Open", 
                "Ryder Cup", "Presidents Cup"
            ],
            "🏏 Cricket": [
                "Test Matches", "ODI", "T20", "IPL", "Big Bash League", 
                "Caribbean Premier League"
            ],
            "🏉 Rugby": [
                "NRL", "Super Rugby", "Six Nations", "Rugby Championship", "Heineken Cup"
            ],
            "🎯 Other Sports": [
                "AFL (Australian Rules)", "PDC (Darts)", "EHF (Handball)", 
                "Formula 1", "NASCAR", "IndyCar", "MotoGP", "Volleyball", 
                "Table Tennis", "Badminton", "Snooker", "Boxing"
            ],
            "🎮 Esports": [
                "CS:GO", "Dota 2", "League of Legends", "Overwatch", 
                "Rocket League", "Valorant"
            ]
        }
        
        for category, leagues in categories.items():
            # Split long lists into multiple fields if needed
            if len(leagues) <= 8:
                embed.add_field(
                    name=category,
                    value=", ".join(leagues),
                    inline=False
                )
            else:
                # Split into chunks
                chunks = [leagues[i:i+8] for i in range(0, len(leagues), 8)]
                for i, chunk in enumerate(chunks):
                    field_name = category if i == 0 else f"{category} (cont.)"
                    embed.add_field(
                        name=field_name,
                        value=", ".join(chunk),
                        inline=False
                    )
        
        embed.set_footer(text="Use /odds to get current odds for upcoming games")
        
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Odds(bot)) 