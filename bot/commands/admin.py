# betting-bot/commands/admin.py

"""Admin commands for server setup and management."""

import logging
import os
from functools import wraps
from typing import List

import discord
from discord import Interaction, Role, TextChannel, app_commands
from discord.ext import commands  # Import commands for Cog

# Use relative imports (assuming commands/ is sibling to services/, utils/)
try:
    # Services will be accessed via self.bot.<service_name>
    from ..services.admin_service import (  # Explicitly import AdminService type hint if needed
        AdminService,
    )
except ImportError:
    # Fallbacks
    pass


logger = logging.getLogger(__name__)


def require_registered_guild():
    """Decorator to check if the guild is registered with the bot."""

    def decorator(func):
        @wraps(func)
        async def wrapper(self, interaction: Interaction, *args, **kwargs):
            # Check if guild exists in database
            existing_settings = await self.bot.db_manager.fetch_one(
                "SELECT * FROM guild_settings WHERE guild_id = %s", interaction.guild_id
            )

            if not existing_settings:
                await interaction.response.send_message(
                    "❌ This server is not registered with the bot. Please use `/setup` to register first.",
                    ephemeral=True,
                )
                return

            return await func(self, interaction, *args, **kwargs)

        return wrapper

    return decorator


# --- UI Components ---


class ChannelSelect(discord.ui.Select):
    """Select menu for choosing text channels."""

    def __init__(
        self,
        placeholder: str,
        setting_key: str,
        channels: List[TextChannel],
        max_options=25,
    ):
        # Filter out channels that have already been selected for this type
        if (
            setting_key == "embed_channel_1"
            and hasattr(self, "view")
            and hasattr(self.view, "embed_channels")
        ):
            channels = [
                ch for ch in channels if str(ch.id) not in self.view.embed_channels
            ]
        elif (
            setting_key == "command_channel_1"
            and hasattr(self, "view")
            and hasattr(self.view, "command_channels")
        ):
            channels = [
                ch for ch in channels if str(ch.id) not in self.view.command_channels
            ]

        options = [
            discord.SelectOption(
                label=f"#{channel.name}",  # Add # prefix
                value=str(channel.id),
                description=f"ID: {channel.id}",
            )
            for channel in channels[:max_options]  # Limit options
        ]
        if not options:  # Handle case with no channels
            options.append(
                discord.SelectOption(
                    label="No Text Channels Found", value="none", emoji="❌"
                )
            )

        super().__init__(
            placeholder=placeholder,
            options=options,
            min_values=1,
            max_values=1,
            disabled=not options
            or options[0].value == "none",  # Disable if no channels
        )
        self.setting_key = setting_key

    async def callback(self, interaction: discord.Interaction):
        # Ensure the view attribute exists and has settings
        if not hasattr(self.view, "settings"):
            logger.error(
                "Parent view or settings dictionary not found in ChannelSelect."
            )
            await interaction.response.send_message(
                "Error processing selection.", ephemeral=True
            )
            return

        selected_value = self.values[0]
        if selected_value == "none":
            await interaction.response.defer()  # Acknowledge but do nothing else
            return

        # For embed channels, track the selection
        if self.setting_key == "embed_channel_1":
            if selected_value in self.view.embed_channels:
                await interaction.response.send_message(
                    "This channel has already been selected as an embed channel.",
                    ephemeral=True,
                )
                return
            self.view.embed_channels.append(selected_value)
            if "embed_channel_1" not in self.view.settings:
                self.view.settings["embed_channel_1"] = []
            self.view.settings["embed_channel_1"].append(selected_value)
        elif self.setting_key == "command_channel_1":
            if selected_value in self.view.command_channels:
                await interaction.response.send_message(
                    "This channel has already been selected as a command channel.",
                    ephemeral=True,
                )
                return
            self.view.command_channels.append(selected_value)
            if "command_channel_1" not in self.view.settings:
                self.view.settings["command_channel_1"] = []
            self.view.settings["command_channel_1"].append(selected_value)
        else:
            self.view.settings[self.setting_key] = selected_value

        await interaction.response.defer()
        self.view.current_step += 1
        await self.view.process_next_selection(interaction)


