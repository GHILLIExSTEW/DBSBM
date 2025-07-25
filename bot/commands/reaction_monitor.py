import os

import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import Button, Select, View


class ReactionMonitorView(View):
    def __init__(self, bot, guild_id):
        super().__init__(timeout=120)
        self.bot = bot
        self.guild_id = guild_id
        self.add_item(ReactionMonitorDropdown(self))


class ReactionMonitorDropdown(Select):
    def __init__(self, parent_view):
        options = [
            discord.SelectOption(
                label="Turn on reaction monitoring", value="monitor_on"
            ),
            discord.SelectOption(
                label="Upload custom emoji for 'Won'", value="upload_won"
            ),
            discord.SelectOption(
                label="Upload custom emoji for 'Loss'", value="upload_loss"
            ),
        ]
        super().__init__(
            placeholder="Choose an action...",
            options=options,
            min_values=1,
            max_values=1,
        )
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction):
        value = self.values[0]
        if value == "monitor_on":
            await interaction.response.send_message(
                "✅ Reaction monitoring enabled! (This is a placeholder, implement logic as needed)",
                ephemeral=True,
            )
        else:
            label = "Won" if value == "upload_won" else "Loss"
            await interaction.response.send_message(
                f"Please upload your custom emoji for '{label}' as an image file.",
                ephemeral=True,
            )
            self.parent_view.bot.reaction_monitor_upload_state[interaction.user.id] = {
                "guild_id": interaction.guild_id,
                "type": value,
                "channel_id": interaction.channel_id,
            }


class ReactionMonitorCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Track users waiting to upload an emoji
        self.bot.reaction_monitor_upload_state = {}

    @app_commands.command(
        name="reaction_monitor",
        description="Configure reaction monitoring and custom emojis.",
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def reaction_monitor(self, interaction: discord.Interaction):
        view = ReactionMonitorView(self.bot, interaction.guild_id)
        await interaction.response.send_message(
            "What would you like to do?", view=view, ephemeral=True
        )

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        # Only handle DMs or messages in the guild where the upload was requested
        if message.author.bot or not message.attachments:
            return
        state = self.bot.reaction_monitor_upload_state.get(message.author.id)
        if not state:
            return
        if message.guild is None or message.guild.id != state["guild_id"]:
            return
        attachment = message.attachments[0]
        # Only allow image files
        if not attachment.filename.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
            await message.channel.send(
                "❌ Please upload a valid image file (png, jpg, jpeg, webp).",
                delete_after=10,
            )
            return
        # Save the file
        guild_id = state["guild_id"]
        emoji_type = "won" if state["type"] == "upload_won" else "loss"
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        emoji_dir = os.path.join(base_dir, "static", "guilds", str(guild_id), "emojis")
        os.makedirs(emoji_dir, exist_ok=True)
        file_path = os.path.join(emoji_dir, f"{emoji_type}.webp")
        await attachment.save(file_path)
        await message.channel.send(
            f"✅ Custom emoji for '{emoji_type.capitalize()}' uploaded successfully!",
            delete_after=10,
        )
        del self.bot.reaction_monitor_upload_state[message.author.id]


async def setup(bot):
    await bot.add_cog(ReactionMonitorCog(bot))
