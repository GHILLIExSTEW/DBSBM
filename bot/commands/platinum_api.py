import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

import aiohttp
import discord
from discord import app_commands
from discord.ext import commands

logger = logging.getLogger(__name__)


class SportDropdown(discord.ui.Select):
    def __init__(self, parent_view):
        self.parent_view = parent_view
        options = [
            discord.SelectOption(
                label="⚽ Football (Soccer)",
                value="football",
                description="Soccer leagues worldwide",
            ),
            discord.SelectOption(
                label="🏀 Basketball",
                value="basketball",
                description="NBA, WNBA, EuroLeague",
            ),
            discord.SelectOption(
                label="⚾ Baseball", value="baseball", description="MLB, NPB, KBO"
            ),
            discord.SelectOption(
                label="🏈 American Football",
                value="american-football",
                description="NFL, NCAA",
            ),
            discord.SelectOption(
                label="🏒 Hockey", value="hockey", description="NHL, KHL"
            ),
            discord.SelectOption(
                label="🎾 Tennis", value="tennis", description="ATP, WTA, Grand Slams"
            ),
            discord.SelectOption(
                label="🥊 MMA", value="mma", description="UFC, Bellator"
            ),
            discord.SelectOption(
                label="🏎️ Formula 1", value="formula-1", description="F1 Championship"
            ),
            discord.SelectOption(
                label="🏉 Rugby", value="rugby", description="Super Rugby, Six Nations"
            ),
            discord.SelectOption(
                label="🏐 Volleyball",
                value="volleyball",
                description="FIVB World League",
            ),
            discord.SelectOption(
                label="🤾 Handball",
                value="handball",
                description="EHF Champions League",
            ),
        ]
        super().__init__(
            placeholder="Select a sport...",
            min_values=1,
            max_values=1,
            options=options,
        )

    async def callback(self, interaction: discord.Interaction):
        sport = self.values[0]
        await self.parent_view.show_query_type_dropdown(interaction, sport)


class QueryTypeDropdown(discord.ui.Select):
    def __init__(self, parent_view, sport: str):
        self.parent_view = parent_view
        self.sport = sport
        options = [
            discord.SelectOption(
                label="🏆 Leagues",
                value="leagues",
                description="Available leagues for this sport",
            ),
            discord.SelectOption(
                label="👥 Players",
                value="players",
                description="Players by league or team",
            ),
            discord.SelectOption(
                label="⚽ Teams", value="teams", description="Teams in a league"
            ),
            discord.SelectOption(
                label="🏟️ Fixtures/Matches",
                value="fixtures",
                description="Upcoming and past matches",
            ),
            discord.SelectOption(
                label="💰 Odds", value="odds", description="Betting odds for matches"
            ),
            discord.SelectOption(
                label="📺 Live Matches",
                value="live",
                description="Currently live matches",
            ),
        ]
        super().__init__(
            placeholder="Select what to query...",
            min_values=1,
            max_values=1,
            options=options,
        )

    async def callback(self, interaction: discord.Interaction):
        query_type = self.values[0]
        await self.parent_view.show_league_dropdown(interaction, self.sport, query_type)


class LeagueDropdown(discord.ui.Select):
    def __init__(self, parent_view, sport: str, query_type: str):
        self.parent_view = parent_view
        self.sport = sport
        self.query_type = query_type

        # Define leagues for each sport
        leagues = {
            "football": [
                ("Premier League", 39, "England"),
                ("La Liga", 140, "Spain"),
                ("Bundesliga", 78, "Germany"),
                ("Serie A", 135, "Italy"),
                ("Ligue 1", 61, "France"),
                ("MLS", 253, "USA"),
                ("Champions League", 2, "Europe"),
                ("Europa League", 3, "Europe"),
                ("Brazil Serie A", 71, "Brazil"),
                ("World Cup", 15, "International"),
            ],
            "basketball": [
                ("NBA", 12, "USA"),
                ("WNBA", 13, "USA"),
                ("EuroLeague", 1, "Europe"),
            ],
            "baseball": [
                ("MLB", 1, "USA"),
                ("NPB", 2, "Japan"),
                ("KBO", 3, "South Korea"),
            ],
            "hockey": [
                ("NHL", 57, "USA/Canada"),
                ("KHL", 1, "Russia"),
            ],
            "american-football": [
                ("NFL", 1, "USA"),
                ("NCAA", 2, "USA"),
            ],
            "tennis": [
                ("ATP", 1, "International"),
                ("WTA", 2, "International"),
                ("Grand Slam", 3, "International"),
            ],
            "mma": [
                ("UFC", 1, "International"),
            ],
            "formula-1": [
                ("F1", 1, "International"),
            ],
            "rugby": [
                ("Super Rugby", 1, "International"),
                ("Six Nations", 2, "Europe"),
            ],
            "volleyball": [
                ("FIVB", 1, "International"),
            ],
            "handball": [
                ("EHF", 1, "Europe"),
            ],
        }

        sport_leagues = leagues.get(sport, [])
        options = []

        for league_name, league_id, country in sport_leagues:
            options.append(
                discord.SelectOption(
                    label=league_name,
                    value=str(league_id),
                    description=f"{country} • ID: {league_id}",
                )
            )

        super().__init__(
            placeholder="Select a league...",
            min_values=1,
            max_values=1,
            options=options,
        )

    async def callback(self, interaction: discord.Interaction):
        league_id = int(self.values[0])

        # For players query, show team selection
        if self.query_type == "players":
            await self.parent_view.show_team_dropdown(
                interaction, self.sport, self.query_type, league_id
            )
        else:
            # For other queries, execute directly
            await self.parent_view.execute_query(
                interaction, self.sport, self.query_type, league_id
            )


