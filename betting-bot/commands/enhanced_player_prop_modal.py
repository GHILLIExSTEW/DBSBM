"""
Enhanced Player Prop Modal
Provides improved player search, prop type selection, and validation.
"""

import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional, List
import asyncio
import logging

from config.prop_templates import get_prop_templates_for_league, get_prop_groups_for_league, validate_prop_value
from services.player_search_service import PlayerSearchService, PlayerSearchResult

logger = logging.getLogger(__name__)

class EnhancedPlayerPropModal(discord.ui.Modal, title="Player Prop Bet"):
    """Enhanced modal for player prop betting with search and validation."""
    
    def __init__(self, bot, db_manager, league: str, game_id: str, team_name: str):
        super().__init__()
        self.bot = bot
        self.db_manager = db_manager
        self.league = league
        self.game_id = game_id
        self.team_name = team_name
        self.player_search_service = PlayerSearchService(db_manager)
        
        # Get prop templates for this league
        self.prop_templates = get_prop_templates_for_league(league)
        self.prop_groups = get_prop_groups_for_league(league)
        
        # Initialize UI components
        self._setup_ui_components()
    
    def _setup_ui_components(self):
        """Setup the UI components for the modal."""
        # Player search input
        self.player_search = discord.ui.TextInput(
            label="Search Player",
            placeholder="Type player name to search...",
            style=discord.TextStyle.short,
            required=True,
            max_length=100
        )
        
        # Prop type selection
        prop_types = list(self.prop_templates.keys())
        self.prop_type = discord.ui.TextInput(
            label="Prop Type",
            placeholder=f"Available: {', '.join(prop_types[:5])}...",
            style=discord.TextStyle.short,
            required=True,
            max_length=50
        )
        
        # Line value input
        self.line_value = discord.ui.TextInput(
            label="Line Value",
            placeholder="Enter the over/under line (e.g., 25.5)",
            style=discord.TextStyle.short,
            required=True,
            max_length=10
        )
        
        # Bet direction
        self.bet_direction = discord.ui.TextInput(
            label="Over/Under",
            placeholder="Type 'over' or 'under'",
            style=discord.TextStyle.short,
            required=True,
            max_length=10
        )
        
        # Bet amount
        self.bet_amount = discord.ui.TextInput(
            label="Bet Amount",
            placeholder="Enter bet amount (e.g., 10.00)",
            style=discord.TextStyle.short,
            required=True,
            max_length=10
        )
        
        # Add components to modal
        self.add_item(self.player_search)
        self.add_item(self.prop_type)
        self.add_item(self.line_value)
        self.add_item(self.bet_direction)
        self.add_item(self.bet_amount)
    
    async def on_submit(self, interaction: discord.Interaction):
        """Handle modal submission with validation."""
        try:
            # Validate and process inputs
            validation_result = await self._validate_inputs()
            
            if not validation_result['valid']:
                await interaction.response.send_message(
                    f"❌ **Validation Error:** {validation_result['error']}",
                    ephemeral=True
                )
                return
            
            # Create the bet
            bet_data = validation_result['bet_data']
            success = await self._create_player_prop_bet(interaction, bet_data)
            
            if success:
                await interaction.response.send_message(
                    f"✅ **Player Prop Bet Created!**\n"
                    f"**{bet_data['player_name']}** - {bet_data['prop_type']}\n"
                    f"{bet_data['bet_direction'].upper()} {bet_data['line_value']}\n"
                    f"Amount: ${bet_data['bet_amount']}",
                    ephemeral=True
                )
            else:
                await interaction.response.send_message(
                    "❌ **Error creating bet.** Please try again.",
                    ephemeral=True
                )
                
        except Exception as e:
            logger.error(f"Error in player prop modal submission: {e}")
            await interaction.response.send_message(
                "❌ **An error occurred.** Please try again.",
                ephemeral=True
            )
    
    async def _validate_inputs(self) -> dict:
        """Validate all modal inputs."""
        try:
            # Validate player search
            player_name = self.player_search.value.strip()
            if len(player_name) < 2:
                return {
                    'valid': False,
                    'error': 'Player name must be at least 2 characters long.'
                }
            
            # Search for player
            search_results = await self.player_search_service.search_players(
                player_name, self.league, limit=1, min_confidence=70.0
            )
            
            if not search_results:
                return {
                    'valid': False,
                    'error': f'Player "{player_name}" not found. Try a different search term.'
                }
            
            selected_player = search_results[0]
            
            # Validate prop type
            prop_type = self.prop_type.value.strip().lower()
            if prop_type not in self.prop_templates:
                available_types = ', '.join(list(self.prop_templates.keys())[:10])
                return {
                    'valid': False,
                    'error': f'Invalid prop type. Available types: {available_types}'
                }
            
            # Validate line value
            try:
                line_value = float(self.line_value.value.strip())
                if not validate_prop_value(self.league, prop_type, line_value):
                    template = self.prop_templates[prop_type]
                    return {
                        'valid': False,
                        'error': f'Line value must be between {template.min_value} and {template.max_value} {template.unit}.'
                    }
            except ValueError:
                return {
                    'valid': False,
                    'error': 'Line value must be a valid number.'
                }
            
            # Validate bet direction
            bet_direction = self.bet_direction.value.strip().lower()
            if bet_direction not in ['over', 'under']:
                return {
                    'valid': False,
                    'error': 'Bet direction must be "over" or "under".'
                }
            
            # Validate bet amount
            try:
                bet_amount = float(self.bet_amount.value.strip())
                if bet_amount <= 0:
                    return {
                        'valid': False,
                        'error': 'Bet amount must be greater than 0.'
                    }
            except ValueError:
                return {
                    'valid': False,
                    'error': 'Bet amount must be a valid number.'
                }
            
            # All validations passed
            return {
                'valid': True,
                'bet_data': {
                    'player_name': selected_player.player_name,
                    'team_name': selected_player.team_name,
                    'league': self.league,
                    'sport': selected_player.sport,
                    'prop_type': prop_type,
                    'line_value': line_value,
                    'bet_direction': bet_direction,
                    'bet_amount': bet_amount,
                    'game_id': self.game_id
                }
            }
            
        except Exception as e:
            logger.error(f"Error validating inputs: {e}")
            return {
                'valid': False,
                'error': 'An error occurred during validation.'
            }
    
    async def _create_player_prop_bet(self, interaction: discord.Interaction, bet_data: dict) -> bool:
        """Create the player prop bet in the database."""
        try:
            # Insert into bets table
            query = """
                INSERT INTO bets (
                    user_id, guild_id, bet_type, player_prop, player_name, 
                    team_name, league, sport, player_prop_type, player_prop_line,
                    player_prop_direction, bet_amount, game_id, status, created_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
            """
            
            await self.db_manager.execute(
                query,
                (
                    interaction.user.id,
                    interaction.guild_id,
                    'player_prop',
                    True,
                    bet_data['player_name'],
                    bet_data['team_name'],
                    bet_data['league'],
                    bet_data['sport'],
                    bet_data['prop_type'],
                    bet_data['line_value'],
                    bet_data['bet_direction'],
                    bet_data['bet_amount'],
                    bet_data['game_id'],
                    'pending'
                )
            )
            
            # Add player to search cache for future searches
            await self.player_search_service.add_player_to_cache(
                bet_data['player_name'],
                bet_data['team_name'],
                bet_data['league'],
                bet_data['sport']
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error creating player prop bet: {e}")
            return False

class PlayerPropSearchView(discord.ui.View):
    """View for player search with autocomplete."""
    
    def __init__(self, bot, db_manager, league: str, game_id: str, team_name: str):
        super().__init__(timeout=60)
        self.bot = bot
        self.db_manager = db_manager
        self.league = league
        self.game_id = game_id
        self.team_name = team_name
        self.player_search_service = PlayerSearchService(db_manager)
    
    @discord.ui.button(label="Search Players", style=discord.ButtonStyle.primary)
    async def search_players(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Show popular players for this league."""
        try:
            popular_players = await self.player_search_service.get_popular_players(
                self.league, limit=10
            )
            
            if not popular_players:
                await interaction.response.send_message(
                    "No popular players found for this league. Use the modal to search manually.",
                    ephemeral=True
                )
                return
            
            # Create embed with popular players
            embed = discord.Embed(
                title=f"Popular {self.league} Players",
                description="Click a player to create a prop bet",
                color=discord.Color.blue()
            )
            
            for i, player in enumerate(popular_players[:5], 1):
                embed.add_field(
                    name=f"{i}. {player.player_name}",
                    value=f"Team: {player.team_name}\nUsage: {player.usage_count} times",
                    inline=True
                )
            
            await interaction.response.send_message(
                embed=embed,
                ephemeral=True
            )
            
        except Exception as e:
            logger.error(f"Error showing popular players: {e}")
            await interaction.response.send_message(
                "❌ Error loading popular players.",
                ephemeral=True
            )
    
    @discord.ui.button(label="Create Prop Bet", style=discord.ButtonStyle.success)
    async def create_prop_bet(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Open the enhanced player prop modal."""
        try:
            modal = EnhancedPlayerPropModal(
                self.bot, self.db_manager, self.league, self.game_id, self.team_name
            )
            await interaction.response.send_modal(modal)
            
        except Exception as e:
            logger.error(f"Error opening player prop modal: {e}")
            await interaction.response.send_message(
                "❌ Error opening bet modal.",
                ephemeral=True
            )

async def setup_enhanced_player_prop(bot, db_manager, league: str, game_id: str, team_name: str):
    """Setup and return the enhanced player prop view."""
    return PlayerPropSearchView(bot, db_manager, league, game_id, team_name) 