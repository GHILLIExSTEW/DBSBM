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
    from services.admin_service import (  # Explicitly import AdminService type hint if needed
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
                "SELECT * FROM guild_settings WHERE guild_id = $1", interaction.guild_id
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

        # Defer the interaction to prevent timeout
        if not interaction.response.is_done():
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
            # Disable if no roles
            disabled=not options or options[0].value == "none",
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

        # Defer the interaction to prevent timeout
        if not interaction.response.is_done():
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
        # Subscription page redirect implementation
        embed = discord.Embed(
            title="🔗 Premium Subscription",
            description="Click the link below to subscribe to premium features:",
            color=0x00FF00,
        )
        embed.add_field(
            name="Premium Features",
            value="• Multiple embed channels\n• Advanced analytics\n• Priority support\n• Custom branding",
            inline=False,
        )
        embed.add_field(
            name="Subscription Link",
            value="[Subscribe to Premium](https://your-subscription-page.com)",
            inline=False,
        )

        await interaction.response.send_message(embed=embed, ephemeral=True)
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
        try:
            # Store the message for editing
            self.view.message = interaction.message
            # Move to next step
            self.view.current_step += 1

            # Defer the interaction to prevent timeout
            if not interaction.response.is_done():
                await interaction.response.defer()

            await self.view.process_next_selection(interaction)
        except Exception as e:
            import logging

            logging.exception(f"Skip button failed: {e}")
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    f"An error occurred while skipping: {e}", ephemeral=True
                )
            else:
                await interaction.followup.send(
                    f"An error occurred while skipping: {e}", ephemeral=True
                )


