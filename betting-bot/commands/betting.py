# REV 1.0.0 - Enhanced betting command with improved workflow selection and error handling
# betting-bot/commands/betting.py

"""Main betting command for placing straight or parlay bets."""

import discord
from discord import app_commands, ButtonStyle, Interaction, SelectOption
from discord.ext import commands
from discord.ui import View, Select, Button
import logging
from typing import Optional, Union

# Import from same directory
from .straight_betting import StraightBetWorkflowView
from .parlay_betting import ParlayBetWorkflowView
from config.leagues import LEAGUE_IDS 
from utils.player_prop_image_generator import PlayerPropImageGenerator
from utils.game_line_image_generator import generate_player_prop_bet_image as generate_game_line_image

logger = logging.getLogger(__name__)

# --- Authorization Check Function ---
async def is_allowed_command_channel(interaction: Interaction) -> bool:
    """Checks if the command is used in a configured command channel."""
    if not interaction.guild_id:
        if not interaction.response.is_done():
            await interaction.response.send_message("This command must be used in a server.", ephemeral=True)
        else:
            # This case is less likely for a primary command check but good for robustness
            try: await interaction.followup.send("This command must be used in a server.", ephemeral=True)
            except discord.HTTPException: pass # Ignore if followup fails (e.g. original interaction deleted)
        return False

    if not hasattr(interaction.client, 'db_manager') or not interaction.client.db_manager: # type: ignore
        logger.error("Database manager not found on bot client for command channel check.")
        msg = "Bot configuration error (DBM). Cannot verify command channel."
        if not interaction.response.is_done(): await interaction.response.send_message(msg, ephemeral=True)
        else: 
            try: await interaction.followup.send(msg, ephemeral=True)
            except discord.HTTPException: pass
        return False
    
    db_manager = interaction.client.db_manager # type: ignore

    settings = await db_manager.fetch_one(
        "SELECT command_channel_1, command_channel_2 FROM guild_settings WHERE guild_id = %s",
        (interaction.guild_id,)
    )

    if not settings:
        msg = "Command channels are not configured for this server. Please ask an admin to set them up using `/setup` or a relevant admin command."
        if not interaction.response.is_done(): await interaction.response.send_message(msg, ephemeral=True)
        else: 
            try: await interaction.followup.send(msg, ephemeral=True)
            except discord.HTTPException: pass
        return False

    command_channel_1_id = settings.get('command_channel_1')
    command_channel_2_id = settings.get('command_channel_2')

    allowed_channel_ids = []
    if command_channel_1_id:
        try: allowed_channel_ids.append(int(command_channel_1_id))
        except (ValueError, TypeError): logger.error(f"Invalid command_channel_1 ID in DB for guild {interaction.guild_id}: {command_channel_1_id}")
    if command_channel_2_id:
        try: allowed_channel_ids.append(int(command_channel_2_id))
        except (ValueError, TypeError): logger.error(f"Invalid command_channel_2 ID in DB for guild {interaction.guild_id}: {command_channel_2_id}")

    if not allowed_channel_ids:
        msg = "No command channels are configured for betting. Please ask an admin to set them up."
        if not interaction.response.is_done(): await interaction.response.send_message(msg, ephemeral=True)
        else: 
            try: await interaction.followup.send(msg, ephemeral=True)
            except discord.HTTPException: pass
        return False

    if interaction.channel_id not in allowed_channel_ids:
        channel_mentions = []
        guild = interaction.guild # Cache guild attribute
        if guild:
            for ch_id in allowed_channel_ids:
                channel = guild.get_channel(ch_id)
                if channel: channel_mentions.append(channel.mention)
                else: channel_mentions.append(f"`Channel ID: {ch_id}` (not found/accessible)")
        else: # Should not happen for a guild command
             channel_mentions = [f"`Channel ID: {ch_id}`" for ch_id in allowed_channel_ids]

        
        msg = f"This command can only be used in the designated command channel(s): {', '.join(channel_mentions) if channel_mentions else 'None Configured'}"
        if not interaction.response.is_done(): await interaction.response.send_message(msg, ephemeral=True)
        else: 
            try: await interaction.followup.send(msg, ephemeral=True)
            except discord.HTTPException: pass
        return False
    
    return True

