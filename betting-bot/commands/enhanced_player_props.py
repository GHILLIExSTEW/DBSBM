"""
Enhanced Player Props Command
Provides advanced player prop betting with search, validation, and modern UI.
"""

import logging

import discord
from config.leagues import LEAGUE_CONFIG
from discord import app_commands
from discord.ext import commands

from commands.admin import require_registered_guild
from commands.enhanced_player_prop_modal import setup_enhanced_player_prop

logger = logging.getLogger(__name__)


class EnhancedPlayerPropsCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db_manager = bot.db_manager

    @app_commands.command(
        name="playerprops",
        description="🏀 Place a player performance bet - points, rebounds, assists, etc.",
    )
    @require_registered_guild()
    async def playerprops(self, interaction: discord.Interaction):
        """Enhanced player props command with search and validation."""
        try:
            # Check if user is in allowed channel
            from commands.betting import is_allowed_command_channel

            if not await is_allowed_command_channel(interaction):
                return

            # Create embed with available leagues
            embed = discord.Embed(
                title="🎯 Enhanced Player Props",
                description="Select a league to create player prop bets with advanced search and validation.",
                color=discord.Color.blue(),
            )

            # Add league options
            for league_key, league_config in LEAGUE_CONFIG.items():
                if league_config.get("supports_player_props", True):  # Default to True
                    sport_icon = league_config.get("sport_icon", "🏈")
                    embed.add_field(
                        name=f"{sport_icon} {league_key}",
                        value=f"Available props: {', '.join(league_config.get('player_prop_types', ['Points', 'Rebounds', 'Assists']))}",
                        inline=True,
                    )

            embed.set_footer(
                text="Click a button below to select a league and start creating player prop bets"
            )

            # Create view with league selection buttons
            view = LeagueSelectionView(self.bot, self.db_manager)

            await interaction.response.send_message(
                embed=embed, view=view, ephemeral=True
            )

        except Exception as e:
            logger.error(f"Error in playerprops command: {e}", exc_info=True)
            await interaction.response.send_message(
                f"❌ **Error:** {str(e)}", ephemeral=True
            )


class LeagueSelectionView(discord.ui.View):
    """View for selecting a league for player props."""

    def __init__(self, bot: commands.Bot, db_manager):
        super().__init__(timeout=300)
        self.bot = bot
        self.db_manager = db_manager

        # Add buttons for each supported league
        for league_key, league_config in LEAGUE_CONFIG.items():
            if league_config.get("supports_player_props", True):
                sport_icon = league_config.get("sport_icon", "🏈")
                button = discord.ui.Button(
                    label=f"{sport_icon} {league_key}",
                    custom_id=f"league_{league_key}",
                    style=discord.ButtonStyle.primary,
                )
                button.callback = self.create_league_callback(league_key)
                self.add_item(button)

        # Add cancel button
        cancel_button = discord.ui.Button(
            label="❌ Cancel", style=discord.ButtonStyle.red, custom_id="cancel_league"
        )
        cancel_button.callback = self.cancel_callback
        self.add_item(cancel_button)

    def create_league_callback(self, league_key: str):
        """Create a callback function for a specific league."""

        async def callback(interaction: discord.Interaction):
            try:
                await self.handle_league_selection(interaction, league_key)
            except Exception as e:
                logger.error(
                    f"Error in league callback for {league_key}: {e}", exc_info=True
                )
                await interaction.response.send_message(
                    f"❌ **Error:** {str(e)}", ephemeral=True
                )

        return callback

    async def cancel_callback(self, interaction: discord.Interaction):
        """Handle cancel button click."""
        try:
            await interaction.response.edit_message(
                content="Player props cancelled.", view=None, embed=None
            )
        except Exception as e:
            logger.error(f"Error cancelling player props: {e}", exc_info=True)

    async def handle_league_selection(
        self, interaction: discord.Interaction, league_key: str
    ):
        """Handle league selection and show game selection."""
        try:
            # Get available games for this league
            games = await self.get_available_games(league_key)

            if not games:
                await interaction.response.send_message(
                    f"❌ **No games available** for {league_key} at the moment.\n"
                    "Try again later or select a different league.",
                    ephemeral=True,
                )
                return

            # Create game selection embed
            embed = discord.Embed(
                title=f"🎮 {league_key} Games",
                description=f"Select a game to create player prop bets for {league_key}.",
                color=discord.Color.green(),
            )

            # Add game options (limit to 10 to avoid too many buttons)
            for i, game in enumerate(games[:10], 1):
                home_team = game.get("home_team", "TBD")
                away_team = game.get("away_team", "TBD")
                game_time = game.get("game_time", "TBD")

                embed.add_field(
                    name=f"{i}. {away_team} @ {home_team}",
                    value=f"Time: {game_time}",
                    inline=False,
                )

            if len(games) > 10:
                embed.add_field(
                    name="Note",
                    value=f"Showing first 10 of {len(games)} games. More games available.",
                    inline=False,
                )

            # Create game selection view
            view = GameSelectionView(self.bot, self.db_manager, league_key, games[:10])

            await interaction.response.edit_message(embed=embed, view=view)

        except Exception as e:
            logger.error(f"Error handling league selection: {e}", exc_info=True)
            await interaction.response.send_message(
                f"❌ **Error:** {str(e)}", ephemeral=True
            )

    async def get_available_games(self, league_key: str) -> list:
        """Get available games for a league."""
        try:
            # Query games table for upcoming games in this league
            query = """
                SELECT game_id, home_team, away_team, game_time, league
                FROM games
                WHERE league = %s
                AND game_time > NOW()
                AND status = 'scheduled'
                ORDER BY game_time ASC
                LIMIT 20
            """

            games = await self.db_manager.fetch_all(query, (league_key,))

            # Format the results
            formatted_games = []
            for game in games:
                formatted_games.append(
                    {
                        "game_id": game["game_id"],
                        "home_team": game["home_team"],
                        "away_team": game["away_team"],
                        "game_time": game["game_time"].strftime("%m/%d %I:%M %p")
                        if game["game_time"]
                        else "TBD",
                        "league": game["league"],
                    }
                )

            return formatted_games

        except Exception as e:
            logger.error(
                f"Error getting available games for {league_key}: {e}", exc_info=True
            )
            return []


