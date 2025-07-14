# betting-bot/commands/setid.py

import discord
from discord import app_commands, Interaction, Member, Attachment
from discord.ext import commands # Import commands for Cog
from discord.ui import Modal, TextInput, View, Button, button # Corrected import for button decorator
import logging
import os
import requests # Keep requests for URL fetching
from io import BytesIO
from PIL import Image # Keep Pillow for image processing
from typing import Optional
from .admin import require_registered_guild

# Use relative imports
try:
    # Import db_manager only for type hint if needed
    # from ..data.db_manager import DatabaseManager
    # Import errors if needed
    # from ..utils.errors import ...
    pass # No specific service needed directly here? DB access via bot.db_manager
except ImportError:
    # Fallback imports
    # from data.db_manager import DatabaseManager
    # from utils.errors import ...
    pass

logger = logging.getLogger(__name__)

# --- UI Components ---

class CapperModal(Modal, title="Capper Profile Setup"):
    # Corrected __init__ to not require guild_id/user_id if passed via interaction context
    def __init__(self, target_user: Member, db_manager):
        super().__init__(timeout=300) # Add timeout
        self.target_user = target_user
        self.db = db_manager # Store db_manager instance

    display_name = TextInput(
        label="Display Name",
        placeholder="Enter the capper's display name",
        required=True,
        max_length=32
    )

    banner_color = TextInput(
        label="Banner Color (Hex)",
        placeholder="#RRGGBB (e.g., #0096FF)",
        required=False,
        max_length=7,
        default="#0096FF" # Provide default
    )

    async def on_submit(self, interaction: Interaction):
        try:
            # Acknowledge interaction
            await interaction.response.defer(ephemeral=True, thinking=True)

            guild_id = interaction.guild_id
            user_id = self.target_user.id
            color_value = self.banner_color.value.strip()

            # Validate hex color
            if color_value:
                if not color_value.startswith('#'):
                    color_value = '#' + color_value
                if len(color_value) != 7:
                    # Try parsing to see if it's a valid hex
                    try: int(color_value[1:], 16)
                    except ValueError:
                         await interaction.followup.send(
                              "❌ Invalid hex color format. Please use #RRGGBB (e.g., #3498db).",
                              ephemeral=True
                         )
                         return
                # Store valid color or default
                final_color = color_value
            else:
                 final_color = "#0096FF" # Default if empty

            # Create the capper entry using shared db_manager
            # Assumes 'cappers' table exists with columns: guild_id, user_id, display_name, banner_color, updated_at
            # Using ON CONFLICT DO NOTHING for safety, though check beforehand is better
            insert_status = await self.db.execute(
                """
                INSERT INTO cappers (
                    guild_id, user_id, display_name, banner_color, updated_at
                ) VALUES (%s, %s, %s, %s, UTC_TIMESTAMP())
                ON DUPLICATE KEY UPDATE updated_at = UTC_TIMESTAMP()
                """,
                guild_id,
                user_id,
                self.display_name.value,
                final_color
            )

            # Check if insert happened (status might vary depending on db_manager.execute)
            # For now, assume success if no exception
            logger.info(f"Capper entry created/exists for {user_id} in guild {guild_id}.")

            # Follow up - ask for image
            image_view = ImageUploadView(guild_id=guild_id, user_id=user_id, db_manager=self.db)
            await interaction.followup.send(
                f"✅ Profile base for {self.target_user.mention} setup! Now, please provide a profile picture.",
                view=image_view,
                ephemeral=True
            )

        except Exception as e:
            logger.exception(f"Error in CapperModal submission: {e}")
            # Ensure followup is used if response was deferred
            await interaction.followup.send(
                "❌ An error occurred while setting up the profile.",
                ephemeral=True
            )

    async def on_error(self, interaction: Interaction, error: Exception) -> None:
         logger.error(f"Error in CapperModal: {error}", exc_info=True)
         # Use followup because original response was likely deferred
         await interaction.followup.send('❌ An error occurred with the profile setup modal.', ephemeral=True)