class TeamDropdown(discord.ui.Select):
    def __init__(self, parent_view, sport: str, query_type: str, league_id: int):
        self.parent_view = parent_view
        self.sport = sport
        self.query_type = query_type
        self.league_id = league_id
        super().__init__(
            placeholder="Loading teams...",
            min_values=1,
            max_values=1,
            options=[discord.SelectOption(label="Loading...", value="loading")],
        )

    async def callback(self, interaction: discord.Interaction):
        try:
            team_id = int(self.values[0])
            logger.info(
                f"Team selected: {team_id} for sport={self.sport}, query_type={self.query_type}, league_id={self.league_id}"
            )
            await self.parent_view.execute_query_with_team(
                interaction, self.sport, self.query_type, self.league_id, team_id
            )
        except Exception as e:
            logger.error(f"Error in TeamDropdown callback: {e}", exc_info=True)
            try:
                await interaction.response.send_message(
                    f"❌ An error occurred while processing your team selection: {str(e)}",
                    ephemeral=True,
                )
            except:
                await interaction.followup.send(
                    f"❌ An error occurred while processing your team selection: {str(e)}",
                    ephemeral=True,
                )

    async def load_teams(self, interaction: discord.Interaction):
        """Load teams for the selected league."""
        try:
            # Build parameters for teams query
            params = {"league": self.league_id}
            if self.sport in ["football", "basketball", "baseball", "hockey"]:
                params["season"] = datetime.now().year

            logger.info(
                f"Loading teams for sport={self.sport}, league={self.league_id}, params={params}"
            )

            # Make API request to get teams
            result = await self.parent_view.cog.make_api_request(
                self.sport, "teams", params
            )

            logger.info(f"Teams API response: {result}")

            if "error" in result or not result.get("response"):
                logger.warning(f"Teams API failed or returned no data: {result}")
                # If teams API fails, provide a generic option
                self.options = [
                    discord.SelectOption(
                        label="All Teams",
                        value="0",
                        description="Get players from all teams",
                    )
                ]
            else:
                teams = result.get("response", [])
                logger.info(f"Found {len(teams)} teams")
                self.options = []

                # Add "All Teams" option
                self.options.append(
                    discord.SelectOption(
                        label="All Teams",
                        value="0",
                        description="Get players from all teams",
                    )
                )

                # Add individual teams (limit to 24 for dropdown)
                for team in teams[:24]:  # 24 + "All Teams" = 25 total
                    # Handle different response structures
                    if isinstance(team, dict):
                        # Check if it's a nested team structure (football API)
                        if "team" in team:
                            team_info = team["team"]
                            name = team_info.get("name", "Unknown")
                            team_id = team_info.get("id", 0)
                        else:
                            # Direct team object (baseball API)
                            name = team.get("name", "Unknown")
                            team_id = team.get("id", 0)
                    else:
                        # Fallback
                        name = "Unknown"
                        team_id = 0

                    if team_id and name != "Unknown":
                        # Filter out league names (like "American League", "National League")
                        if name.lower() not in ["american league", "national league"]:
                            self.options.append(
                                discord.SelectOption(
                                    label=name[:100],  # Limit label length
                                    value=str(team_id),
                                    description=f"Team ID: {team_id}",
                                )
                            )

                # If no valid teams found, fall back to "All Teams"
                if len(self.options) == 1:  # Only "All Teams" option
                    logger.warning("No valid teams found in API response")

            self.placeholder = "Select a team..."

        except Exception as e:
            logger.error(f"Error loading teams: {e}", exc_info=True)
            self.options = [
                discord.SelectOption(
                    label="All Teams",
                    value="0",
                    description="Get players from all teams",
                )
            ]
            self.placeholder = "Select a team..."