# --- UI Component Classes ---
class BetTypeSelect(Select):
    def __init__(self, parent_view: 'BetTypeView'): # Added type hint for parent_view
        self.parent_view = parent_view
        options = [
            SelectOption(
                label="Straight",
                value="straight",
                description="Moneyline, over/under, or player prop",
            ),
            SelectOption(
                label="Parlay",
                value="parlay",
                description="Combine multiple bets",
            ),
        ]
        super().__init__(
            placeholder="Select Bet Type...",
            options=options,
            min_values=1,
            max_values=1,
        )

    async def callback(self, interaction: Interaction):
        logger.debug(
            f"Bet Type selected by {interaction.user} (ID: {interaction.user.id}): {self.values[0]} in guild {interaction.guild_id}"
        )
        self.disabled = True
        for item in self.parent_view.children:
            item.disabled = True # type: ignore
        try:
            await interaction.response.edit_message(view=self.parent_view)
            logger.debug(f"Starting bet workflow for type: {self.values[0]}")
            await self.parent_view.start_bet_workflow(
                interaction, self.values[0]
            )
        except Exception as e:
            logger.error(
                f"Error processing bet type selection for user {interaction.user}: {e}",
                exc_info=True,
            )
            try:
                await interaction.followup.send(
                    f"❌ Failed to process bet type selection: {str(e)}",
                    ephemeral=True,
                )
            except discord.HTTPException:
                 logger.error("Failed to send followup after bet type selection error.")


class CancelButton(Button):
    def __init__(self, parent_view: 'BetTypeView'): # Added type hint
        super().__init__(
            style=ButtonStyle.red,
            label="Cancel",
            custom_id=f"cancel_bet_type_{parent_view.original_interaction.id}",
        )
        self.parent_view = parent_view

    async def callback(self, interaction: Interaction):
        logger.debug(
            f"Cancel button clicked by {interaction.user} (ID: {interaction.user.id}) in bet type selection"
        )
        self.disabled = True
        for item in self.parent_view.children:
            item.disabled = True # type: ignore
        try:
            await interaction.response.edit_message(
                content="Bet workflow cancelled.", view=None
            )
        except Exception as e:
            logger.error(
                f"Error cancelling bet workflow for user {interaction.user}: {e}",
                exc_info=True,
            )
        self.parent_view.stop()


class BetTypeView(View):
    def __init__(self, interaction: Interaction, bot: commands.Bot):
        super().__init__(timeout=600)
        self.original_interaction = interaction 
        self.bot = bot
        self.message: Optional[
            Union[discord.WebhookMessage, discord.InteractionMessage]
        ] = None
        self.add_item(BetTypeSelect(self))
        self.add_item(CancelButton(self))
        logger.debug(
            f"BetTypeView initialized for user {interaction.user} (ID: {interaction.user.id})"
        )

    async def interaction_check(self, interaction: Interaction) -> bool:
        if interaction.user.id != self.original_interaction.user.id:
            logger.debug(
                f"Unauthorized interaction attempt by {interaction.user} (ID: {interaction.user.id})"
            )
            await interaction.response.send_message(
                "You cannot interact with this bet placement.", ephemeral=True
            )
            return False
        logger.debug(
            f"Interaction check passed for user {interaction.user} (ID: {interaction.user.id})"
        )
        return True

    async def start_bet_workflow(
        self, interaction_from_select: Interaction, bet_type: str
    ):
        logger.debug(
            f"Starting {bet_type} bet workflow for user {interaction_from_select.user} (ID: {interaction_from_select.user.id})"
        )
        try:
            if bet_type == "straight":
                logger.debug("Initializing StraightBetWorkflowView")
                view = StraightBetWorkflowView(
                    self.original_interaction, 
                    self.bot,
                    message_to_control=self.message  # Ensure message context is passed
                )
                if not view.message: 
                    logger.error("StraightBetWorkflowView initiated without a message to control.")
                    await interaction_from_select.followup.send("Error: Could not initiate straight bet workflow (message context).", ephemeral=True)
                    self.stop()
                    return
                await view.start_flow(interaction_from_select) # Pass the component interaction
            elif bet_type == "parlay":
                logger.debug("Initializing ParlayBetWorkflowView")
                view = ParlayBetWorkflowView( 
                    self.original_interaction, 
                    self.bot
                    # ParlayBetWorkflowView's start_flow will handle sending its own initial message
                    # using self.original_interaction (the /bet command interaction)
                )
                await view.start_flow() # Parlay's start_flow doesn't need interaction_from_select here
            elif bet_type == "player_prop":
                logger.debug("Initializing PlayerPropBetWorkflowView")
                view = PlayerPropBetWorkflowView(
                    self.original_interaction,
                    self.bot
                )
                await view.start_flow(interaction_from_select)

            logger.debug(f"{bet_type} bet workflow started successfully")
        except Exception as e:
            logger.error(
                f"Failed to start {bet_type} bet workflow for user {interaction_from_select.user}: {e}",
                exc_info=True,
            )
            try:
                await interaction_from_select.followup.send(
                    f"❌ Failed to start {bet_type} bet workflow: {str(e)}. Please try again.",
                    ephemeral=True,
                )
            except discord.HTTPException:
                logger.error(f"Failed to send followup for {bet_type} workflow start error.")
        finally:
            self.stop()