class ImageUploadView(View):
    def __init__(self, guild_id: int, user_id: int, db_manager):
        super().__init__(timeout=300) # 5 minute timeout for user to respond
        self.guild_id = guild_id
        self.user_id = user_id
        self.db = db_manager
        self.waiting_for_upload = False

    async def interaction_check(self, interaction: Interaction) -> bool:
         return True # Allow interaction

    @button(label="Provide URL", style=discord.ButtonStyle.secondary, custom_id="capper_provide_url")
    async def provide_url_button(self, interaction: Interaction, button: Button):
        modal = ImageURLModal(guild_id=self.guild_id, user_id=self.user_id, db_manager=self.db)
        await interaction.response.send_modal(modal)

    @button(label="Upload Image", style=discord.ButtonStyle.primary, custom_id="capper_upload_image")
    async def upload_image_button(self, interaction: Interaction, button: Button):
        self.waiting_for_upload = True
        await interaction.response.send_message(
            "Please upload your image as a file in this channel (PNG, JPG, GIF, WEBP). This prompt will timeout in 2 minutes.",
            ephemeral=True
        )
        # Wait for the next message from the user with an attachment
        def check(msg):
            return (
                msg.author.id == interaction.user.id and
                msg.channel.id == interaction.channel.id and
                msg.attachments and
                any(a.content_type and a.content_type.startswith('image/') for a in msg.attachments)
            )
        try:
            msg = await interaction.client.wait_for('message', timeout=120, check=check)
            attachment = next(a for a in msg.attachments if a.content_type and a.content_type.startswith('image/'))
            image_data = BytesIO(await attachment.read())
            with Image.open(image_data) as img:
                if img.format not in ['PNG', 'JPEG', 'GIF', 'WEBP']:
                    await interaction.followup.send(
                        "❌ Invalid image format. Use PNG, JPG, GIF, WEBP.", ephemeral=True
                    )
                    return
                filename = f"{self.user_id}.png"
                base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
                save_dir = os.path.join(base_dir, 'assets', 'logos', str(self.guild_id))
                os.makedirs(save_dir, exist_ok=True)
                save_path = os.path.join(save_dir, filename)
                img.save(save_path, 'PNG')
                logger.info(f"Saved capper logo to {save_path}")
                db_path = os.path.relpath(save_path, base_dir)
                await self.db.execute(
                    """
                    UPDATE cappers
                    SET image_path = %s, updated_at = UTC_TIMESTAMP()
                    WHERE guild_id = %s AND user_id = %s
                    """,
                    db_path, self.guild_id, self.user_id
                )
                await interaction.followup.send(
                    "✅ Profile picture updated successfully!",
                    ephemeral=True
                )
        except Exception as e:
            logger.exception(f"Error processing uploaded image: {e}")
            await interaction.followup.send(
                "❌ An error occurred while processing the uploaded image or the upload timed out.",
                ephemeral=True
            )

    async def on_timeout(self) -> None:
         logger.info(f"ImageUploadView timed out for user {self.user_id}")
         # Optionally update original message or disable view components
         # self.clear_items()
         # await self.message.edit(content="Image upload prompt timed out.", view=self) # Need message reference