class GuildSettingsView(discord.ui.View):
    """View for guild settings setup"""

    SETUP_STEPS = [
        # Dynamic channel selection steps (handled in process_next_selection)
        {
            "name": "Embed Channels",
            "select": ChannelSelect,
            "setting_key": "embed_channels",
            "description": "Select channels for betting embeds",
            "dynamic_channel_type": "embed",
        },
        {
            "name": "Command Channels",
            "select": ChannelSelect,
            "setting_key": "command_channels",
            "description": "Select channels for bot commands",
            "dynamic_channel_type": "command",
        },
        {
            "name": "Admin Channels",
            "select": ChannelSelect,
            "setting_key": "admin_channels",
            "description": "Select channels for admin commands",
            "dynamic_channel_type": "admin",
        },
        {
            "name": "Main Chat Channel",
            "select": ChannelSelect,
            "options": lambda guild: [
                discord.SelectOption(label=ch.name, value=str(ch.id))
                for ch in guild.text_channels
            ],
            "setting_key": "main_chat_channel_id",
            "max_count": 1,
            "free_count": 1,
            "description": "Channel for achievement notifications and community updates",
        },
        {
            "name": "Admin Role",
            "select": RoleSelect,
            "options": lambda guild: [
                discord.SelectOption(label=role.name, value=str(role.id))
                for role in guild.roles
            ],
            "setting_key": "admin_role",
            "max_count": 1,
            "free_count": 1,
            "description": "Role for admin permissions",
        },
        {
            "name": "Authorized Role",
            "select": RoleSelect,
            "options": lambda guild: [
                discord.SelectOption(label=role.name, value=str(role.id))
                for role in guild.roles
            ],
            "setting_key": "authorized_role",
            "max_count": 1,
            "free_count": 1,
            "description": "Role for authorized users",
        },
        {
            "name": "Member Role",
            "select": RoleSelect,
            "options": lambda guild: [
                discord.SelectOption(label=role.name, value=str(role.id))
                for role in guild.roles
            ],
            "setting_key": "member_role",
            "max_count": 1,
            "free_count": 1,
            "description": "Role tagged in official posts",
        },
        {
            "name": "Min Units",
            "select": None,
            "setting_key": "min_units",
            "is_number": True,
            "default": 0.50,
            "description": "Minimum units allowed for bets",
        },
        {
            "name": "Max Units",
            "select": None,
            "setting_key": "max_units",
            "is_number": True,
            "default": 3.00,
            "description": "Maximum units allowed for bets",
        },
        {
            "name": "Embed Color",
            "select": None,
            "setting_key": "embed_color",
            "default": "#00FF00",
            "description": "Default color for embeds (hex format)",
        },
        {
            "name": "Timezone",
            "select": None,
            "setting_key": "timezone",
            "default": "UTC",
            "description": "Timezone for date/time displays",
        },
        # Premium Features
        {
            "name": "Premium: Enable Live Game Updates",
            "select": None,
            "setting_key": "live_game_updates",
            "is_boolean": True,
            "is_premium_only": True,
            "description": "Enable 15-second live game updates (Premium feature)",
        },
        {
            "name": "Premium: Additional Embed Channel",
            "select": ChannelSelect,
            "options": lambda guild: [
                discord.SelectOption(label=ch.name, value=str(ch.id))
                for ch in guild.text_channels
            ],
            "setting_key": "embed_channel_2",
            "max_count": 2,  # Premium gets 2 embed channels
            "is_premium_only": True,
            "description": "Second embed channel (Premium feature)",
        },
        {
            "name": "Premium: Additional Command Channel",
            "select": ChannelSelect,
            "options": lambda guild: [
                discord.SelectOption(label=ch.name, value=str(ch.id))
                for ch in guild.text_channels
            ],
            "setting_key": "command_channel_2",
            "max_count": 2,  # Premium gets 2 command channels
            "is_premium_only": True,
            "description": "Second command channel (Premium feature)",
        },
        {
            "name": "Premium: Bot Avatar URL",
            "select": None,
            "setting_key": "bot_image_mask",
            "is_premium_only": True,
            "description": "Custom bot avatar (Premium feature)",
        },
        {
            "name": "Premium: Guild Background URL",
            "select": None,
            "setting_key": "guild_background",
            "is_premium_only": True,
            "description": "Custom guild background (Premium feature)",
        },
        {
            "name": "Premium: Default Parlay Image",
            "select": None,
            "setting_key": "default_parlay_image",
            "is_premium_only": True,
            "description": "Custom parlay image (Premium feature)",
        },
        {
            "name": "Premium: Units Display Mode",
            "select": None,
            "setting_key": "units_display_mode",
            "is_premium_only": True,
            "default": "auto",
            "description": "Units display mode (Premium feature)",
        },
        # Platinum Features
        {
            "name": "Platinum: Embed Channel 3",
            "select": ChannelSelect,
            "options": lambda guild: [
                discord.SelectOption(label=ch.name, value=str(ch.id))
                for ch in guild.text_channels
            ],
            "setting_key": "embed_channel_3",
            "max_count": 5,  # Platinum gets up to 5 embed channels
            "is_platinum_only": True,
            "description": "Third embed channel (Platinum feature)",
        },
        {
            "name": "Platinum: Embed Channel 4",
            "select": ChannelSelect,
            "options": lambda guild: [
                discord.SelectOption(label=ch.name, value=str(ch.id))
                for ch in guild.text_channels
            ],
            "setting_key": "embed_channel_4",
            "max_count": 5,
            "is_platinum_only": True,
            "description": "Fourth embed channel (Platinum feature)",
        },
        {
            "name": "Platinum: Embed Channel 5",
            "select": ChannelSelect,
            "options": lambda guild: [
                discord.SelectOption(label=ch.name, value=str(ch.id))
                for ch in guild.text_channels
            ],
            "setting_key": "embed_channel_5",
            "max_count": 5,
            "is_platinum_only": True,
            "description": "Fifth embed channel (Platinum feature)",
        },
        {
            "name": "Platinum: Command Channel 3",
            "select": ChannelSelect,
            "options": lambda guild: [
                discord.SelectOption(label=ch.name, value=str(ch.id))
                for ch in guild.text_channels
            ],
            "setting_key": "command_channel_3",
            "max_count": 5,  # Platinum gets up to 5 command channels
            "is_platinum_only": True,
            "description": "Third command channel (Platinum feature)",
        },
        {
            "name": "Platinum: Command Channel 4",
            "select": ChannelSelect,
            "options": lambda guild: [
                discord.SelectOption(label=ch.name, value=str(ch.id))
                for ch in guild.text_channels
            ],
            "setting_key": "command_channel_4",
            "max_count": 5,
            "is_platinum_only": True,
            "description": "Fourth command channel (Platinum feature)",
        },
        {
            "name": "Platinum: Command Channel 5",
            "select": ChannelSelect,
            "options": lambda guild: [
                discord.SelectOption(label=ch.name, value=str(ch.id))
                for ch in guild.text_channels
            ],
            "setting_key": "command_channel_5",
            "max_count": 5,
            "is_platinum_only": True,
            "description": "Fifth command channel (Platinum feature)",
        },
        {
            "name": "Platinum: Admin Channel 2",
            "select": ChannelSelect,
            "options": lambda guild: [
                discord.SelectOption(label=ch.name, value=str(ch.id))
                for ch in guild.text_channels
            ],
            "setting_key": "admin_channel_2",
            "max_count": 5,  # Platinum gets up to 5 admin channels
            "is_platinum_only": True,
            "description": "Second admin channel (Platinum feature)",
        },
        {
            "name": "Platinum: Admin Channel 3",
            "select": ChannelSelect,
            "options": lambda guild: [
                discord.SelectOption(label=ch.name, value=str(ch.id))
                for ch in guild.text_channels
            ],
            "setting_key": "admin_channel_3",
            "max_count": 5,
            "is_platinum_only": True,
            "description": "Third admin channel (Platinum feature)",
        },
        {
            "name": "Platinum: Admin Channel 4",
            "select": ChannelSelect,
            "options": lambda guild: [
                discord.SelectOption(label=ch.name, value=str(ch.id))
                for ch in guild.text_channels
            ],
            "setting_key": "admin_channel_4",
            "max_count": 5,
            "is_platinum_only": True,
            "description": "Fourth admin channel (Platinum feature)",
        },
        {
            "name": "Platinum: Admin Channel 5",
            "select": ChannelSelect,
            "options": lambda guild: [
                discord.SelectOption(label=ch.name, value=str(ch.id))
                for ch in guild.text_channels
            ],
            "setting_key": "admin_channel_5",
            "max_count": 5,
            "is_platinum_only": True,
            "description": "Fifth admin channel (Platinum feature)",
        },
        {
            "name": "Platinum: Webhook URL",
            "select": None,
            "setting_key": "platinum_webhook_url",
            "is_platinum_only": True,
            "description": "Discord webhook URL for notifications (Platinum feature)",
        },
        {
            "name": "Platinum: Alert Channel",
            "select": ChannelSelect,
            "options": lambda guild: [
                discord.SelectOption(label=ch.name, value=str(ch.id))
                for ch in guild.text_channels
            ],
            "setting_key": "platinum_alert_channel_id",
            "max_count": 1,
            "is_platinum_only": True,
            "description": "Channel for Platinum alerts (Platinum feature)",
        },
        {
            "name": "Platinum: API Channel",
            "select": ChannelSelect,
            "options": lambda guild: [
                discord.SelectOption(label=ch.name, value=str(ch.id))
                for ch in guild.text_channels
            ],
            "setting_key": "platinum_api_channel_id",
            "max_count": 1,
            "is_platinum_only": True,
            "description": "Channel for API features (Platinum feature)",
        },
        {
            "name": "Platinum: Analytics Channel",
            "select": ChannelSelect,
            "options": lambda guild: [
                discord.SelectOption(label=ch.name, value=str(ch.id))
                for ch in guild.text_channels
            ],
            "setting_key": "platinum_analytics_channel_id",
            "max_count": 1,
            "is_platinum_only": True,
            "description": "Channel for analytics (Platinum feature)",
        },
        {
            "name": "Platinum: Export Channel",
            "select": ChannelSelect,
            "options": lambda guild: [
                discord.SelectOption(label=ch.name, value=str(ch.id))
                for ch in guild.text_channels
            ],
            "setting_key": "platinum_export_channel_id",
            "max_count": 1,
            "is_platinum_only": True,
            "description": "Channel for data exports (Platinum feature)",
        },
        {
            "name": "Platinum: Parlay Embed Channel",
            "select": ChannelSelect,
            "options": lambda guild: [
                discord.SelectOption(label=ch.name, value=str(ch.id))
                for ch in guild.text_channels
            ],
            "setting_key": "parlay_embed_channel_id",
            "max_count": 1,
            "is_platinum_only": True,
            "description": "Dedicated parlay embed channel (Platinum feature)",
        },
        {
            "name": "Platinum: Player Prop Embed Channel",
            "select": ChannelSelect,
            "options": lambda guild: [
                discord.SelectOption(label=ch.name, value=str(ch.id))
                for ch in guild.text_channels
            ],
            "setting_key": "player_prop_embed_channel_id",
            "max_count": 1,
            "is_platinum_only": True,
            "description": "Dedicated player prop embed channel (Platinum feature)",
        },
        {
            "name": "Platinum: Default Parlay Thumbnail",
            "select": None,
            "setting_key": "default_parlay_thumbnail",
            "is_platinum_only": True,
            "description": "Custom parlay thumbnail (Platinum feature)",
        },
    ]

    def __init__(
        self,
        bot,
        guild,
        admin_service,
        original_interaction,
        subscription_level="free",
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

        # Filter setup steps based on subscription level
        self.filtered_steps = self._filter_steps_by_subscription()
        logger.info(
            f"Filtered {len(self.filtered_steps)} steps for subscription level '{subscription_level}'"
        )

    def _filter_steps_by_subscription(self):
        """Filter setup steps based on subscription level."""
        filtered_steps = []

        for step in self.SETUP_STEPS:
            # Skip premium-only steps for free users
            if step.get("is_premium_only", False) and self.subscription_level not in [
                "premium",
                "platinum",
            ]:
                logger.info(
                    f"Skipping premium step '{step['name']}' for subscription level '{self.subscription_level}'"
                )
                continue

            # Skip platinum-only steps for non-platinum users
            if (
                step.get("is_platinum_only", False)
                and self.subscription_level != "platinum"
            ):
                logger.info(
                    f"Skipping platinum step '{step['name']}' for subscription level '{self.subscription_level}'"
                )
                continue

            # Skip steps that start with "Platinum:" for non-platinum users (backward compatibility)
            if (
                step.get("name", "").startswith("Platinum:")
                and self.subscription_level != "platinum"
            ):
                logger.info(
                    f"Skipping platinum step '{step['name']}' for subscription level '{self.subscription_level}'"
                )
                continue

            filtered_steps.append(step)

        return filtered_steps

    async def start_selection(self):
        """Start the selection process"""
        # This method is now just a placeholder since we handle the setup in setup_command

    async def process_next_selection(
        self, interaction: discord.Interaction, initial: bool = False
    ):
        if self.current_step >= len(self.filtered_steps):
            await self.finalize_setup(interaction)
            return

        step = self.filtered_steps[self.current_step]
        logger.info(f"Processing setup step {self.current_step}: {step}")

        # Handle dynamic channel steps
        if step.get("dynamic_channel_type"):
            channel_type = step["dynamic_channel_type"]
            # Determine max selectable channels by subscription level
            if self.subscription_level == "platinum":
                max_count = 5
            elif self.subscription_level == "premium":
                max_count = 2
            else:
                max_count = 1

            # Get available channels
            items = interaction.guild.text_channels
            if not items:
                try:
                    await self.message.edit(
                        content=f"No {step['name'].lower()} found. Please create one and try again.",
                        view=None,
                    )
                except Exception as e:
                    logger.error(f"Failed to update message for empty items: {e}")
                    if not interaction.response.is_done():
                        await interaction.response.send_message(
                            f"No {step['name'].lower()} found. Please create one and try again.",
                            ephemeral=True,
                        )
                return

            # Remove all items from the current view and add the new select and skip button
            self.clear_items()
            select = ChannelSelect(
                placeholder=f"Select up to {max_count} {step['name'].lower()}",
                setting_key=step["setting_key"],
                channels=items,
            )
            select.max_values = max_count
            select.min_values = 1
            self.add_item(select)
            skip_button = SkipButton()
            self.add_item(skip_button)

            try:
                await self.message.edit(
                    content=f"Please select up to {max_count} {step['name'].lower()}:", view=self
                )
            except Exception as e:
                logger.error(f"Failed to update message with new view: {e}")
                if not interaction.response.is_done():
                    await interaction.response.send_message(
                        f"Please select up to {max_count} {step['name'].lower()}:",
                        view=self,
                        ephemeral=True,
                    )
                else:
                    await interaction.followup.send(
                        f"Please select up to {max_count} {step['name'].lower()}:",
                        view=self,
                        ephemeral=True,
                    )
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

            try:
                await self.message.edit(
                    content=f"Would you like to enable {step['name'].lower()}?",
                    view=view,
                )
            except Exception as e:
                logger.error(f"Failed to update message for boolean step: {e}")
                if not interaction.response.is_done():
                    await interaction.response.send_message(
                        f"Would you like to enable {step['name'].lower()}?",
                        view=view,
                        ephemeral=True,
                    )
            return

        # Handle modal input steps (URL inputs, etc.)
        select_class = step["select"]
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

                try:
                    await interaction.response.send_modal(modal)
                except discord.errors.InteractionResponded:
                    await interaction.followup.send(
                        f"Please enter the {step['name']} manually. The setup will continue automatically.",
                        ephemeral=True,
                    )
                    self.current_step += 1
                    await self.process_next_selection(interaction)
                return
            else:
                self.current_step += 1
                await self.process_next_selection(interaction)
                return

        # Handle select menu steps (roles, etc.)
        if select_class == ChannelSelect:
            items = interaction.guild.text_channels
        else:
            items = interaction.guild.roles

        if not items:
            try:
                await self.message.edit(
                    content=f"No {step['name'].lower()} found. Please create one and try again.",
                    view=None,
                )
            except Exception as e:
                logger.error(f"Failed to update message for empty items: {e}")
                if not interaction.response.is_done():
                    await interaction.response.send_message(
                        f"No {step['name'].lower()} found. Please create one and try again.",
                        ephemeral=True,
                    )
            return

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

        try:
            await self.message.edit(
                content=f"Please select a {step['name'].lower()}:", view=self
            )
        except Exception as e:
            logger.error(f"Failed to update message with new view: {e}")
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    f"Please select a {step['name'].lower()}:",
                    view=self,
                    ephemeral=True,
                )
            else:
                await interaction.followup.send(
                    f"Please select a {step['name'].lower()}:",
                    view=self,
                    ephemeral=True,
                )

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
                        "main_chat_channel_id",
                        "admin_role",
                        "authorized_role",
                        "member_role",
                    ]:
                        # Handle single values for roles and channels
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
        self.guild_setup_locks = set()  # Track guilds with active /setup

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
        guild_id = interaction.guild_id
        if guild_id in self.guild_setup_locks:
            await interaction.response.send_message(
                "❌ A setup is already in progress for this server. Please wait for it to complete before starting another.",
                ephemeral=True,
            )
            return
        self.guild_setup_locks.add(guild_id)
        logger.info(
            f"Setup command initiated by {interaction.user} in guild {guild_id}"
        )
        try:
            # Check if guild exists in database
            existing_settings = await self.bot.db_manager.fetch_one(
                "SELECT * FROM guild_settings WHERE guild_id = $1", guild_id
            )

            # If guild doesn't exist, create it with default values for the new table structure
            if not existing_settings:
                await self.bot.db_manager.execute(
                    """
                    INSERT INTO guild_settings
                    (guild_id, is_active, subscription_level, is_paid,
                     embed_channel_1, command_channel_1, admin_channel_1,
                     live_game_updates, units_display_mode, min_units, max_units,
                     embed_color, timezone, auto_sync_commands)
                    VALUES ($1, 1, 'free', 0,
                           NULL, NULL, NULL,
                           0, 'auto', 0.50, 3.00,
                           '#00FF00', 'UTC', 1)
                    """,
                    guild_id,
                )
                subscription_level = "free"
            else:
                # Determine subscription level based on the new table structure
                is_paid = existing_settings.get("is_paid", 0)
                db_subscription_level = existing_settings.get(
                    "subscription_level", "free"
                )

                # Check for platinum features
                platinum_features_enabled = existing_settings.get(
                    "platinum_features_enabled", 0
                )

                # Map subscription levels properly
                if platinum_features_enabled or db_subscription_level == "platinum":
                    subscription_level = "platinum"
                elif is_paid or db_subscription_level == "premium":
                    subscription_level = "premium"
                else:
                    subscription_level = "free"

                logger.info(
                    f"Guild {guild_id} - is_paid: {is_paid}, db_subscription_level: {db_subscription_level}, "
                    f"platinum_features_enabled: {platinum_features_enabled}, final_subscription_level: {subscription_level}"
                )

                # Update subscription_level in database if it doesn't match
                if subscription_level != db_subscription_level:
                    await self.bot.db_manager.execute(
                        "UPDATE guild_settings SET subscription_level = $1 WHERE guild_id = $2",
                        subscription_level,
                        guild_id,
                    )
                    logger.info(
                        f"Updated subscription_level to '{subscription_level}' for guild {guild_id}"
                    )

            # --- Create static/guilds/{guild_id}/users directory ---
            try:
                base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
                guild_dir = os.path.join(base_dir, "static", "guilds", str(guild_id))
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

            # Send initial message as ephemeral
            await interaction.response.send_message(
                f"Starting server setup... (Subscription Level: {subscription_level.title()})",
                view=view,
                ephemeral=True,
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
        finally:
            self.guild_setup_locks.discard(guild_id)

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
        name="premium",
        description="Get the link to subscribe your server to premium features.",
    )
    @app_commands.checks.has_permissions(manage_guild=True)
    async def premium_command(self, interaction: Interaction):
        """Sends the subscription webpage link for premium services."""
        try:
            guild_id = interaction.guild_id
            user = interaction.user

            # Check if user has authorized role - REQUIRED for all users
            guild_settings = await self.bot.admin_service.get_guild_settings(guild_id)
            if guild_settings and guild_settings.get("authorized_role"):
                authorized_role_id = guild_settings["authorized_role"]
                has_authorized_role = any(
                    role.id == authorized_role_id for role in user.roles
                )
                if not has_authorized_role:
                    await interaction.response.send_message(
                        "❌ You need the authorized user role to use this command.",
                        ephemeral=True,
                    )
                    return
            else:
                # If no authorized role is set, only allow admins
                if not user.guild_permissions.administrator:
                    await interaction.response.send_message(
                        "❌ You need administrator permissions to use this command.",
                        ephemeral=True,
                    )
                    return

            # Check if user is admin for subscription link
            is_admin = user.guild_permissions.administrator

            embed = discord.Embed(
                title="⭐ Premium Tier - Upgrade Available",
                description="Unlock advanced features with Premium tier!",
                color=0x00FF00,
            )

            embed.add_field(
                name="Premium Features",
                value="🎯 Advanced Betting Tools\n"
                "📊 Enhanced Analytics\n"
                "🔔 Custom Notifications\n"
                "🎨 Custom Branding\n"
                "📈 Performance Tracking\n"
                "⚡ Priority Support",
                inline=True,
            )

            embed.add_field(
                name="Pricing",
                value="⭐ **Premium**: $49.99/month\n" "💎 **Platinum**: $99.99/month",
                inline=True,
            )

            if is_admin:
                subscription_url = "https://betting-server-manager.us/subscribe"
                embed.add_field(
                    name="Subscribe Now",
                    value=f"[Click here to subscribe]({subscription_url})",
                    inline=False,
                )
            else:
                embed.add_field(
                    name="Contact Admin",
                    value="Please contact a server administrator to upgrade to Premium tier.",
                    inline=False,
                )

            embed.set_footer(text="Upgrade to unlock these powerful features!")

            await interaction.response.send_message(embed=embed)

        except Exception as e:
            logger.error(f"Error in premium_command: {e}")
            await interaction.response.send_message(
                "❌ An error occurred while processing your request.", ephemeral=True
            )

    @app_commands.command(
        name="fix_commands", description="Fix and sync all bot commands (admin only)"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def fix_commands(self, interaction: Interaction):
        """Fix and sync all bot commands."""
        try:
            await interaction.response.defer(ephemeral=True)

            embed = discord.Embed(
                title="EMERGENCY COMMAND FIX",
                description="Force syncing ALL commands to this guild...",
                color=0xFF0000,
            )

            # Force reload ALL extensions first
            embed.add_field(
                name="🔄 Step 1: Reloading Extensions",
                value="Reloading all command extensions...",
                inline=False,
            )

            extensions_to_reload = [
                "bot.commands.admin",
                "bot.commands.betting",
                "bot.commands.enhanced_player_props",
                "bot.commands.parlay_betting",
                "bot.commands.remove_user",
                "bot.commands.setid",
                "bot.commands.add_user",
                "bot.commands.stats",
                "bot.commands.load_logos",
                "bot.commands.schedule",
                "bot.commands.maintenance",
                "bot.commands.odds",
                "bot.commands.platinum_fixed",
                "bot.commands.platinum_api",
                "bot.commands.sync_cog",
            ]

            reloaded_count = 0
            for ext in extensions_to_reload:
                try:
                    await self.bot.reload_extension(ext)
                    reloaded_count += 1
                except Exception as e:
                    logger.warning(f"Failed to reload {ext}: {e}")

            embed.add_field(
                name="✅ Extensions Reloaded",
                value=f"Successfully reloaded {reloaded_count}/{len(extensions_to_reload)} extensions",
                inline=False,
            )

            # Clear all commands and re-add them
            embed.add_field(
                name="🧹 Step 2: Clearing Commands",
                value="Clearing existing command tree...",
                inline=False,
            )

            self.bot.tree.clear_commands(guild=discord.Object(id=interaction.guild_id))

            # Get all available commands after reload
            all_commands = [cmd.name for cmd in self.bot.tree.get_commands()]
            logger.info(f"All available commands after reload: {all_commands}")

            embed.add_field(
                name="Available Commands",
                value="\n".join([f"• `/{cmd}`" for cmd in all_commands[:20]])
                + (
                    f"\n... and {len(all_commands) - 20} more"
                    if len(all_commands) > 20
                    else ""
                ),
                inline=False,
            )

            # Force sync to guild
            embed.add_field(
                name="🔄 Step 3: Force Syncing",
                value="Syncing all commands to this guild...",
                inline=False,
            )

            guild_obj = discord.Object(id=interaction.guild_id)
            synced = await self.bot.tree.sync(guild=guild_obj)
            synced_names = [cmd.name for cmd in synced]

            embed.add_field(
                name="✅ SYNC COMPLETE",
                value=f"Successfully synced {len(synced)} commands to guild!",
                inline=False,
            )

            embed.add_field(
                name="Synced Commands",
                value="\n".join([f"• `/{cmd}`" for cmd in synced_names[:25]])
                + (
                    f"\n... and {len(synced_names) - 25} more"
                    if len(synced_names) > 25
                    else ""
                ),
                inline=False,
            )

            # Check for critical commands
            critical_commands = ["fix_commands"]
            missing_critical = [
                cmd for cmd in critical_commands if cmd not in synced_names
            ]

            if missing_critical:
                embed.add_field(
                    name="⚠️ MISSING CRITICAL COMMANDS",
                    value="\n".join([f"• `/{cmd}`" for cmd in missing_critical]),
                    inline=False,
                )
                embed.color = 0xFFA500
            else:
                embed.add_field(
                    name="🎉 SUCCESS!",
                    value="All critical commands are now available!",
                    inline=False,
                )
                embed.color = 0x00FF00

            embed.set_footer(
                text=f"Guild ID: {interaction.guild_id} • Emergency fix at {discord.utils.utcnow().strftime('%H:%M:%S')}"
            )

            await interaction.followup.send(embed=embed, ephemeral=True)

        except Exception as e:
            logger.error(f"Emergency fix commands failed: {e}", exc_info=True)
            error_embed = discord.Embed(
                title="❌ EMERGENCY FIX FAILED",
                description=f"Critical error: {str(e)}",
                color=0xFF0000,
            )

            if not interaction.response.is_done():
                await interaction.response.send_message(
                    embed=error_embed, ephemeral=True
                )
            else:
                await interaction.followup.send(embed=error_embed, ephemeral=True)

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