class PlayerPropBetWorkflowView(View):
    def __init__(self, interaction: Interaction, bot: commands.Bot):
        super().__init__(timeout=600)
        self.original_interaction = interaction
        self.bot = bot
        self.message: Optional[Union[discord.WebhookMessage, discord.InteractionMessage]] = None
        logger.debug(f"PlayerPropBetWorkflowView initialized for user {interaction.user} (ID: {interaction.user.id})")

    async def start_flow(self, interaction: Interaction):
        try:
            # Example data for player prop bet
            player_name = "John Doe"
            player_picture_path = "betting-bot/assets/player_pictures/john_doe.png"
            team_name = "Team A"
            team_logo_path = "betting-bot/assets/logos/team_a_logo.png"
            line = "Over 20.5 Points"
            units = "5"
            output_path = "/workspaces/DBSBM/generated_player_prop_bet.png"

            # Generate the player prop bet image
            PlayerPropImageGenerator().generate_player_prop_bet_image(player_name, player_picture_path, team_name, team_logo_path, line, units, output_path)
            logger.info(f"Player prop bet image generated and saved to {output_path}")

            # Send the image to the user
            await interaction.response.send_message(
                content="Player Prop Bet Slip:",
                file=discord.File(output_path),
                ephemeral=True
            )
        except Exception as e:
            logger.error(f"Error in PlayerPropBetWorkflowView: {e}", exc_info=True)
            await interaction.response.send_message(
                f"❌ Failed to generate player prop bet slip: {str(e)}",
                ephemeral=True
            )

@app_commands.command(name="bet", description="Place a bet (straight or parlay).")
async def bet(interaction: Interaction):
    logger.info(f"/bet command invoked by {interaction.user} (ID: {interaction.user.id})")
    try:
        view = BetTypeView(interaction, interaction.client)
        logger.debug("BetTypeView initialized successfully.")
        # Send the initial message
        await interaction.response.send_message(
            "Select the type of bet you want to place:",
            view=view,
            ephemeral=True
        )
        # Retrieve and assign the message object
        view.message = await interaction.original_response()
        logger.info("/bet command response sent successfully.")
    except Exception as e:
        logger.error(f"Error in /bet command: {e}", exc_info=True)
        await interaction.response.send_message(
            "❌ An error occurred while processing your request.", ephemeral=True
        )

# Add the command to the bot's command tree
async def setup(bot: commands.Bot):
    logger.info("Setting up betting commands...")
    try:
        bot.tree.add_command(bet)
        logger.debug("/bet command added to command tree.")
        logger.info("Syncing commands globally...")
        synced = await bot.tree.sync()
        logger.info(f"Commands synced successfully: {[cmd.name for cmd in synced]}")
    except Exception as e:
        logger.error(f"Error during command setup or syncing: {e}", exc_info=True)