class ImageURLModal(Modal, title="Enter Profile Image URL"):
    def __init__(self, guild_id: int, user_id: int, db_manager):
        super().__init__(timeout=300)
        self.guild_id = guild_id
        self.user_id = user_id
        self.db = db_manager

    url = TextInput(
        label="Image URL",
        placeholder="https://example.com/image.png",
        style=discord.TextStyle.short,
        required=True
    )

    async def on_submit(self, interaction: Interaction):
        try:
            await interaction.response.defer(ephemeral=True, thinking=True)
            image_url = self.url.value

            # --- Download and Process Image (Consider running in executor) ---
            try:
                 # Use a timeout for the request
                 response = requests.get(image_url, timeout=10, stream=True)
                 response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)

                 # Check content type (optional but recommended)
                 content_type = response.headers.get('content-type', '').lower()
                 if not content_type.startswith('image/'):
                      await interaction.followup.send("❌ URL does not point to a valid image type.", ephemeral=True)
                      return

                 # Read image data
                 image_data = BytesIO(response.content)
                 with Image.open(image_data) as img:
                      # Validate format
                      if img.format not in ['PNG', 'JPEG', 'GIF', 'WEBP']: # Allow WEBP?
                           await interaction.followup.send("❌ Invalid image format. Use PNG, JPG, GIF.", ephemeral=True)
                           return

                      # Define save path and ensure directory exists
                      # Save as PNG for consistency? Or keep original format? Let's use PNG.
                      filename = f"{self.user_id}.png"
                      # Use absolute path based on bot's root if possible, otherwise relative
                      # Assuming 'assets' is at the same level as 'commands', 'services' etc.
                      base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__))) # Up two levels
                      save_dir = os.path.join(base_dir, 'assets', 'logos', str(self.guild_id))
                      os.makedirs(save_dir, exist_ok=True)
                      save_path = os.path.join(save_dir, filename)

                      # Save the image (potentially resizing/optimizing first)
                      img.save(save_path, 'PNG') # Save as PNG
                      logger.info(f"Saved capper logo to {save_path}")
                      db_path = os.path.relpath(save_path, base_dir) # Store relative path in DB

            except requests.exceptions.RequestException as req_err:
                 logger.error(f"Failed to download image from URL {image_url}: {req_err}")
                 await interaction.followup.send("❌ Failed to download image from URL. Check the link.", ephemeral=True)
                 return
            except IOError as img_err: # Catch Pillow errors
                 logger.error(f"Failed to process image from URL {image_url}: {img_err}")
                 await interaction.followup.send("❌ Could not process the image file from the URL.", ephemeral=True)
                 return
            except Exception as proc_err: # Catch other potential errors
                 logger.exception(f"Error processing image from {image_url}: {proc_err}")
                 await interaction.followup.send("❌ An error occurred while processing the image.", ephemeral=True)
                 return
            # --- End Image Processing ---


            # Update database using shared db_manager
            update_status = await self.db.execute(
                """
                UPDATE cappers
                SET image_path = %s, updated_at = UTC_TIMESTAMP()
                WHERE guild_id = %s AND user_id = %s
                """,
                db_path, self.guild_id, self.user_id
            )

            if update_status and 'UPDATE 1' in update_status:
                await interaction.followup.send(
                    "✅ Profile picture updated successfully!",
                    ephemeral=True
                )
            else:
                 await interaction.followup.send(
                      "⚠️ Profile picture saved, but failed to update database record.",
                      ephemeral=True
                 )

        except Exception as e:
            logger.exception(f"Error processing image URL modal: {e}")
            # Check if response already sent before sending followup
            if not interaction.response.is_done():
                 await interaction.response.send_message("❌ An error occurred.", ephemeral=True)
            else:
                 await interaction.followup.send("❌ An error occurred processing the image URL.", ephemeral=True)

    async def on_error(self, interaction: Interaction, error: Exception) -> None:
         logger.error(f"Error in ImageURLModal: {error}", exc_info=True)
         if not interaction.response.is_done():
              await interaction.response.send_message('❌ An error occurred with the URL modal.', ephemeral=True)
         else:
              await interaction.followup.send('❌ An error occurred with the URL modal.', ephemeral=True)


# --- Cog Definition ---
class SetIDCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # Access db_manager via self.bot assuming it's attached in main.py
        self.db_manager = bot.db_manager

    @app_commands.command(name="setid", description="Set your capper ID and display name.")
    @require_registered_guild()
    async def setid(self, interaction: Interaction):
        """Show the capper profile setup modal."""
        modal = CapperModal(target_user=interaction.user, db_manager=self.db_manager)
        await interaction.response.send_modal(modal)

# The setup function for the extension
async def setup(bot: commands.Bot):
    await bot.add_cog(SetIDCog(bot))
    logger.info("SetIDCog loaded")