class GameSelectionView(discord.ui.View):
    """View for selecting a game for player props."""

    def __init__(self, bot: commands.Bot, db_manager, league_key: str, games: list):
        super().__init__(timeout=300)
        self.bot = bot
        self.db_manager = db_manager
        self.league_key = league_key
        self.games = games

        # Add buttons for each game
        for i, game in enumerate(games, 1):
            home_team = game.get("home_team", "TBD")
            away_team = game.get("away_team", "TBD")

            button = discord.ui.Button(
                label=f"{i}. {away_team} @ {home_team}",
                custom_id=f"game_{game['game_id']}",
                style=discord.ButtonStyle.secondary,
            )
            button.callback = self.create_game_callback(game)
            self.add_item(button)

        # Add back button
        back_button = discord.ui.Button(
            label="⬅️ Back to Leagues",
            style=discord.ButtonStyle.gray,
            custom_id="back_to_leagues",
        )
        back_button.callback = self.back_callback
        self.add_item(back_button)

    def create_game_callback(self, game: dict):
        """Create a callback function for a specific game."""

        async def callback(interaction: discord.Interaction):
            try:
                await self.handle_game_selection(interaction, game)
            except Exception as e:
                logger.error(f"Error in game callback: {e}", exc_info=True)
                await interaction.response.send_message(
                    f"❌ **Error:** {str(e)}", ephemeral=True
                )

        return callback

    async def back_callback(self, interaction: discord.Interaction):
        """Handle back button click."""
        try:
            # Recreate the league selection view
            from commands.enhanced_player_props import LeagueSelectionView

            view = LeagueSelectionView(self.bot, self.db_manager)

            embed = discord.Embed(
                title="🎯 Enhanced Player Props",
                description="Select a league to create player prop bets with advanced search and validation.",
                color=discord.Color.blue(),
            )

            for league_key, league_config in LEAGUE_CONFIG.items():
                if league_config.get("supports_player_props", True):
                    sport_icon = league_config.get("sport_icon", "🏈")
                    embed.add_field(
                        name=f"{sport_icon} {league_key}",
                        value=f"Available props: {', '.join(league_config.get('player_prop_types', ['Points', 'Rebounds', 'Assists']))}",
                        inline=True,
                    )

            embed.set_footer(
                text="Click a button below to select a league and start creating player prop bets"
            )

            await interaction.response.edit_message(embed=embed, view=view)

        except Exception as e:
            logger.error(f"Error going back to leagues: {e}", exc_info=True)

    async def handle_game_selection(self, interaction: discord.Interaction, game: dict):
        """Handle game selection and show team selection."""
        try:
            # Create team selection embed
            embed = discord.Embed(
                title=f"🏈 {game['away_team']} @ {game['home_team']}",
                description=f"Select a team to create player prop bets for.",
                color=discord.Color.purple(),
            )

            embed.add_field(name="📅 Game Time", value=game["game_time"], inline=False)

            embed.add_field(name="🏆 League", value=self.league_key, inline=False)

            # Create team selection view
            view = TeamSelectionView(
                self.bot,
                self.db_manager,
                self.league_key,
                game["game_id"],
                game["home_team"],
                game["away_team"],
            )

            await interaction.response.edit_message(embed=embed, view=view)

        except Exception as e:
            logger.error(f"Error handling game selection: {e}", exc_info=True)
            await interaction.response.send_message(
                f"❌ **Error:** {str(e)}", ephemeral=True
            )


