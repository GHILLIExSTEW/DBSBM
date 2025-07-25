"""
UFC Fighter Dropdown System
Provides hierarchical dropdown selection for UFC fighters by category.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional

import discord
from discord import app_commands
from discord.ext import commands

from bot.services.ufc_fighter_service import ufc_fighter_service

logger = logging.getLogger(__name__)


class UFCGenderDropdown(discord.ui.Select):
    """Dropdown for selecting gender (Men/Women)."""

    def __init__(self, parent_view):
        self.parent_view = parent_view
        options = []

        for gender in ufc_fighter_service.get_gender_options():
            options.append(
                discord.SelectOption(
                    label=gender, value=gender, description=f"Select {gender} fighters"
                )
            )

        super().__init__(
            placeholder="Select gender...", min_values=1, max_values=1, options=options
        )

    async def callback(self, interaction: discord.Interaction):
        selected_gender = self.values[0]
        self.parent_view.selected_gender = selected_gender
        await self.parent_view.update_category_dropdown(interaction)


class UFCCategoryDropdown(discord.ui.Select):
    """Dropdown for selecting weight category."""

    def __init__(self, parent_view, gender: str):
        self.parent_view = parent_view
        options = []

        categories = ufc_fighter_service.get_category_options(gender)
        for category in categories:
            # Get fighter count for this category
            fighter_count = len(ufc_fighter_service.get_fighters_by_category(category))
            options.append(
                discord.SelectOption(
                    label=f"{category} ({fighter_count})",
                    value=category,
                    description=f"{fighter_count} fighters in {category}",
                )
            )

        super().__init__(
            placeholder="Select weight category...",
            min_values=1,
            max_values=1,
            options=options,
        )

    async def callback(self, interaction: discord.Interaction):
        selected_category = self.values[0]
        self.parent_view.selected_category = selected_category
        await self.parent_view.update_fighter_dropdown(interaction)


class UFCFighterDropdown(discord.ui.Select):
    """Dropdown for selecting individual fighters."""

    def __init__(self, parent_view, category: str, page: int = 0, page_size: int = 20):
        self.parent_view = parent_view
        self.page = page
        self.page_size = page_size

        fighters = ufc_fighter_service.get_fighter_options(category)
        total_fighters = len(fighters)

        start = page * page_size
        end = min(start + page_size, total_fighters)
        page_fighters = fighters[start:end]

        options = []

        # Add navigation options
        if page > 0:
            options.append(
                discord.SelectOption(
                    label="⬅️ Previous Page",
                    value="previous",
                    description="Go to previous page",
                )
            )

        # Add fighter options
        for fighter in page_fighters:
            options.append(
                discord.SelectOption(
                    label=f"{fighter['label']}",
                    value=fighter["value"],
                    description=f"{fighter['nationality']} - {category}",
                )
            )

        # Add next page option
        if end < total_fighters:
            options.append(
                discord.SelectOption(
                    label="Next Page ➡️", value="next", description="Go to next page"
                )
            )

        super().__init__(
            placeholder=f"Select fighter from {category}...",
            min_values=1,
            max_values=1,
            options=options,
        )

    async def callback(self, interaction: discord.Interaction):
        value = self.values[0]

        if value == "previous":
            self.parent_view.fighter_page -= 1
            await self.parent_view.update_fighter_dropdown(interaction)
        elif value == "next":
            self.parent_view.fighter_page += 1
            await self.parent_view.update_fighter_dropdown(interaction)
        else:
            # Fighter selected
            fighter_id = value
            fighter_data = ufc_fighter_service.get_fighter_by_id(fighter_id)
            if fighter_data:
                await self.parent_view.show_fighter_details(interaction, fighter_data)


class UFCDropdownView(discord.ui.View):
    """Main view for UFC fighter selection."""

    def __init__(self, cog):
        super().__init__(timeout=300)  # 5 minute timeout
        self.cog = cog
        self.selected_gender = None
        self.selected_category = None
        self.fighter_page = 0

        # Start with gender selection
        self.add_item(UFCGenderDropdown(self))

    async def update_category_dropdown(self, interaction: discord.Interaction):
        """Update to show category dropdown."""
        self.clear_items()
        self.add_item(UFCGenderDropdown(self))
        self.add_item(UFCCategoryDropdown(self, self.selected_gender))

        embed = discord.Embed(
            title="🥊 UFC Fighter Selection",
            description=f"Selected: **{self.selected_gender}**\nChoose a weight category:",
            color=0x00FF00,
        )

        await interaction.response.edit_message(embed=embed, view=self)

    async def update_fighter_dropdown(self, interaction: discord.Interaction):
        """Update to show fighter dropdown."""
        self.clear_items()
        self.add_item(UFCGenderDropdown(self))
        self.add_item(UFCCategoryDropdown(self, self.selected_gender))
        self.add_item(
            UFCFighterDropdown(self, self.selected_category, self.fighter_page)
        )

        fighters = ufc_fighter_service.get_fighters_by_category(self.selected_category)

        embed = discord.Embed(
            title="🥊 UFC Fighter Selection",
            description=f"Selected: **{self.selected_gender}** → **{self.selected_category}**\nChoose a fighter:",
            color=0x00FF00,
        )

        embed.add_field(
            name="Category Info",
            value=f"**{len(fighters)}** fighters in {self.selected_category}",
            inline=False,
        )

        await interaction.response.edit_message(embed=embed, view=self)

    async def show_fighter_details(
        self, interaction: discord.Interaction, fighter_data: Dict
    ):
        """Show detailed fighter information."""
        embed = discord.Embed(
            title=f"🥊 {fighter_data['name'].title()}",
            description=f"**Category:** {fighter_data['category']}\n**Nationality:** {fighter_data['nationality']}",
            color=0xFF0000,
        )

        embed.add_field(
            name="Record", value=f"**{fighter_data['record']}** (W-L-D)", inline=True
        )

        # Check if logo exists
        logo_path = fighter_data.get("logo_path", "")
        if logo_path and Path(logo_path).exists():
            embed.set_thumbnail(url=f"attachment://{Path(logo_path).name}")

        embed.add_field(name="Fighter ID", value=f"`{fighter_data['id']}`", inline=True)

        # Add action buttons
        view = discord.ui.View(timeout=60)

        # Add betting options if needed
        bet_button = discord.ui.Button(
            label="Place Bet",
            style=discord.ButtonStyle.primary,
            custom_id=f"bet_fighter_{fighter_data['id']}",
        )
        view.add_item(bet_button)

        # Back button
        back_button = discord.ui.Button(
            label="Back to Selection",
            style=discord.ButtonStyle.secondary,
            custom_id="back_to_selection",
        )
        view.add_item(back_button)

        await interaction.response.edit_message(embed=embed, view=view)


class UFC(commands.Cog):
    """UFC fighter selection and betting commands."""

    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="ufc_fighters", description="Browse UFC fighters by weight category"
    )
    async def ufc_fighters(self, interaction: discord.Interaction):
        """Main command to browse UFC fighters."""
        await interaction.response.defer(ephemeral=True)

        # Check if UFC fighter data is available
        if not ufc_fighter_service.organized_data:
            await interaction.followup.send(
                "❌ UFC fighter data not available!\n"
                "Please run the fighter fetcher first.",
                ephemeral=True,
            )
            return

        embed = discord.Embed(
            title="🥊 UFC Fighter Selection",
            description="Select a gender to browse fighters by weight category:",
            color=0x00FF00,
        )

        # Show stats
        stats = ufc_fighter_service.get_category_stats()
        stats_text = ""
        for category, data in list(stats.items())[:5]:  # Show first 5 categories
            stats_text += f"• **{category}**: {data['count']} fighters\n"

        if stats_text:
            embed.add_field(name="Available Categories", value=stats_text, inline=False)

        view = UFCDropdownView(self)
        await interaction.followup.send(embed=embed, view=view, ephemeral=True)

    @app_commands.command(
        name="ufc_search", description="Search for a UFC fighter by name"
    )
    async def ufc_search(self, interaction: discord.Interaction, query: str):
        """Search for UFC fighters by name."""
        await interaction.response.defer(ephemeral=True)

        if not ufc_fighter_service.organized_data:
            await interaction.followup.send(
                "❌ UFC fighter data not available!", ephemeral=True
            )
            return

        results = ufc_fighter_service.search_fighters(query, limit=10)

        if not results:
            await interaction.followup.send(
                f"❌ No fighters found matching '{query}'", ephemeral=True
            )
            return

        embed = discord.Embed(
            title=f"🥊 UFC Fighter Search: '{query}'",
            description=f"Found **{len(results)}** fighters:",
            color=0x00FF00,
        )

        for fighter in results[:5]:  # Show first 5 results
            embed.add_field(
                name=fighter["name"].title(),
                value=f"**Category:** {fighter['category']}\n**Record:** {fighter['record']}\n**Nationality:** {fighter['nationality']}",
                inline=True,
            )

        if len(results) > 5:
            embed.set_footer(text=f"And {len(results) - 5} more results...")

        await interaction.followup.send(embed=embed, ephemeral=True)


async def setup(bot):
    """Setup the UFC cog."""
    await bot.add_cog(UFC(bot))