class APIFlowView(discord.ui.View):
    def __init__(self, cog):
        super().__init__(timeout=120)
        self.cog = cog
        self.add_item(SportDropdown(self))

    async def show_query_type_dropdown(
        self, interaction: discord.Interaction, sport: str
    ):
        """Show the query type dropdown after sport selection."""
        embed = discord.Embed(
            title=f"🔍 API Query - {sport.title()}",
            description="What would you like to query?",
            color=0x9B59B6,
        )

        view = discord.ui.View(timeout=120)
        view.add_item(QueryTypeDropdown(self, sport))

        await interaction.response.edit_message(embed=embed, view=view)

    async def show_league_dropdown(
        self, interaction: discord.Interaction, sport: str, query_type: str
    ):
        """Show the league dropdown after query type selection."""
        embed = discord.Embed(
            title=f"🔍 API Query - {sport.title()} {query_type.title()}",
            description="Select a league:",
            color=0x9B59B6,
        )

        view = discord.ui.View(timeout=120)
        view.add_item(LeagueDropdown(self, sport, query_type))

        await interaction.response.edit_message(embed=embed, view=view)

    async def show_team_dropdown(
        self,
        interaction: discord.Interaction,
        sport: str,
        query_type: str,
        league_id: int,
    ):
        """Show the team dropdown for players queries."""
        embed = discord.Embed(
            title=f"🔍 API Query - {sport.title()} {query_type.title()}",
            description="Loading teams for the selected league...",
            color=0x9B59B6,
        )

        view = discord.ui.View(timeout=120)
        team_dropdown = TeamDropdown(self, sport, query_type, league_id)
        view.add_item(team_dropdown)

        await interaction.response.edit_message(embed=embed, view=view)

        # Load teams asynchronously
        await team_dropdown.load_teams(interaction)

        # Update the embed description
        if len(team_dropdown.options) > 1:
            embed.description = "Select a team to get players from:"
            # Update the message with the new embed
            await interaction.edit_original_response(embed=embed, view=view)
        else:
            embed.description = "No teams found. Getting all players from the league..."
            # Auto-select "All Teams" if no teams found
            await self.execute_query_with_team(
                interaction, sport, query_type, league_id, 0
            )

    async def execute_query(
        self,
        interaction: discord.Interaction,
        sport: str,
        query_type: str,
        league_id: int,
    ):
        """Execute the final API query and send results."""
        try:
            # Check Platinum status
            guild_id = interaction.guild_id
            if not await self.cog.bot.platinum_service.is_platinum_guild(guild_id):
                await interaction.response.edit_message(
                    content="❌ This feature requires a Platinum subscription.",
                    embed=None,
                    view=None,
                )
                return

            await interaction.response.edit_message(
                content="⏳ Querying API...", embed=None, view=None
            )

            # Build parameters based on query type
            params = {"league": league_id}

            # Add season for most queries
            if query_type in ["players", "teams", "fixtures", "odds"]:
                params["season"] = datetime.now().year

            logger.info(
                f"Executing API query: sport={sport}, type={query_type}, params={params}"
            )

            # Make API request
            result = await self.cog.make_api_request(sport, query_type, params)

            if "error" in result:
                await interaction.followup.send(
                    f"❌ API Error: {result['error']}", ephemeral=True
                )
                return

            # Process and display results
            await self.cog.display_query_results(interaction, sport, query_type, result)

        except Exception as e:
            logger.error(f"Error in API flow: {e}")
            await interaction.followup.send(
                "❌ An error occurred while processing your request.", ephemeral=True
            )

    async def execute_query_with_team(
        self,
        interaction: discord.Interaction,
        sport: str,
        query_type: str,
        league_id: int,
        team_id: int,
    ):
        """Execute the final API query with team selection for players."""
        try:
            logger.info(
                f"Starting execute_query_with_team: sport={sport}, query_type={query_type}, league_id={league_id}, team_id={team_id}"
            )

            # Check Platinum status
            guild_id = interaction.guild_id
            if not await self.cog.bot.platinum_service.is_platinum_guild(guild_id):
                logger.warning(f"Non-platinum guild attempted to use API: {guild_id}")
                await interaction.response.edit_message(
                    content="❌ This feature requires a Platinum subscription.",
                    embed=None,
                    view=None,
                )
                return

            logger.info("Platinum status check passed, proceeding with API query")

            # Check if interaction has already been responded to
            if interaction.response.is_done():
                logger.warning("Interaction already responded to, using followup")
                await interaction.followup.send("⏳ Querying API...", ephemeral=True)
            else:
                await interaction.response.edit_message(
                    content="⏳ Querying API...", embed=None, view=None
                )

            # Build parameters for players query
            params = {"league": league_id}
            if team_id > 0:
                params["team"] = team_id

            # Add season for players query - try current year first, then previous year if needed
            current_year = datetime.now().year
            params["season"] = current_year

            logger.info(
                f"Executing API query with team: sport={sport}, type={query_type}, league={league_id}, team={team_id}, params={params}"
            )

            # Make API request
            result = await self.cog.make_api_request(sport, query_type, params)

            # If no results and we're querying players, try with previous year
            if query_type == "players" and (
                not result.get("response") or len(result.get("response", [])) == 0
            ):
                logger.info(
                    f"No players found for season {current_year}, trying {current_year - 1}"
                )
                params["season"] = current_year - 1
                result = await self.cog.make_api_request(sport, query_type, params)

            logger.info(
                f"API request completed, result keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}"
            )

            if "error" in result:
                logger.error(f"API returned error: {result['error']}")
                await interaction.followup.send(
                    f"❌ API Error: {result['error']}", ephemeral=True
                )
                return

            # Process and display results
            logger.info("Calling display_query_results")
            await self.cog.display_query_results(interaction, sport, query_type, result)

        except Exception as e:
            logger.error(f"Error in API flow with team: {e}", exc_info=True)
            try:
                # Check if interaction has already been responded to
                if interaction.response.is_done():
                    await interaction.followup.send(
                        f"❌ An error occurred while processing your request: {str(e)}",
                        ephemeral=True,
                    )
                else:
                    await interaction.response.send_message(
                        f"❌ An error occurred while processing your request: {str(e)}",
                        ephemeral=True,
                    )
            except Exception as followup_error:
                logger.error(f"Failed to send error message: {followup_error}")
                # Try to respond to the original interaction
                try:
                    if not interaction.response.is_done():
                        await interaction.response.send_message(
                            f"❌ An error occurred while processing your request: {str(e)}",
                            ephemeral=True,
                        )
                except:
                    logger.error("Failed to send any error message to user")