class TeamSelectionView(discord.ui.View):
    """View for selecting a team for player props."""

    def __init__(
        self,
        bot: commands.Bot,
        db_manager,
        league_key: str,
        game_id: str,
        home_team: str,
        away_team: str,
    ):
        super().__init__(timeout=300)
        self.bot = bot
        self.db_manager = db_manager
        self.league_key = league_key
        self.game_id = game_id
        self.home_team = home_team
        self.away_team = away_team

        # Add buttons for each team
        home_button = discord.ui.Button(
            label=f"🏠 {home_team}",
            custom_id=f"team_{home_team}",
            style=discord.ButtonStyle.primary,
        )
        home_button.callback = self.create_team_callback(home_team)
        self.add_item(home_button)

        away_button = discord.ui.Button(
            label=f"✈️ {away_team}",
            custom_id=f"team_{away_team}",
            style=discord.ButtonStyle.primary,
        )
        away_button.callback = self.create_team_callback(away_team)
        self.add_item(away_button)

        # Add back button
        back_button = discord.ui.Button(
            label="⬅️ Back to Games",
            style=discord.ButtonStyle.gray,
            custom_id="back_to_games",
        )
        back_button.callback = self.back_callback
        self.add_item(back_button)

    def create_team_callback(self, team_name: str):
        """Create a callback function for a specific team."""

        async def callback(interaction: discord.Interaction):
            try:
                await self.handle_team_selection(interaction, team_name)
            except Exception as e:
                logger.error(f"Error in team callback: {e}", exc_info=True)
                await interaction.response.send_message(
                    f"❌ **Error:** {str(e)}", ephemeral=True
                )

        return callback

    async def back_callback(self, interaction: discord.Interaction):
        """Handle back button click."""
        try:
            # Recreate the game selection view
            games = await self.get_available_games(self.league_key)
            view = GameSelectionView(
                self.bot, self.db_manager, self.league_key, games[:10]
            )

            embed = discord.Embed(
                title=f"🎮 {self.league_key} Games",
                description=f"Select a game to create player prop bets for {self.league_key}.",
                color=discord.Color.green(),
            )

            for i, game in enumerate(games[:10], 1):
                home_team = game.get("home_team", "TBD")
                away_team = game.get("away_team", "TBD")
                game_time = game.get("game_time", "TBD")

                embed.add_field(
                    name=f"{i}. {away_team} @ {home_team}",
                    value=f"Time: {game_time}",
                    inline=False,
                )

            await interaction.response.edit_message(embed=embed, view=view)

        except Exception as e:
            logger.error(f"Error going back to games: {e}", exc_info=True)

    async def get_available_games(self, league_key: str) -> list:
        """Get available games for a league."""
        try:
            query = """
                SELECT game_id, home_team, away_team, game_time, league
                FROM games
                WHERE league = %s
                AND game_time > NOW()
                AND status = 'scheduled'
                ORDER BY game_time ASC
                LIMIT 20
            """

            games = await self.db_manager.fetch_all(query, (league_key,))

            formatted_games = []
            for game in games:
                formatted_games.append(
                    {
                        "game_id": game["game_id"],
                        "home_team": game["home_team"],
                        "away_team": game["away_team"],
                        "game_time": game["game_time"].strftime("%m/%d %I:%M %p")
                        if game["game_time"]
                        else "TBD",
                        "league": game["league"],
                    }
                )

            return formatted_games

        except Exception as e:
            logger.error(
                f"Error getting available games for {league_key}: {e}", exc_info=True
            )
            return []

    async def handle_team_selection(
        self, interaction: discord.Interaction, team_name: str
    ):
        """Handle team selection and show enhanced player prop modal."""
        try:
            # Create the enhanced player prop view
            view = await setup_enhanced_player_prop(
                self.bot, self.db_manager, self.league_key, self.game_id, team_name
            )

            embed = discord.Embed(
                title=f"🎯 Player Props - {team_name}",
                description=f"Create player prop bets for {team_name} players.\n\n"
                f"**Features:**\n"
                f"• 🔍 Smart player search\n"
                f"• ✅ Automatic validation\n"
                f"• 📊 Performance stats\n"
                f"• 🎨 Modern bet slips",
                color=discord.Color.gold(),
            )

            embed.add_field(name="🏆 League", value=self.league_key, inline=True)

            embed.add_field(
                name="🎮 Game", value=f"{self.away_team} @ {self.home_team}", inline=True
            )

            embed.add_field(name="👥 Team", value=team_name, inline=True)

            await interaction.response.edit_message(embed=embed, view=view)

        except Exception as e:
            logger.error(f"Error handling team selection: {e}", exc_info=True)
            await interaction.response.send_message(
                f"❌ **Error:** {str(e)}", ephemeral=True
            )


async def setup(bot: commands.Bot):
    """Setup the enhanced player props cog."""
    await bot.add_cog(EnhancedPlayerPropsCog(bot))
    logger.info("Enhanced Player Props cog loaded successfully")
