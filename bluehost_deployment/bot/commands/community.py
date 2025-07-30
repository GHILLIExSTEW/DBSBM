import logging
from datetime import datetime

import discord
from discord import app_commands
from discord.ext import commands

logger = logging.getLogger(__name__)


class CommunityCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def track_command_usage(self, guild_id: int, user_id: int, command_name: str):
        """Track command usage for analytics."""
        try:
            if (
                hasattr(self.bot, "community_analytics_service")
                and self.bot.community_analytics_service
            ):
                await self.bot.community_analytics_service.track_community_command(
                    guild_id, user_id, command_name
                )
        except Exception as e:
            logger.error(f"Failed to track community command: {e}")

    @app_commands.command(name="discuss", description="Start a community discussion")
    async def discuss(
        self, interaction: discord.Interaction, topic: str, question: str
    ):
        """Start a community discussion topic."""
        embed = discord.Embed(
            title=f"💬 Community Discussion: {topic}",
            description=question,
            color=0x00FF00,
            timestamp=datetime.utcnow(),
        )
        embed.set_footer(text=f"Started by {interaction.user.display_name}")
        embed.set_author(
            name=interaction.user.display_name,
            icon_url=interaction.user.display_avatar.url,
        )

        await interaction.response.send_message(embed=embed)
        logger.info(
            f"Community discussion started by {interaction.user.id} in guild {interaction.guild_id}: {topic}"
        )

        # Track command usage for analytics
        await self.track_command_usage(
            interaction.guild_id, interaction.user.id, "discuss"
        )

    @app_commands.command(name="funfact", description="Share a fun sports fact")
    async def funfact(self, interaction: discord.Interaction, fact: str):
        """Share a fun sports fact with the community."""
        embed = discord.Embed(
            title="📚 Fun Fact of the Day",
            description=fact,
            color=0xFFD700,
            timestamp=datetime.utcnow(),
        )
        embed.set_footer(text=f"Shared by {interaction.user.display_name}")
        embed.set_author(
            name=interaction.user.display_name,
            icon_url=interaction.user.display_avatar.url,
        )

        await interaction.response.send_message(embed=embed)
        logger.info(
            f"Fun fact shared by {interaction.user.id} in guild {interaction.guild_id}"
        )

        # Track command usage for analytics
        await self.track_command_usage(
            interaction.guild_id, interaction.user.id, "funfact"
        )

    @app_commands.command(name="celebrate", description="Celebrate with the community")
    async def celebrate(
        self, interaction: discord.Interaction, reason: str, message: str = ""
    ):
        """Celebrate wins and milestones with the community."""
        embed = discord.Embed(
            title=f"🎉 Celebration: {reason}",
            description=message or "Let's celebrate together! 🎊",
            color=0xFF69B4,
            timestamp=datetime.utcnow(),
        )
        embed.set_footer(text=f"Celebrating with {interaction.user.display_name}")
        embed.set_author(
            name=interaction.user.display_name,
            icon_url=interaction.user.display_avatar.url,
        )

        await interaction.response.send_message(embed=embed)
        logger.info(
            f"Celebration started by {interaction.user.id} in guild {interaction.guild_id}: {reason}"
        )

        # Track command usage for analytics
        await self.track_command_usage(
            interaction.guild_id, interaction.user.id, "celebrate"
        )

    @app_commands.command(name="encourage", description="Encourage another user")
    async def encourage(
        self, interaction: discord.Interaction, user: discord.Member, message: str
    ):
        """Encourage another community member."""
        embed = discord.Embed(
            title="💪 Encouragement",
            description=f"{interaction.user.mention} is encouraging {user.mention}:\n\n{message}",
            color=0x87CEEB,
            timestamp=datetime.utcnow(),
        )
        embed.set_footer(text=f"Spread positivity in our community!")
        embed.set_author(
            name=interaction.user.display_name,
            icon_url=interaction.user.display_avatar.url,
        )

        await interaction.response.send_message(embed=embed)
        logger.info(
            f"Encouragement from {interaction.user.id} to {user.id} in guild {interaction.guild_id}"
        )

        # Track command usage for analytics
        await self.track_command_usage(
            interaction.guild_id, interaction.user.id, "encourage"
        )

    @app_commands.command(
        name="help_community", description="Ask for help from the community"
    )
    async def help_community(
        self, interaction: discord.Interaction, topic: str, question: str
    ):
        """Ask the community for help."""
        embed = discord.Embed(
            title=f"❓ Help Request: {topic}",
            description=question,
            color=0xFFA500,
            timestamp=datetime.utcnow(),
        )
        embed.set_footer(text=f"Help requested by {interaction.user.display_name}")
        embed.set_author(
            name=interaction.user.display_name,
            icon_url=interaction.user.display_avatar.url,
        )

        await interaction.response.send_message(embed=embed)
        logger.info(
            f"Help request from {interaction.user.id} in guild {interaction.guild_id}: {topic}"
        )

        # Track command usage for analytics
        await self.track_command_usage(
            interaction.guild_id, interaction.user.id, "help_community"
        )

    @app_commands.command(name="thanks", description="Thank someone for help")
    async def thanks(
        self, interaction: discord.Interaction, user: discord.Member, reason: str
    ):
        """Thank someone for their help."""
        embed = discord.Embed(
            title="🙏 Thank You",
            description=f"{interaction.user.mention} thanks {user.mention} for: {reason}",
            color=0x32CD32,
            timestamp=datetime.utcnow(),
        )
        embed.set_footer(text=f"Gratitude makes our community stronger!")
        embed.set_author(
            name=interaction.user.display_name,
            icon_url=interaction.user.display_avatar.url,
        )

        await interaction.response.send_message(embed=embed)
        logger.info(
            f"Thanks from {interaction.user.id} to {user.id} in guild {interaction.guild_id}"
        )

        # Track command usage for analytics
        await self.track_command_usage(
            interaction.guild_id, interaction.user.id, "thanks"
        )

    @app_commands.command(name="shoutout", description="Give a shoutout to someone")
    async def shoutout(
        self, interaction: discord.Interaction, user: discord.Member, reason: str
    ):
        """Give a shoutout to a community member."""
        embed = discord.Embed(
            title="📢 Community Shoutout",
            description=f"{interaction.user.mention} is giving a shoutout to {user.mention}:\n\n**{reason}**",
            color=0x9370DB,
            timestamp=datetime.utcnow(),
        )
        embed.set_footer(text=f"Recognizing great community members!")
        embed.set_author(
            name=interaction.user.display_name,
            icon_url=interaction.user.display_avatar.url,
        )

        await interaction.response.send_message(embed=embed)
        logger.info(
            f"Shoutout from {interaction.user.id} to {user.id} in guild {interaction.guild_id}"
        )

        # Track command usage for analytics
        await self.track_command_usage(
            interaction.guild_id, interaction.user.id, "shoutout"
        )

    @app_commands.command(name="poll", description="Create a community poll")
    async def poll(
        self,
        interaction: discord.Interaction,
        question: str,
        option1: str,
        option2: str,
        option3: str = None,
        option4: str = None,
    ):
        """Create a community poll."""
        embed = discord.Embed(
            title="📊 Community Poll",
            description=f"**{question}**",
            color=0x4169E1,
            timestamp=datetime.utcnow(),
        )

        options = [option1, option2]
        if option3:
            options.append(option3)
        if option4:
            options.append(option4)

        reactions = ["1️⃣", "2️⃣", "3️⃣", "4️⃣"]

        for i, option in enumerate(options):
            embed.add_field(name=f"{reactions[i]} {option}", value="", inline=False)

        embed.set_footer(text=f"Poll created by {interaction.user.display_name}")
        embed.set_author(
            name=interaction.user.display_name,
            icon_url=interaction.user.display_avatar.url,
        )

        message = await interaction.response.send_message(embed=embed)

        # Add reaction options
        for i in range(len(options)):
            await message.add_reaction(reactions[i])

        logger.info(
            f"Poll created by {interaction.user.id} in guild {interaction.guild_id}: {question}"
        )

        # Track command usage for analytics
        await self.track_command_usage(
            interaction.guild_id, interaction.user.id, "poll"
        )


async def setup(bot):
    await bot.add_cog(CommunityCog(bot))