class OddsPaginatedView(discord.ui.View):
    def __init__(
        self, cog, odds_data: List[Dict], sport: str, page: int = 0, page_size: int = 5
    ):
        super().__init__(timeout=120)
        self.cog = cog
        self.odds_data = odds_data
        self.sport = sport
        self.page = page
        self.page_size = page_size
        self.total_pages = (len(odds_data) + page_size - 1) // page_size

    @discord.ui.button(
        label="⬅️ Previous", style=discord.ButtonStyle.gray, disabled=True
    )
    async def previous_page(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        if self.page > 0:
            self.page -= 1
            await self.update_odds_display(interaction)

    @discord.ui.button(label="➡️ Next", style=discord.ButtonStyle.gray)
    async def next_page(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        if self.page < self.total_pages - 1:
            self.page += 1
            await self.update_odds_display(interaction)

    async def update_odds_display(self, interaction: discord.Interaction):
        start_idx = self.page * self.page_size
        end_idx = min(start_idx + self.page_size, len(self.odds_data))
        page_odds = self.odds_data[start_idx:end_idx]

        embed = discord.Embed(
            title=f"💰 {self.sport.title()} Odds",
            description=f"Page {self.page + 1} of {self.total_pages} • Showing {start_idx + 1}-{end_idx} of {len(self.odds_data)} entries",
            color=0x9B59B6,
        )

        for i, odds in enumerate(page_odds):
            # Extract team names - try multiple approaches
            home_team = "Unknown"
            away_team = "Unknown"

            # Log the structure for debugging
            logger.info(f"Odds entry structure: {odds}")

            # Try to get team names from various possible locations
            if "fixture" in odds and "teams" in odds["fixture"]:
                teams = odds["fixture"]["teams"]
                home_team = teams.get("home", {}).get("name", "Unknown")
                away_team = teams.get("away", {}).get("name", "Unknown")
            elif "teams" in odds:
                teams = odds["teams"]
                home_team = teams.get("home", {}).get("name", "Unknown")
                away_team = teams.get("away", {}).get("name", "Unknown")
            elif "game" in odds and "teams" in odds["game"]:
                teams = odds["game"]["teams"]
                home_team = teams.get("home", {}).get("name", "Unknown")
                away_team = teams.get("away", {}).get("name", "Unknown")
            else:
                # Try direct field access
                home_team = odds.get("home_team", odds.get("home", "Unknown"))
                away_team = odds.get("away_team", odds.get("away", "Unknown"))

            # Get bookmaker and odds information
            bookmakers = odds.get("bookmakers", [])
            if bookmakers:
                bookmaker_name = bookmakers[0].get("name", "Unknown")
                bets = bookmakers[0].get("bets", [])
                if bets:
                    bet_values = bets[0].get("values", [])
                    # Convert decimal odds to American odds
                    odds_text_parts = []
                    for v in bet_values[:3]:
                        value = v.get("value", "N/A")
                        decimal_odd = v.get("odd", "N/A")
                        if decimal_odd != "N/A":
                            american_odd = self.cog.decimal_to_american(decimal_odd)
                            odds_text_parts.append(f"{value}: {american_odd}")
                        else:
                            odds_text_parts.append(f"{value}: N/A")
                    odds_text = ", ".join(odds_text_parts)
                else:
                    odds_text = "No odds available"
            else:
                odds_text = "No bookmakers available"

            embed.add_field(
                name=f"{start_idx + i + 1}. {home_team} vs {away_team}",
                value=f"Odds: {odds_text}",
                inline=False,
            )

        # Update button states
        self.previous_page.disabled = self.page == 0
        self.next_page.disabled = self.page == self.total_pages - 1

        await interaction.response.edit_message(embed=embed, view=self)


class GenericPaginatedView(discord.ui.View):
    def __init__(
        self,
        cog,
        data: List[Dict],
        sport: str,
        query_type: str,
        page: int = 0,
        page_size: int = 10,
    ):
        super().__init__(timeout=120)
        self.cog = cog
        self.data = data
        self.sport = sport
        self.query_type = query_type
        self.page = page
        self.page_size = page_size
        self.total_pages = (len(data) + page_size - 1) // page_size

    @discord.ui.button(
        label="⬅️ Previous", style=discord.ButtonStyle.gray, disabled=True
    )
    async def previous_page(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        if self.page > 0:
            self.page -= 1
            await self.update_display(interaction)

    @discord.ui.button(label="➡️ Next", style=discord.ButtonStyle.gray)
    async def next_page(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        if self.page < self.total_pages - 1:
            self.page += 1
            await self.update_display(interaction)

    async def update_display(self, interaction: discord.Interaction):
        start_idx = self.page * self.page_size
        end_idx = min(start_idx + self.page_size, len(self.data))
        page_data = self.data[start_idx:end_idx]

        # Get title and emoji based on query type
        titles = {
            "leagues": ("🏆", "Leagues"),
            "players": ("👥", "Players"),
            "teams": ("⚽", "Teams"),
            "fixtures": ("🏟️", "Fixtures"),
            "live": ("🔴", "Live Matches"),
        }

        emoji, title_name = titles.get(self.query_type, ("📋", "Results"))

        embed = discord.Embed(
            title=f"{emoji} {self.sport.title()} {title_name}",
            description=f"Page {self.page + 1} of {self.total_pages} • Showing {start_idx + 1}-{end_idx} of {len(self.data)} entries",
            color=0x9B59B6,
        )

        # Process data based on query type
        if self.query_type == "leagues":
            for i, league in enumerate(page_data):
                league_info = league.get("league", {})
                name = league_info.get("name", "Unknown")
                country = league_info.get("country", "Unknown")
                type_name = league_info.get("type", "Unknown")

                embed.add_field(
                    name=f"{start_idx + i + 1}. {name}",
                    value=f"Country: {country}\nType: {type_name}",
                    inline=True,
                )

        elif self.query_type == "players":
            for i, player in enumerate(page_data):
                player_info = player.get("player", {})
                name = player_info.get("name", "Unknown")
                age = player_info.get("age", "Unknown")
                nationality = player_info.get("nationality", "Unknown")

                embed.add_field(
                    name=f"{start_idx + i + 1}. {name}",
                    value=f"Age: {age}\nNationality: {nationality}",
                    inline=True,
                )

        elif self.query_type == "teams":
            for i, team in enumerate(page_data):
                team_info = team.get("team", {})
                name = team_info.get("name", "Unknown")
                country = team_info.get("country", "Unknown")
                founded = team_info.get("founded", "Unknown")

                embed.add_field(
                    name=f"{start_idx + i + 1}. {name}",
                    value=f"Country: {country}\nFounded: {founded}",
                    inline=True,
                )

        elif self.query_type == "fixtures":
            for i, fixture in enumerate(page_data):
                teams = fixture.get("teams", {})
                home_team = teams.get("home", {}).get("name", "Unknown")
                away_team = teams.get("away", {}).get("name", "Unknown")
                fixture_info = fixture.get("fixture", {})
                date = fixture_info.get("date", "Unknown")
                status = fixture_info.get("status", {}).get("short", "Unknown")

                embed.add_field(
                    name=f"{start_idx + i + 1}. {home_team} vs {away_team}",
                    value=f"Date: {date}\nStatus: {status}",
                    inline=True,
                )

        elif self.query_type == "live":
            for i, match in enumerate(page_data):
                teams = match.get("teams", {})
                home_team = teams.get("home", {}).get("name", "Unknown")
                away_team = teams.get("away", {}).get("name", "Unknown")

                goals = match.get("goals", {})
                home_goals = goals.get("home", 0)
                away_goals = goals.get("away", 0)

                fixture_info = match.get("fixture", {})
                status = fixture_info.get("status", {}).get("short", "Unknown")
                elapsed = fixture_info.get("status", {}).get("elapsed", 0)

                embed.add_field(
                    name=f"{start_idx + i + 1}. {home_team} {home_goals} - {away_goals} {away_team}",
                    value=f"Status: {status}\nElapsed: {elapsed}'",
                    inline=True,
                )

        # Update button states
        self.previous_page.disabled = self.page == 0
        self.next_page.disabled = self.page == self.total_pages - 1

        await interaction.response.edit_message(embed=embed, view=self)


class PlatinumAPICog(commands.Cog):
    """Platinum tier API query commands for direct sports data access."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.api_base_urls = {
            "football": "https://v3.football.api-sports.io",
            "basketball": "https://v1.basketball.api-sports.io",
            "baseball": "https://v1.baseball.api-sports.io",
            "hockey": "https://v1.hockey.api-sports.io",
            "rugby": "https://v1.rugby.api-sports.io",
            "handball": "https://v1.handball.api-sports.io",
            "mma": "https://v1.mma.api-sports.io",
            "formula-1": "https://v1.formula-1.api-sports.io",
            "american-football": "https://v1.american-football.api-sports.io",
            "tennis": "https://v1.tennis.api-sports.io",
            "volleyball": "https://v1.volleyball.api-sports.io",
        }

    def decimal_to_american(self, decimal_odds: float) -> str:
        """Convert decimal odds to American odds format."""
        try:
            decimal_odds = float(decimal_odds)
            if decimal_odds >= 2.0:
                # Underdog odds (positive)
                american_odds = int((decimal_odds - 1) * 100)
                return f"+{american_odds}"
            else:
                # Favorite odds (negative)
                american_odds = int(-100 / (decimal_odds - 1))
                return str(american_odds)
        except (ValueError, TypeError, ZeroDivisionError):
            return "N/A"

    async def cog_app_command_error(
        self, interaction: discord.Interaction, error: app_commands.AppCommandError
    ):
        """Handle errors for Platinum API commands."""
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message(
                "❌ You don't have permission to use this command.", ephemeral=True
            )
        else:
            logger.error(f"Error in Platinum API command: {error}")
            await interaction.response.send_message(
                "❌ An error occurred while processing your command.", ephemeral=True
            )

    async def make_api_request(self, sport: str, endpoint: str, params: dict) -> dict:
        """Make a request to the sports API."""
        try:
            api_key = self.bot.sports_api.api_key
            base_url = self.api_base_urls.get(sport)

            if not base_url:
                return {"error": f"Unsupported sport: {sport}"}

            # Special handling for odds endpoint
            if endpoint == "odds":
                # Use the correct odds endpoint structure
                url = f"https://v1.{sport}.api-sports.io/odds"
            else:
                url = f"{base_url}/{endpoint}"

            logger.info(f"Making API request to: {url}")
            logger.info(f"Parameters: {params}")

            headers = {"x-apisports-key": api_key}

            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, params=params) as response:
                    logger.info(f"API response status: {response.status}")

                    if response.status == 200:
                        data = await response.json()
                        logger.info(
                            f"API response keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}"
                        )
                        logger.info(
                            f"API response count: {len(data.get('response', [])) if isinstance(data, dict) else 'N/A'}"
                        )
                        return data
                    else:
                        error_text = await response.text()
                        logger.error(
                            f"API request failed with status {response.status}: {error_text}"
                        )
                        return {
                            "error": f"API request failed with status {response.status}: {error_text}"
                        }

        except Exception as e:
            logger.error(f"Error making API request: {e}")
            return {"error": f"Request failed: {str(e)}"}

    async def _send_interaction_response(
        self,
        interaction: discord.Interaction,
        content=None,
        embed=None,
        view=None,
        ephemeral=False,
    ):
        """Helper function to send interaction response safely."""
        try:
            if interaction.response.is_done():
                await interaction.followup.send(
                    content=content, embed=embed, view=view, ephemeral=ephemeral
                )
            else:
                await interaction.response.send_message(
                    content=content, embed=embed, view=view, ephemeral=ephemeral
                )
        except Exception as e:
            logger.error(f"Error sending interaction response: {e}")

    async def display_query_results(
        self,
        interaction: discord.Interaction,
        sport: str,
        query_type: str,
        result: dict,
    ):
        """Display the results of an API query."""
        if "error" in result:
            embed = discord.Embed(
                title="❌ API Error", description=result["error"], color=0xFF0000
            )
            await self._send_interaction_response(
                interaction, embed=embed, ephemeral=True
            )
            return

        if query_type == "leagues":
            leagues = result.get("response", [])
            if not leagues:
                embed = discord.Embed(
                    title="🏆 Leagues Query",
                    description="No leagues found for the specified criteria.",
                    color=0x9B59B6,
                )
                await self._send_interaction_response(
                    interaction, embed=embed, ephemeral=True
                )
                return

            # Use pagination if more than 10 results
            if len(leagues) > 10:
                view = GenericPaginatedView(self, leagues, sport, "leagues")
                await view.update_display(interaction)
            else:
                embed = discord.Embed(
                    title=f"🏆 {sport.title()} Leagues",
                    description=f"Found {len(leagues)} leagues",
                    color=0x9B59B6,
                )
                for i, league in enumerate(leagues):
                    league_info = league.get("league", {})
                    name = league_info.get("name", "Unknown")
                    country = league_info.get("country", "Unknown")
                    type_name = league_info.get("type", "Unknown")

                    embed.add_field(
                        name=f"{i+1}. {name}",
                        value=f"Country: {country}\nType: {type_name}",
                        inline=True,
                    )
                await self._send_interaction_response(interaction, embed=embed)

        elif query_type == "players":
            players = result.get("response", [])
            if not players:
                # Get the parameters that were used for the query
                params_info = f"League ID: {result.get('parameters', {}).get('league', 'Unknown')}\n"
                params_info += f"Team ID: {result.get('parameters', {}).get('team', 'All teams')}\n"
                params_info += (
                    f"Season: {result.get('parameters', {}).get('season', 'Unknown')}"
                )

                embed = discord.Embed(
                    title="👥 Players Query",
                    description=f"No players found for the specified criteria.\n\n"
                    f"**Query Parameters:**\n{params_info}\n\n"
                    "**Possible Solutions:**\n"
                    "• Try selecting 'All Teams' instead of a specific team\n"
                    "• The team may not have active players in the current season\n"
                    "• Check if the league/team combination is valid\n"
                    "• Try a different season (the system automatically tries current and previous year)",
                    color=0x9B59B6,
                )
                await self._send_interaction_response(
                    interaction, embed=embed, ephemeral=True
                )
                return

            # Use pagination if more than 10 results
            if len(players) > 10:
                view = GenericPaginatedView(self, players, sport, "players")
                await view.update_display(interaction)
            else:
                embed = discord.Embed(
                    title=f"👥 {sport.title()} Players",
                    description=f"Found {len(players)} players",
                    color=0x9B59B6,
                )
                for i, player in enumerate(players):
                    player_info = player.get("player", {})
                    name = player_info.get("name", "Unknown")
                    age = player_info.get("age", "Unknown")
                    nationality = player_info.get("nationality", "Unknown")

                    embed.add_field(
                        name=f"{i+1}. {name}",
                        value=f"Age: {age}\nNationality: {nationality}",
                        inline=True,
                    )
                await self._send_interaction_response(interaction, embed=embed)

        elif query_type == "teams":
            teams = result.get("response", [])
            if not teams:
                embed = discord.Embed(
                    title="📋 Teams Query",
                    description="No teams found for the specified criteria.",
                    color=0x9B59B6,
                )
                await self._send_interaction_response(
                    interaction, embed=embed, ephemeral=True
                )
                return

            # Use pagination if more than 10 results
            if len(teams) > 10:
                view = GenericPaginatedView(self, teams, sport, "teams")
                await view.update_display(interaction)
            else:
                embed = discord.Embed(
                    title=f"🏈 {sport.title()} Teams",
                    description=f"Found {len(teams)} teams",
                    color=0x9B59B6,
                )
                for i, team in enumerate(teams):
                    team_info = team.get("team", {})
                    name = team_info.get("name", "Unknown")
                    country = team_info.get("country", "Unknown")
                    founded = team_info.get("founded", "Unknown")

                    embed.add_field(
                        name=f"{i+1}. {name}",
                        value=f"Country: {country}\nFounded: {founded}",
                        inline=True,
                    )
                await self._send_interaction_response(interaction, embed=embed)

        elif query_type == "fixtures":
            fixtures = result.get("response", [])
            if not fixtures:
                embed = discord.Embed(
                    title="📅 Fixtures Query",
                    description="No fixtures found for the specified criteria.",
                    color=0x9B59B6,
                )
                await self._send_interaction_response(
                    interaction, embed=embed, ephemeral=True
                )
                return

            # Use pagination if more than 10 results
            if len(fixtures) > 10:
                view = GenericPaginatedView(self, fixtures, sport, "fixtures")
                await view.update_display(interaction)
            else:
                embed = discord.Embed(
                    title=f"📅 {sport.title()} Fixtures",
                    description=f"Found {len(fixtures)} fixtures",
                    color=0x9B59B6,
                )
                for i, fixture in enumerate(fixtures):
                    teams = fixture.get("teams", {})
                    home_team = teams.get("home", {}).get("name", "Unknown")
                    away_team = teams.get("away", {}).get("name", "Unknown")
                    fixture_info = fixture.get("fixture", {})
                    date = fixture_info.get("date", "Unknown")
                    status = fixture_info.get("status", {}).get("short", "Unknown")

                    embed.add_field(
                        name=f"{i+1}. {home_team} vs {away_team}",
                        value=f"Date: {date}\nStatus: {status}",
                        inline=True,
                    )
                await self._send_interaction_response(interaction, embed=embed)

        elif query_type == "odds":
            odds_data = result.get("response", [])
            if not odds_data:
                embed = discord.Embed(
                    title="💰 Odds Query",
                    description="No odds found for the specified criteria.\n\n"
                    "**Possible reasons:**\n"
                    "• No upcoming matches in this league/season\n"
                    "• Odds not yet available for these matches\n"
                    "• League doesn't provide odds data\n\n"
                    "**Try:**\n"
                    "• Use `/api_fixtures` to find recent/upcoming matches\n"
                    "• Use `/api_leagues` to find league IDs\n"
                    "• Check if the season is current",
                    color=0x9B59B6,
                )
                await self._send_interaction_response(
                    interaction, embed=embed, ephemeral=True
                )
                return

            # Debug: Log the first odds entry structure
            if odds_data:
                logger.info(f"First odds entry structure: {odds_data[0]}")
                logger.info(f"Keys in first odds entry: {list(odds_data[0].keys())}")

            # Create paginated view and show first page
            view = OddsPaginatedView(self, odds_data, sport)
            start_idx = 0
            end_idx = min(5, len(odds_data))
            page_odds = odds_data[start_idx:end_idx]

            embed = discord.Embed(
                title=f"💰 {sport.title()} Odds",
                description=f"Page 1 of {view.total_pages} • Showing {start_idx + 1}-{end_idx} of {len(odds_data)} entries",
                color=0x9B59B6,
            )

            for i, odds in enumerate(page_odds):
                # Extract team names - try multiple approaches
                home_team = "Unknown"
                away_team = "Unknown"

                # Log the structure for debugging
                logger.info(f"Odds entry structure: {odds}")

                # Try to get team names from various possible locations
                if "fixture" in odds and "teams" in odds["fixture"]:
                    teams = odds["fixture"]["teams"]
                    home_team = teams.get("home", {}).get("name", "Unknown")
                    away_team = teams.get("away", {}).get("name", "Unknown")
                elif "teams" in odds:
                    teams = odds["teams"]
                    home_team = teams.get("home", {}).get("name", "Unknown")
                    away_team = teams.get("away", {}).get("name", "Unknown")
                elif "game" in odds and "teams" in odds["game"]:
                    teams = odds["game"]["teams"]
                    home_team = teams.get("home", {}).get("name", "Unknown")
                    away_team = teams.get("away", {}).get("name", "Unknown")
                else:
                    # Try direct field access
                    home_team = odds.get("home_team", odds.get("home", "Unknown"))
                    away_team = odds.get("away_team", odds.get("away", "Unknown"))

                # Get bookmaker and odds information
                bookmakers = odds.get("bookmakers", [])
                if bookmakers:
                    bookmaker_name = bookmakers[0].get("name", "Unknown")
                    bets = bookmakers[0].get("bets", [])
                    if bets:
                        bet_values = bets[0].get("values", [])
                        # Convert decimal odds to American odds
                        odds_text_parts = []
                        for v in bet_values[:3]:
                            value = v.get("value", "N/A")
                            decimal_odd = v.get("odd", "N/A")
                            if decimal_odd != "N/A":
                                american_odd = self.decimal_to_american(decimal_odd)
                                odds_text_parts.append(f"{value}: {american_odd}")
                            else:
                                odds_text_parts.append(f"{value}: N/A")
                        odds_text = ", ".join(odds_text_parts)
                    else:
                        odds_text = "No odds available"
                else:
                    odds_text = "No bookmakers available"

                embed.add_field(
                    name=f"{start_idx + i + 1}. {home_team} vs {away_team}",
                    value=f"Odds: {odds_text}",
                    inline=False,
                )

            # Update button states
            view.previous_page.disabled = True
            view.next_page.disabled = view.total_pages <= 1

            await self._send_interaction_response(interaction, embed=embed, view=view)

        elif query_type == "live":
            live_matches = result.get("response", [])
            if not live_matches:
                embed = discord.Embed(
                    title="🔴 Live Matches",
                    description="No live matches currently playing.",
                    color=0x9B59B6,
                )
                await self._send_interaction_response(
                    interaction, embed=embed, ephemeral=True
                )
                return

            # Use pagination if more than 10 results
            if len(live_matches) > 10:
                view = GenericPaginatedView(self, live_matches, sport, "live")
                await view.update_display(interaction)
            else:
                embed = discord.Embed(
                    title=f"🔴 Live {sport.title()} Matches",
                    description=f"Found {len(live_matches)} live matches",
                    color=0xFF0000,
                )
                for i, match in enumerate(live_matches):
                    teams = match.get("teams", {})
                    home_team = teams.get("home", {}).get("name", "Unknown")
                    away_team = teams.get("away", {}).get("name", "Unknown")

                    goals = match.get("goals", {})
                    home_goals = goals.get("home", 0)
                    away_goals = goals.get("away", 0)

                    fixture_info = match.get("fixture", {})
                    status = fixture_info.get("status", {}).get("short", "Unknown")
                    elapsed = fixture_info.get("status", {}).get("elapsed", 0)

                    embed.add_field(
                        name=f"{i+1}. {home_team} {home_goals} - {away_goals} {away_team}",
                        value=f"Status: {status}\nElapsed: {elapsed}'",
                        inline=True,
                    )
                await self._send_interaction_response(interaction, embed=embed)

    @app_commands.command(
        name="api",
        description="Interactive sports API query with dropdowns (Platinum only)",
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def api(self, interaction: discord.Interaction):
        """Start the interactive API query flow."""
        try:
            guild_id = interaction.guild_id

            # Check Platinum status
            if not await self.bot.platinum_service.is_platinum_guild(guild_id):
                await interaction.response.send_message(
                    "❌ This feature requires a Platinum subscription.", ephemeral=True
                )
                return

            embed = discord.Embed(
                title="🔍 Sports API Query",
                description="Select a sport to start your query:",
                color=0x9B59B6,
            )

            view = APIFlowView(self)
            await interaction.response.send_message(
                embed=embed, view=view, ephemeral=True
            )

        except Exception as e:
            logger.error(f"Error in api command: {e}")
            await interaction.response.send_message(
                "❌ An error occurred while starting the API query.", ephemeral=True
            )


async def setup(bot: commands.Bot):
    """Setup function for the Platinum API cog."""
    await bot.add_cog(PlatinumAPICog(bot))
    logger.info("PlatinumAPICog loaded successfully")