class RoleSelect(discord.ui.Select):
    """Select menu for choosing roles."""

    def __init__(
        self, placeholder: str, setting_key: str, roles: List[Role], max_options=25
    ):
        options = [
            discord.SelectOption(
                label=role.name, value=str(role.id), description=f"ID: {role.id}"
            )
            for role in roles[:max_options]  # Limit options
        ]
        if not options:  # Handle case with no roles
            options.append(
                discord.SelectOption(
                    label="No Roles Found (Except @everyone)", value="none", emoji="❌"
                )
            )

        super().__init__(
            placeholder=placeholder,
            options=options,
            min_values=1,
            max_values=1,
            disabled=not options or options[0].value == "none",  # Disable if no roles
        )
        self.setting_key = setting_key

    async def callback(self, interaction: discord.Interaction):
        # Ensure the view attribute exists and has settings
        if not hasattr(self.view, "settings"):
            logger.error("Parent view or settings dictionary not found in RoleSelect.")
            await interaction.response.send_message(
                "Error processing selection.", ephemeral=True
            )
            return

        selected_value = self.values[0]
        if selected_value == "none":
            await interaction.response.defer()  # Acknowledge but do nothing else
            return

        self.view.settings[self.setting_key] = selected_value
        await interaction.response.defer()
        self.view.current_step += 1
        await self.view.process_next_selection(interaction)


class SubscriptionModal(discord.ui.Modal):
    def __init__(self):
        super().__init__(title="Free Tier Information")
        self.add_item(
            discord.ui.TextInput(
                label="Free Tier Details",
                style=discord.TextStyle.paragraph,
                placeholder="Please enjoy our free tier service as long as you like, however your server is limited to 4 active bets at a time, and all premium services will be locked out. For only $19.99 a month, your server can have access to two embed channels, two command channels, an admin channel, unit tracking monthly and yearly, bot avatar masks, custom user avatar masks, a daily report, and custom guild background image for your bet slips. Subscribe today to unlock the full power of the Bet Embed Generator!",
                required=True,
                default="Please enjoy our free tier service as long as you like, however your server is limited to 4 active bets at a time, and all premium services will be locked out. For only $19.99 a month, your server can have access to two embed channels, two command channels, an admin channel, unit tracking monthly and yearly, bot avatar masks, custom user avatar masks, a daily report, and custom guild background image for your bet slips. Subscribe today to unlock the full power of the Bet Embed Generator!",
            )
        )


