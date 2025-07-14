import logging
from typing import Dict, List
from PIL import Image, ImageDraw, ImageFont
import os
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch
import numpy as np
from io import BytesIO
import seaborn as sns
from matplotlib.colors import LinearSegmentedColormap

logger = logging.getLogger(__name__)

class StatsImageGenerator:
    def __init__(self):
        self.font_path = os.path.join(os.path.dirname(__file__), '..', 'static', 'fonts', 'arial.ttf')
        self.background_path = os.path.join(os.path.dirname(__file__), '..', 'static', 'images', 'stats_bg.png')
        
        # Create directories if they don't exist
        os.makedirs(os.path.dirname(self.font_path), exist_ok=True)
        os.makedirs(os.path.dirname(self.background_path), exist_ok=True)
        
        # Set matplotlib style for better looking charts
        plt.style.use('dark_background')
        sns.set_palette("husl")

    async def generate_capper_stats_image(self, stats: Dict, username: str, profile_image_url: str = None) -> Image.Image:
        """Generate a flashy stats image with charts and graphs."""
        try:
            # Create figure with dark theme
            fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(20, 14))
            fig.patch.set_facecolor('#1a1a1a')
            
            # Load profile image if available (make it large for top left)
            profile_img = None
            if profile_image_url:
                try:
                    import os
                    local_path = profile_image_url
                    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                    if profile_image_url.startswith('/static/'):
                        local_path = os.path.join(base_dir, *profile_image_url.lstrip('/').split('/'))
                    elif not os.path.isabs(local_path):
                        local_path = os.path.join(base_dir, local_path)
                    print(f"[DEBUG] Trying profile image local_path: {local_path}")
                    print(f"[DEBUG] File exists: {os.path.exists(local_path)}")
                    if os.path.exists(local_path):
                        profile_img = Image.open(local_path).convert("RGBA")
                        profile_img.thumbnail((500, 500), Image.Resampling.LANCZOS)
                        logger.info(f"Loaded profile image from local path: {local_path}")
                    elif profile_image_url.startswith('http://') or profile_image_url.startswith('https://'):
                        import requests
                        response = requests.get(profile_image_url, timeout=10)
                        if response.status_code == 200:
                            profile_img = Image.open(BytesIO(response.content)).convert("RGBA")
                            profile_img.thumbnail((500, 500), Image.Resampling.LANCZOS)
                            logger.info(f"Loaded profile image from URL: {profile_image_url}")
                except Exception as e:
                    logger.warning(f"Failed to load profile image from {profile_image_url}: {e}")

            # Fallback: If no user profile image, try server's default image
            if profile_img is None and stats.get('guild_id'):
                try:
                    guild_id = str(stats['guild_id'])
                    default_path = os.path.join(base_dir, 'static', 'guilds', guild_id, 'default_image.png')
                    print(f"[DEBUG] Trying guild default image: {default_path}")
                    print(f"[DEBUG] Guild default exists: {os.path.exists(default_path)}")
                    if os.path.exists(default_path):
                        profile_img = Image.open(default_path).convert("RGBA")
                        profile_img.thumbnail((500, 500), Image.Resampling.LANCZOS)
                        logger.info(f"Loaded guild default image from: {default_path}")
                except Exception as e:
                    logger.warning(f"Failed to load guild default image: {e}")

            # Extract stats (must be before any chart code that uses them)
            total_bets = int(stats.get('total_bets', 0) or 0)
            wins = int(stats.get('wins', 0) or 0)
            losses = int(stats.get('losses', 0) or 0)
            pushes = int(stats.get('pushes', 0) or 0)
            win_rate = float(stats.get('win_rate', 0) or 0.0)
            net_units = float(stats.get('net_units', 0) or 0.0)
            roi = float(stats.get('roi', 0) or 0.0)

            # --- Flashy Background ---
            # Create a gradient background for the figure
            gradient = np.linspace(0, 1, 256)
            gradient = np.vstack((gradient, gradient))
            cmap = LinearSegmentedColormap.from_list("custom", ["#232526", "#414345", "#232526"])
            fig.figimage(cmap(gradient), xo=0, yo=0, alpha=0.5, zorder=0)

            # 1. Profile Image (top left)
            ax1.axis('off')
            if profile_img is not None:
                # Add a glow effect
                from PIL import ImageFilter
                glow = profile_img.copy().resize((520, 520)).filter(ImageFilter.GaussianBlur(18)).convert("RGBA")
                ax1.imshow(glow, extent=[-0.1, 1.1, -0.1, 1.1], alpha=0.5, zorder=1)
                ax1.imshow(profile_img, zorder=2)
                ax1.set_title(f"{username}", color='#00ffe7', fontsize=36, fontweight='bold', pad=30)
            else:
                ax1.text(0.5, 0.5, f"{username}\n(No Profile Image)", ha='center', va='center', color='#00ffe7', fontsize=28, fontweight='bold', transform=ax1.transAxes)
                ax1.set_title(f"{username}", color='#00ffe7', fontsize=36, fontweight='bold', pad=30)

            # 2. Performance Metrics (top right)
            metrics = ['Win Rate', 'ROI', 'Net Units']
            values = [win_rate, roi, net_units]
            colors_metrics = ['#00ff88' if v >= 0 else '#ff4444' for v in values]
            bars = ax2.bar(metrics, values, color=colors_metrics, alpha=0.9, edgecolor='white', linewidth=3, zorder=3)
            ax2.set_title('Performance Metrics', color='#00ffe7', fontsize=22, fontweight='bold')
            ax2.set_ylabel('Value', color='white', fontsize=14)
            ax2.tick_params(colors='white', labelsize=12)
            for bar, value in zip(bars, values):
                height = bar.get_height()
                ax2.text(bar.get_x() + bar.get_width()/2., height + (0.01 * max(values)),
                        f'{value:.1f}', ha='center', va='bottom', color='white', fontweight='bold', fontsize=16)
            ax2.grid(axis='y', alpha=0.2)

            # 3. Bet Distribution Pie Chart (bottom left)
            if total_bets > 0:
                labels = ['Wins', 'Losses', 'Pushes'] if pushes > 0 else ['Wins', 'Losses']
                sizes = [wins, losses, pushes] if pushes > 0 else [wins, losses]
                colors = ['#00ff88', '#ff4444', '#ffaa00'] if pushes > 0 else ['#00ff88', '#ff4444']
                wedges, texts, autotexts = ax3.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90, textprops={'color':'white', 'fontsize':16}, wedgeprops={'linewidth':2, 'edgecolor':'white'})
                ax3.set_title('Bet Distribution', color='#00ffe7', fontsize=22, fontweight='bold')
            else:
                ax3.text(0.5, 0.5, 'No bets yet', ha='center', va='center', transform=ax3.transAxes, color='#00ffe7', fontsize=18)
                ax3.set_title('Bet Distribution', color='#00ffe7', fontsize=22, fontweight='bold')

            # 4. Summary Stats (bottom right)
            ax4.axis('off')
            summary_lines = [
                f"{username}'s Stats Summary",
                "",
                f"Total Bets: {total_bets}",
                f"Wins: {wins}",
                f"Losses: {losses}",
                f"Pushes: {pushes}",
                "",
                f"Win Rate: {win_rate:.1f}%",
                f"Net Units: {net_units:.2f}",
                f"ROI: {roi:.1f}%"
            ]
            summary_text = "\n".join(summary_lines)
            bbox_props = dict(boxstyle="round,pad=1.0", facecolor='#111', alpha=0.95, edgecolor='#00ffe7', linewidth=3)
            ax4.text(
                0.5, 0.5, summary_text,
                ha='center', va='center',
                fontsize=24, color='#ffffff',
                fontweight='bold',
                bbox=bbox_props,
                transform=ax4.transAxes
            )

            # Adjust layout
            plt.tight_layout(pad=3.0)
            
            # Convert matplotlib figure to PIL Image
            buf = BytesIO()
            plt.savefig(buf, format='png', dpi=150, bbox_inches='tight', 
                       facecolor='#1a1a1a', edgecolor='none')
            buf.seek(0)
            
            # Convert to PIL Image
            img = Image.open(buf)
            img = img.convert('RGB')
            
            plt.close()  # Close the matplotlib figure to free memory
            
            return img
            
        except Exception as e:
            logger.error(f"Error generating capper stats image: {str(e)}")
            # Fallback to simple image if matplotlib fails
            return self._generate_fallback_image(stats, username)

    def _generate_fallback_image(self, stats: Dict, username: str) -> Image.Image:
        """Fallback image generation if matplotlib fails."""
        try:
            img = Image.new('RGB', (800, 600), color='#1a1a1a')
            draw = ImageDraw.Draw(img)

            # Load font
            try:
                font = ImageFont.truetype(self.font_path, 24)
                title_font = ImageFont.truetype(self.font_path, 32)
            except IOError:
                font = ImageFont.load_default()
                title_font = ImageFont.load_default()

            # Draw title
            title_text = f"{username}'s Stats"
            draw.text((400, 50), title_text, fill='white', font=title_font, anchor="mm")

            # Draw stats
            y = 150
            stats_text = [
                f"Total Bets: {stats.get('total_bets', 0)}",
                f"Wins: {stats.get('wins', 0)}",
                f"Losses: {stats.get('losses', 0)}",
                f"Pushes: {stats.get('pushes', 0)}",
                f"Win Rate: {stats.get('win_rate', 0):.1f}%",
                f"Net Units: {stats.get('net_units', 0):.2f}",
                f"ROI: {stats.get('roi', 0):.1f}%"
            ]

            for text in stats_text:
                draw.text((400, y), text, fill='white', font=font, anchor="mm")
                y += 50

            return img
        except Exception as e:
            logger.error(f"Error generating fallback image: {str(e)}")
            raise

    def generate_guild_stats_image(self, stats: Dict) -> Image.Image:
        """Generate a flashy guild stats image with charts."""
        try:
            # Create figure with dark theme
            fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
            fig.patch.set_facecolor('#1a1a1a')
            
            # Extract stats
            total_bets = int(stats.get('total_bets', 0) or 0)
            total_cappers = int(stats.get('total_cappers', 0) or 0)
            total_units = float(stats.get('total_units', 0) or 0.0)
            net_units = float(stats.get('net_units', 0) or 0.0)

            # 1. Guild Overview (top left)
            overview_data = ['Total Bets', 'Total Cappers', 'Total Units']
            overview_values = [total_bets, total_cappers, total_units]
            colors_overview = ['#00ff88', '#0088ff', '#ff8800']
            
            bars = ax1.bar(overview_data, overview_values, color=colors_overview, alpha=0.8, edgecolor='white', linewidth=2)
            ax1.set_title('Guild Overview', color='white', fontsize=16, fontweight='bold')
            ax1.set_ylabel('Count', color='white')
            ax1.tick_params(colors='white')
            
            # Add value labels
            for bar, value in zip(bars, overview_values):
                height = bar.get_height()
                ax1.text(bar.get_x() + bar.get_width()/2., height + (0.01 * max(overview_values)),
                        str(value), ha='center', va='bottom', color='white', fontweight='bold')

            # 2. Net Units Performance (top right)
            ax2.bar(['Net Units'], [net_units], color='#00ff88' if net_units >= 0 else '#ff4444', 
                   alpha=0.8, edgecolor='white', linewidth=2)
            ax2.set_title('Net Units Performance', color='white', fontsize=16, fontweight='bold')
            ax2.set_ylabel('Units', color='white')
            ax2.tick_params(colors='white')
            ax2.text(0, net_units + (0.01 * abs(net_units) if net_units != 0 else 1),
                    f'{net_units:.2f}', ha='center', va='bottom', color='white', fontweight='bold')

            # 3. Activity Distribution (bottom left)
            if total_bets > 0:
                activity_data = ['Bets', 'Cappers']
                activity_values = [total_bets, total_cappers]
                ax3.pie(activity_values, labels=activity_data, autopct='%1.1f%%', 
                       colors=['#00ff88', '#0088ff'], startangle=90)
                ax3.set_title('Activity Distribution', color='white', fontsize=16, fontweight='bold')
            else:
                ax3.text(0.5, 0.5, 'No activity yet', ha='center', va='center', transform=ax3.transAxes, 
                        color='white', fontsize=14)
                ax3.set_title('Activity Distribution', color='white', fontsize=16, fontweight='bold')

            # 4. Summary Stats (bottom right)
            ax4.axis('off')
            summary_text = f"""
            🏆 Guild Stats Summary
            
            📊 Total Bets: {total_bets}
            👥 Total Cappers: {total_cappers}
            💰 Total Units Wagered: {total_units:.2f}
            📈 Net Units: {net_units:.2f}
            
            🎯 Average Bets per Capper: {total_bets/total_cappers:.1f if total_cappers > 0 else 0}
            """
            
            ax4.text(0.5, 0.5, summary_text, ha='center', va='center', transform=ax4.transAxes,
                    color='white', fontsize=12, fontweight='bold',
                    bbox=dict(boxstyle="round,pad=0.3", facecolor='#2a2a2a', alpha=0.8))

            # Adjust layout
            plt.tight_layout(pad=3.0)
            
            # Convert to PIL Image
            buf = BytesIO()
            plt.savefig(buf, format='png', dpi=150, bbox_inches='tight', 
                       facecolor='#1a1a1a', edgecolor='none')
            buf.seek(0)
            
            img = Image.open(buf)
            img = img.convert('RGB')
            
            plt.close()
            
            return img
            
        except Exception as e:
            logger.error(f"Error generating guild stats image: {str(e)}")
            return self._generate_fallback_guild_image(stats)

    def _generate_fallback_guild_image(self, stats: Dict) -> Image.Image:
        """Fallback guild image generation."""
        try:
            img = Image.new('RGB', (800, 600), color='#1a1a1a')
            draw = ImageDraw.Draw(img)

            try:
                font = ImageFont.truetype(self.font_path, 24)
                title_font = ImageFont.truetype(self.font_path, 32)
            except IOError:
                font = ImageFont.load_default()
                title_font = ImageFont.load_default()

            draw.text((400, 50), "Guild Stats", fill='white', font=title_font, anchor="mm")

            y = 150
            stats_text = [
                f"Total Bets: {stats.get('total_bets', 0)}",
                f"Total Cappers: {stats.get('total_cappers', 0)}",
                f"Total Units Wagered: {stats.get('total_units', 0)}",
                f"Net Units: {stats.get('net_units', 0)}"
            ]

            for text in stats_text:
                draw.text((400, y), text, fill='white', font=font, anchor="mm")
                y += 50

            return img
        except Exception as e:
            logger.error(f"Error generating fallback guild image: {str(e)}")
            raise

    def generate_top_cappers_image(self, cappers: List[Dict]) -> Image.Image:
        """Generate a flashy top cappers leaderboard image."""
        try:
            # Create figure with dark theme
            fig, ax = plt.subplots(1, 1, figsize=(16, 10))
            fig.patch.set_facecolor('#1a1a1a')
            
            if not cappers:
                ax.text(0.5, 0.5, 'No cappers data available', ha='center', va='center', 
                       transform=ax.transAxes, color='white', fontsize=16)
                ax.set_title('Top Cappers', color='white', fontsize=20, fontweight='bold')
            else:
                # Extract data
                names = [capper.get('username', f"User {capper['user_id']}") for capper in cappers]
                net_units = [float(capper.get('net_units', 0) or 0.0) for capper in cappers]
                
                # Create horizontal bar chart
                colors = ['#00ff88' if units >= 0 else '#ff4444' for units in net_units]
                bars = ax.barh(names, net_units, color=colors, alpha=0.8, edgecolor='white', linewidth=2)
                
                ax.set_title('Top Cappers by Net Units', color='white', fontsize=20, fontweight='bold')
                ax.set_xlabel('Net Units', color='white', fontsize=14)
                ax.tick_params(colors='white')
                
                # Add value labels on bars
                for bar, units in zip(bars, net_units):
                    width = bar.get_width()
                    ax.text(width + (0.01 * max(abs(min(net_units)), max(net_units))), 
                           bar.get_y() + bar.get_height()/2., f'{units:.2f}', 
                           ha='left', va='center', color='white', fontweight='bold')

            plt.tight_layout(pad=3.0)
            
            # Convert to PIL Image
            buf = BytesIO()
            plt.savefig(buf, format='png', dpi=150, bbox_inches='tight', 
                       facecolor='#1a1a1a', edgecolor='none')
            buf.seek(0)
            
            img = Image.open(buf)
            img = img.convert('RGB')
            
            plt.close()
            
            return img
            
        except Exception as e:
            logger.error(f"Error generating top cappers image: {str(e)}")
            return self._generate_fallback_top_cappers_image(cappers)

    def _generate_fallback_top_cappers_image(self, cappers: List[Dict]) -> Image.Image:
        """Fallback top cappers image generation."""
        try:
            img = Image.new('RGB', (800, 600), color='#1a1a1a')
            draw = ImageDraw.Draw(img)

            try:
                font = ImageFont.truetype(self.font_path, 24)
                title_font = ImageFont.truetype(self.font_path, 32)
            except IOError:
                font = ImageFont.load_default()
                title_font = ImageFont.load_default()

            draw.text((400, 50), "Top Cappers", fill='white', font=title_font, anchor="mm")

            y = 150
            for capper in cappers:
                text = f"User ID: {capper['user_id']} - Net Units: {capper['net_units']}"
                draw.text((400, y), text, fill='white', font=font, anchor="mm")
                y += 50

            return img
        except Exception as e:
            logger.error(f"Error generating fallback top cappers image: {str(e)}")
            raise 