class SubscriptionView(discord.ui.View):
    def __init__(self, bot: commands.Bot, interaction: discord.Interaction):
        super().__init__(timeout=300)
        self.bot = bot
        self.original_interaction = interaction

    @discord.ui.button(label="Subscribe", style=discord.ButtonStyle.green)
    async def subscribe(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        # TODO: Implement subscription page redirect
        await interaction.response.send_message(
            "Redirecting to subscription page...", ephemeral=True
        )
        self.stop()

    @discord.ui.button(label="Continue with Free Tier", style=discord.ButtonStyle.grey)
    async def continue_free(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await interaction.response.defer()
        view = GuildSettingsView(
            bot=self.bot,
            guild=interaction.guild,
            admin_service=self.bot.admin_service,
            original_interaction=interaction,
            subscription_level="free",
        )
        await view.start_selection()
        self.stop()


class SkipButton(discord.ui.Button):
    """Button to skip the current setup step."""

    def __init__(self):
        super().__init__(
            label="Skip", style=discord.ButtonStyle.secondary, custom_id="skip_step"
        )

    async def callback(self, interaction: discord.Interaction):
        """Handle skip button click."""
        if not hasattr(self.view, "process_next_selection"):
            await interaction.response.send_message(
                "Error: Cannot process skip action.", ephemeral=True
            )
            return

        # Defer the interaction to prevent timeout
        await interaction.response.defer()

        # Store the message for editing
        self.view.message = interaction.message

        # Move to next step
        self.view.current_step += 1
        await self.view.process_next_selection(interaction)


class GuildSettingsView(discord.ui.View):
    """View for guild settings setup"""

    SETUP_STEPS = [
        {
            "name": "Embed Channel",
            "select": ChannelSelect,
            "options": lambda guild: [
                discord.SelectOption(label=ch.name, value=str(ch.id))
                for ch in guild.text_channels
            ],
            "setting_key": "embed_channel_1",
            "max_count": 2,  # Maximum number of embed channels allowed for premium
            "free_count": 1,  # Maximum number of embed channels for free tier
        },
        {
            "name": "Command Channel",
            "select": ChannelSelect,
            "options": lambda guild: [
                discord.SelectOption(label=ch.name, value=str(ch.id))
                for ch in guild.text_channels
            ],
            "setting_key": "command_channel_1",
            "max_count": 2,  # Maximum number of command channels allowed for premium
            "free_count": 1,  # Maximum number of command channels for free tier
        },
        {
            "name": "Admin Channel",
            "select": ChannelSelect,
            "options": lambda guild: [
                discord.SelectOption(label=ch.name, value=str(ch.id))
                for ch in guild.text_channels
            ],
            "setting_key": "admin_channel_1",
            "max_count": 1,  # Only one admin channel allowed
            "free_count": 1,
        },
        {
            "name": "Admin Role",
            "select": RoleSelect,
            "options": lambda guild: [
                discord.SelectOption(label=role.name, value=str(role.id))
                for role in guild.roles
            ],
            "setting_key": "admin_role",
            "max_count": 1,  # Only one admin role allowed
            "free_count": 1,
        },
        {
            "name": "Authorized Role",
            "select": RoleSelect,
            "options": lambda guild: [
                discord.SelectOption(label=role.name, value=str(role.id))
                for role in guild.roles
            ],
            "setting_key": "authorized_role",
            "max_count": 1,  # Only one authorized role allowed
            "free_count": 1,
        },
        {
            "name": "Member Role",
            "select": RoleSelect,
            "options": lambda guild: [
                discord.SelectOption(label=role.name, value=str(role.id))
                for role in guild.roles
            ],
            "setting_key": "member_role",
            "max_count": 1,  # Only one member role allowed
            "free_count": 1,
        },
        {
            "name": "Bot Avatar URL",
            "select": None,  # This will be handled by message input
            "setting_key": "bot_image_mask",
            "is_premium_only": True,
        },
        {
            "name": "Guild Background URL",
            "select": None,  # This will be handled by message input
            "setting_key": "guild_background",
            "is_premium_only": True,
        },
        {
            "name": "Default Parlay Image",
            "select": None,  # This will be handled by message input
            "setting_key": "default_parlay_image",
            "is_premium_only": True,
        },
        {
            "name": "Enable Live Game Updates",
            "select": None,  # Will be handled by a yes/no prompt
            "setting_key": "live_game_updates",
            "is_boolean": True,
        },
        {
            "name": "Units Display Mode",
            "select": None,  # Will be handled by a select menu
            "setting_key": "units_display_mode",
            "is_premium_only": True,
        },
    ]

    def __init__(
        self,
        bot,
        guild,
        admin_service,
        original_interaction,
        subscription_level="initial",
    ):
        super().__init__(timeout=300)
        self.bot = bot
        self.guild = guild
        self.admin_service = admin_service
        self.original_interaction = original_interaction
        self.current_step = 0
        self.settings = {}
        self.subscription_level = subscription_level
        self.embed_channels = []  # Track selected embed channels
        self.command_channels = []  # Track selected command channels
        self.waiting_for_url = False  # Track if we're waiting for a URL input
        self.message = None  # Initialize message attribute

    async def start_selection(self):
        """Start the selection process"""
        # This method is now just a placeholder since we handle the setup in setup_command

    async def process_next_selection(
        self, interaction: discord.Interaction, initial: bool = False
    ):
        if self.current_step >= len(self.SETUP_STEPS):
            await self.finalize_setup(interaction)
            return

        step = self.SETUP_STEPS[self.current_step]
        logger.info(f"Processing setup step {self.current_step}: {step}")

        # Skip premium-only steps for non-premium users
        if step.get("is_premium_only", False) and self.subscription_level != "premium":
            logger.info(
                f"Skipping premium step '{step['name']}' for subscription level '{self.subscription_level}'"
            )
            self.current_step += 1
            await self.process_next_selection(interaction)
            return

        # Handle boolean (yes/no) steps
        if step.get("is_boolean", False):
            view = discord.ui.View(timeout=60)

            async def yes_callback(inner_interaction):
                self.settings[step["setting_key"]] = 1
                self.current_step += 1
                await self.process_next_selection(inner_interaction)

            async def no_callback(inner_interaction):
                self.settings[step["setting_key"]] = 0
                self.current_step += 1
                await self.process_next_selection(inner_interaction)

            yes_btn = discord.ui.Button(label="Yes", style=discord.ButtonStyle.green)
            no_btn = discord.ui.Button(label="No", style=discord.ButtonStyle.red)
            yes_btn.callback = yes_callback
            no_btn.callback = no_callback
            view.add_item(yes_btn)
            view.add_item(no_btn)
            await self.message.edit(
                content=f"Would you like to enable live game update channels?",
                view=view,
            )
            return

        if not interaction.response.is_done():
            await interaction.response.defer()

        select_class = step["select"]
        # Always handle select_class is None: show modal if setting_key is present, otherwise skip
        if select_class is None:
            if step.get("setting_key") not in [None, ""]:

                class InputModal(discord.ui.Modal, title=f"Enter {step['name']}"):
                    user_input = discord.ui.TextInput(label=step["name"], required=True)

                    async def on_submit(self, modal_interaction: discord.Interaction):
                        self.view.settings[step["setting_key"]] = self.user_input.value
                        self.view.current_step += 1
                        await self.view.process_next_selection(modal_interaction)

                modal = InputModal()
                modal.view = self
                await interaction.response.send_modal(modal)
                return
            # Otherwise, always skip this step
            self.current_step += 1
            await self.process_next_selection(interaction)
            return

        if select_class == ChannelSelect:
            items = interaction.guild.text_channels
        else:
            items = interaction.guild.roles

        if not items:
            await self.message.edit(
                content=f"No {step['name'].lower()} found. Please create one and try again.",
                view=None,
            )
            return

        # Remove all items from the current view and add the new select and skip button
        self.clear_items()
        if select_class == ChannelSelect:
            select = select_class(
                placeholder=f"Select {step['name']}",
                setting_key=step["setting_key"],
                channels=items,
            )
        else:
            select = select_class(
                placeholder=f"Select {step['name']}",
                setting_key=step["setting_key"],
                roles=items,
            )
        self.add_item(select)
        skip_button = SkipButton()
        self.add_item(skip_button)
        await self.message.edit(
            content=f"Please select a {step['name'].lower()}:", view=self
        )

        # Fallback: if for any reason the step is not handled, always advance
        # (This should be unreachable, but ensures no infinite loop)
        if not self.children:
            logger.warning(f"Step {self.current_step} was not handled, skipping.")
            self.current_step += 1
            await self.process_next_selection(interaction)
            return

    async def finalize_setup(self, interaction: discord.Interaction):
        """Saves the collected settings to the database."""
        try:
            # Convert selected IDs from string to int before saving
            final_settings = {}
            for k, v in self.settings.items():
                if v and v != "none":
                    if k in ["embed_channel_1", "command_channel_1"]:
                        # Handle lists for channels
                        if isinstance(v, list):
                            final_settings[k] = [int(x) for x in v]
                        else:
                            final_settings[k] = [int(v)]
                    elif k in [
                        "admin_channel_1",
                        "admin_role",
                        "authorized_role",
                        "member_role",
                    ]:
                        # Handle single values for roles and admin channel
                        final_settings[k] = int(v)
                    else:
                        final_settings[k] = v
            # Ensure live_game_updates is set (default to 0 if not present)
            if "live_game_updates" not in final_settings:
                final_settings["live_game_updates"] = 0

            # Save to database
            await self.admin_service.setup_guild(self.guild.id, final_settings)

            # Update the message
            await self.message.edit(
                content="✅ Guild setup completed successfully!", view=None
            )

        except Exception as e:
            logger.exception(f"Error saving guild settings: {e}")
            await self.message.edit(
                content="❌ An error occurred while saving settings.", view=None
            )
        finally:
            self.stop()


class VoiceChannelSelect(discord.ui.Select):
    def __init__(
        self, parent_view: GuildSettingsView, channels: List[discord.VoiceChannel]
    ):
        self.parent_view = parent_view
        options = [
            discord.SelectOption(
                label=channel.name,
                value=str(channel.id),
                description=f"Channel ID: {channel.id}",
            )
            for channel in channels[:25]
        ]
        super().__init__(
            placeholder="Select voice channel...",
            options=options,
            min_values=1,
            max_values=1,
        )

    async def callback(self, interaction: discord.Interaction):
        self.parent_view.settings[self.custom_id] = self.values[0]
        self.disabled = True
        await interaction.response.defer()
        self.parent_view.current_step += 1
        await self.parent_view.process_next_selection(interaction)


# --- Cog Definition ---
class AdminCog(commands.Cog):
    def __init__(self, bot: commands.Bot, admin_service):
        self.bot = bot
        self.admin_service = admin_service
        self.active_views = {}  # Track active views by user ID

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Handle URL input messages"""
        if message.author.bot:
            return

        # Check if this user has an active view waiting for URL input
        if message.author.id in self.active_views:
            view = self.active_views[message.author.id]
            if view.waiting_for_url:
                try:
                    await view.handle_url_input(message)
                    # If we're done with all URL inputs, remove the view
                    if not view.waiting_for_url:
                        del self.active_views[message.author.id]
                except Exception as e:
                    logger.error(f"Error handling URL input: {str(e)}")
                    await message.channel.send(
                        "An error occurred while processing your input. Please try again."
                    )
                    del self.active_views[message.author.id]

    @app_commands.command(name="setup", description="Run the interactive server setup.")
    @app_commands.checks.has_permissions(administrator=True)
    async def setup_command(self, interaction: Interaction):
        """Starts the interactive server setup process."""
        logger.info(
            f"Setup command initiated by {interaction.user} in guild {interaction.guild_id}"
        )
        try:
            # Check if guild exists in database
            existing_settings = await self.bot.db_manager.fetch_one(
                "SELECT * FROM guild_settings WHERE guild_id = %s", interaction.guild_id
            )

            # If guild doesn't exist, create it with default values
            if not existing_settings:
                await self.bot.db_manager.execute(
                    """
                    INSERT INTO guild_settings
                    (guild_id, is_paid, subscription_level)
                    VALUES (%s, 0, 'initial')
                    """,
                    interaction.guild_id,
                )
                subscription_level = "initial"
            else:
                # Determine subscription level based on is_paid field
                is_paid = existing_settings.get("is_paid", 0)
                subscription_level = "premium" if is_paid else "initial"

                logger.info(
                    f"Guild {interaction.guild_id} - is_paid: {is_paid}, subscription_level: {subscription_level}"
                )

                # Update subscription_level in database if it doesn't match is_paid
                if is_paid and existing_settings.get("subscription_level") != "premium":
                    await self.bot.db_manager.execute(
                        "UPDATE guild_settings SET subscription_level = 'premium' WHERE guild_id = %s",
                        interaction.guild_id,
                    )
                    logger.info(
                        f"Updated subscription_level to 'premium' for guild {interaction.guild_id}"
                    )

            # --- Create static/guilds/{guild_id}/users directory ---
            try:
                base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
                guild_dir = os.path.join(
                    base_dir, "static", "guilds", str(interaction.guild_id)
                )
                users_dir = os.path.join(guild_dir, "users")
                os.makedirs(users_dir, exist_ok=True)
                logger.info(f"Created guild users directory: {users_dir}")
            except Exception as e:
                logger.error(f"Failed to create guild users directory: {e}")

            # Create and start the setup view
            view = GuildSettingsView(
                self.bot,
                interaction.guild,
                self.admin_service,
                interaction,
                subscription_level=subscription_level,
            )

            # Send initial message and store it
            await interaction.response.send_message(
                "Starting server setup...", ephemeral=True
            )
            view.message = await interaction.original_response()

            # Process first step
            await view.process_next_selection(interaction, initial=True)

            # After setup completes, trigger /sync in the background
            sync_cog = self.bot.get_cog("SyncCog")
            if sync_cog:
                self.bot.loop.create_task(
                    sync_cog.sync_command.callback(sync_cog, interaction)
                )
            else:
                logger.warning("SyncCog not found; cannot trigger /sync after setup.")

        except Exception as e:
            logger.exception(f"Error initiating setup command: {e}")
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    "❌ An error occurred while starting the setup.", ephemeral=True
                )
            else:
                await interaction.followup.send(
                    "❌ An error occurred while starting the setup.", ephemeral=True
                )

    @app_commands.command(
        name="setchannel", description="Set or remove voice channels for stat tracking."
    )
    @app_commands.checks.has_permissions(administrator=True)
    @require_registered_guild()
    async def setchannel_command(self, interaction: Interaction):
        """Allows admins to set or remove stat tracking voice channels."""
        logger.info(
            f"SetChannel command initiated by {interaction.user} in guild {interaction.guild_id}"
        )
        try:
            # Access services via self.bot
            if not hasattr(self.bot, "admin_service") or not hasattr(
                self.bot, "db_manager"
            ):
                logger.error(
                    "Required services (AdminService, DatabaseManager) not found on bot instance."
                )
                await interaction.response.send_message(
                    "Bot is not properly configured.", ephemeral=True
                )
                return

            from .views.admin_action_view import AdminActionView

            view = AdminActionView(self.bot, interaction)
            await interaction.response.send_message(
                "Select the channel action you want to perform:",
                view=view,
                ephemeral=True,
            )

        except Exception as e:
            logger.exception(
                f"Error initiating setchannel command for {interaction.user}: {e}"
            )
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    "❌ An error occurred.", ephemeral=True
                )
            # Cannot easily followup here if initial response failed

    @app_commands.command(
        name="subscribe",
        description="Get the link to subscribe your server to premium features.",
    )
    async def subscribe_command(self, interaction: Interaction):
        """Sends the subscription webpage link for premium services."""
        subscription_url = "https://betting-server-manager.us/subscribe"
        await interaction.response.send_message(
            f"To subscribe your server to premium features, visit: {subscription_url}",
            ephemeral=True,
        )

    # Cog specific error handler
    async def cog_app_command_error(
        self, interaction: Interaction, error: app_commands.AppCommandError
    ):
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message(
                "You need administrator permissions to use this command.",
                ephemeral=True,
            )
        else:
            logger.error(f"Error in AdminCog command: {error}", exc_info=True)
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    "An internal error occurred with the admin command.", ephemeral=True
                )
            else:
                # May not be possible to followup reliably
                pass

    async def update_images_callback(
        self, interaction: discord.Interaction, existing_settings=None
    ):
        """Handle update images button click"""
        try:
            # Create a new view for image URL requests
            view = GuildSettingsView(
                bot=self.bot,
                guild=interaction.guild,
                admin_service=self.admin_service,
                original_interaction=interaction,
                subscription_level="premium",
            )
            if existing_settings:
                view.settings = dict(existing_settings)

            # Find the first image URL step
            for i, step in enumerate(view.SETUP_STEPS):
                if step.get("is_premium_only", False) and step["select"] is None:
                    view.current_step = i
                    break

            # Send initial message asking for URL
            await interaction.response.send_message(
                f"Please upload an image for {view.SETUP_STEPS[view.current_step]['name'].lower()} or type 'skip' to skip this step:",
                ephemeral=True,
            )
            view.waiting_for_url = True

            # Store the view for this user
            self.active_views[interaction.user.id] = view

        except Exception as e:
            logger.error(f"Error in update images callback: {str(e)}")
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    "An error occurred while updating images. Please try again.",
                    ephemeral=True,
                )
            else:
                await interaction.followup.send(
                    "An error occurred while updating images. Please try again.",
                    ephemeral=True,
                )

    async def full_setup_callback(self, interaction: discord.Interaction):
        """Handle full setup button click"""
        try:
            await interaction.response.defer()
            view = GuildSettingsView(
                bot=self.bot,
                guild=interaction.guild,
                admin_service=self.admin_service,
                original_interaction=interaction,
                subscription_level="premium",
            )
            await interaction.followup.send(
                "Starting full server setup...", view=view, ephemeral=True
            )
            await view.start_selection()
        except Exception as e:
            logger.error(f"Error in full setup callback: {str(e)}")
            if not interaction.response.is_done():
                await interaction.followup.send(
                    "An error occurred during setup. Please try again.", ephemeral=True
                )
            else:
                await interaction.followup.send(
                    "An error occurred during setup. Please try again.", ephemeral=True
                )


# The setup function for the extension
async def setup(bot: commands.Bot):
    await bot.add_cog(AdminCog(bot, bot.admin_service))
    logger.info("AdminCog loaded")
