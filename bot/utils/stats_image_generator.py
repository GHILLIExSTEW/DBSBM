import logging
import os
import os
from io import BytesIO
from typing import Dict, List, Optional

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from matplotlib.colors import LinearSegmentedColormap
from PIL import Image, ImageDraw, ImageFont
from matplotlib.backends.backend_agg import FigureCanvas

logger = logging.getLogger(__name__)


def make_rounded_feathered(img):
    size = img.size[0]
    mask = Image.new("L", (size, size), 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0, size, size), fill=255)
    result = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    result.paste(img, (0, 0), mask)
    return result


class StatsImageGenerator:
    def __init__(self):
        static_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'StaticFiles', 'static'))
        self.font_path = os.path.join(static_dir, "fonts", "arial.ttf")
        self.background_path = os.path.join(static_dir, "images", "stats_bg.webp")

        # Create directories if they don't exist
        os.makedirs(os.path.dirname(self.font_path), exist_ok=True)
        os.makedirs(os.path.dirname(self.background_path), exist_ok=True)

        # Set matplotlib style for better looking charts
        plt.style.use("dark_background")
        sns.set_palette("husl")

    def generate_guild_stats_image(self, stats: Dict) -> Image.Image:
        """Generate a visually rich stats image for the guild/server."""
        try:
            # Extract stats
            total_bets = int(stats.get("total_bets", 0) or 0)
            total_cappers = int(stats.get("total_cappers", 0) or 0)
            total_units = float(stats.get("total_units", 0) or 0.0)
            net_units = float(stats.get("net_units", 0) or 0.0)
            wins = int(stats.get("wins", 0) or 0)
            losses = int(stats.get("losses", 0) or 0)
            pushes = int(stats.get("pushes", 0) or 0)

            # Build leaderboard if not provided
            leaderboard = stats.get("leaderboard", [])
            if not leaderboard or len(leaderboard) == 0:
                # Try to build from user_stats if available
                user_stats = stats.get("user_stats", [])
                if user_stats and isinstance(user_stats, list):
                    leaderboard = []
                    for u in user_stats:
                        # Use net_units if present, else calculate from bet_won and bet_loss
                        if u.get("net_units") is not None:
                            net_units = float(u.get("net_units", 0) or 0.0)
                        else:
                            net_units = float(u.get("bet_won", 0) or 0.0) - float(
                                u.get("bet_loss", 0) or 0.0
                            )
                        leaderboard.append(
                            {
                                "username": u.get("display_name")
                                or u.get("username")
                                or str(u.get("user_id", "?")),
                                "net_units": net_units,
                            }
                        )
                    leaderboard = sorted(
                        leaderboard, key=lambda x: x["net_units"], reverse=True
                    )[:8]

            # Create multi-panel figure
            fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(20, 14))
            fig.patch.set_facecolor("#1a1a1a")

            # 1. Leaderboard (Top Left)
            ax1.set_facecolor("#232b3b")
            if leaderboard and len(leaderboard) > 0:
                names = [
                    c.get("username", f"User {c.get('user_id','?')}")
                    for c in leaderboard[:8]
                ]
                units = [float(c.get("net_units", 0) or 0.0) for c in leaderboard[:8]]
                colors = ["#00ff88" if u >= 0 else "#ff4444" for u in units]
                bars = ax1.barh(
                    names,
                    units,
                    color=colors,
                    alpha=0.85,
                    edgecolor="white",
                    linewidth=2,
                )
                ax1.set_title(
                    "Leaderboard (Top 8 by Net Units)",
                    color="#00ffe7",
                    fontsize=24,
                    fontweight="bold",
                )
                for bar, value in zip(bars, units):
                    ax1.text(
                        bar.get_width() + 0.1,
                        bar.get_y() + bar.get_height() / 2.0,
                        f"{value:.2f}",
                        ha="left",
                        va="center",
                        color="white",
                        fontweight="bold",
                        fontsize=16,
                    )
                ax1.tick_params(colors="white", labelsize=14)
            else:
                ax1.text(
                    0.5,
                    0.5,
                    "No leaderboard data",
                    ha="center",
                    va="center",
                    color="white",
                    fontsize=18,
                    transform=ax1.transAxes,
                )
                ax1.set_title(
                    "Leaderboard", color="#00ffe7", fontsize=24, fontweight="bold"
                )
            ax1.spines[:].set_color("white")

            # 2. Pie Chart (Top Right) - Win/Loss/Push
            ax2.set_facecolor("#232b3b")
            pie_labels = []
            pie_values = []
            pie_colors = []
            if wins > 0:
                pie_labels.append("Wins")
                pie_values.append(wins)
                pie_colors.append("#00ff88")
            if losses > 0:
                pie_labels.append("Losses")
                pie_values.append(losses)
                pie_colors.append("#ff4444")
            if pushes > 0:
                pie_labels.append("Pushes")
                pie_values.append(pushes)
                pie_colors.append("#ffaa00")
            if sum(pie_values) > 0:
                wedges, texts, autotexts = ax2.pie(
                    pie_values,
                    labels=pie_labels,
                    colors=pie_colors,
                    autopct="%1.1f%%",
                    startangle=90,
                    textprops={"color": "white", "fontsize": 16},
                    wedgeprops={"linewidth": 2, "edgecolor": "white"},
                )
                ax2.set_title(
                    "Win/Loss/Push Distribution",
                    color="#00ffe7",
                    fontsize=22,
                    fontweight="bold",
                )
            else:
                ax2.text(
                    0.5,
                    0.5,
                    "No win/loss data",
                    ha="center",
                    va="center",
                    color="#00ffe7",
                    fontsize=18,
                    transform=ax2.transAxes,
                )
                ax2.set_title(
                    "Win/Loss/Push Distribution",
                    color="#00ffe7",
                    fontsize=22,
                    fontweight="bold",
                )
            ax2.spines[:].set_color("white")

            # 3. Bar Chart (Bottom Left) - Bets & Units
            ax3.set_facecolor("#232b3b")
            bar_labels = ["Total Bets", "Total Cappers", "Total Units"]
            bar_values = [total_bets, total_cappers, total_units]
            bar_colors = ["#2196f3", "#ff9800", "#4caf50"]
            bars = ax3.bar(
                bar_labels,
                bar_values,
                color=bar_colors,
                alpha=0.85,
                edgecolor="white",
                linewidth=2,
            )
            for bar, value in zip(bars, bar_values):
                ax3.text(
                    bar.get_x() + bar.get_width() / 2.0,
                    value + 0.1,
                    str(value),
                    ha="center",
                    va="bottom",
                    color="white",
                    fontweight="bold",
                    fontsize=16,
                )
            ax3.set_title(
                "Server Overview", color="#00ffe7", fontsize=22, fontweight="bold"
            )
            ax3.tick_params(colors="white", labelsize=14)
            ax3.spines[:].set_color("white")

            # 4. Summary Box (Bottom Right)
            ax4.axis("off")
            summary_lines = [
                "Server Stats Summary",
                "",
                f"Total Bets: {total_bets}",
                f"Total Cappers: {total_cappers}",
                f"Total Units Wagered: {total_units}",
                f"Net Units: {net_units}",
            ]
            summary_text = "\n".join(summary_lines)
            bbox_props = dict(
                boxstyle="round,pad=1.0",
                facecolor="#111",
                alpha=0.95,
                edgecolor="#00ffe7",
                linewidth=3,
            )
            ax4.text(
                0.5,
                0.5,
                summary_text,
                ha="center",
                va="center",
                fontsize=28,
                color="#ffffff",
                fontweight="bold",
                bbox=bbox_props,
                transform=ax4.transAxes,
            )

            plt.tight_layout(pad=3.0)
            buf = BytesIO()
            plt.savefig(
                buf,
                format="png",
                dpi=150,
                bbox_inches="tight",
                facecolor="#1a1a1a",
                edgecolor="none",
            )
            buf.seek(0)
            img = Image.open(buf)
            img = img.convert("RGB")
            plt.close()
            return img
        except Exception as e:
            logger.error(f"Error generating guild stats image: {str(e)}")
            return self._generate_fallback_guild_image(stats)

    def _load_profile_image(
        self, profile_image_url: str, stats: Dict
    ) -> Optional[Image.Image]:
        """Load profile image from various sources with fallbacks."""
        import os
        from io import BytesIO
        import requests

        # base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        # Try to load from provided URL/path
        if profile_image_url:
            try:
                local_path = profile_image_url
                if profile_image_url.startswith("/static/"):
                    local_path = os.path.join(static_dir, *profile_image_url.lstrip("/static/").split("/"))
                elif not os.path.isabs(local_path):
                    local_path = os.path.join(static_dir, local_path)

                if os.path.exists(local_path):
                    profile_img = Image.open(local_path).convert("RGBA")
                    profile_img.thumbnail((500, 500), Image.Resampling.LANCZOS)
                    logger.info(f"Loaded profile image from local path: {local_path}")
                    return profile_img
                elif profile_image_url.startswith(
                    "http://"
                ) or profile_image_url.startswith("https://"):
                    response = requests.get(profile_image_url, timeout=10)
                    if response.status_code == 200:
                        profile_img = Image.open(BytesIO(response.content)).convert(
                            "RGBA"
                        )
                        profile_img.thumbnail((500, 500), Image.Resampling.LANCZOS)
                        logger.info(
                            f"Loaded profile image from URL: {profile_image_url}"
                        )
                        return profile_img
            except Exception as e:
                logger.warning(
                    f"Failed to load profile image from {profile_image_url}: {e}"
                )

        # Fallback: Try guild default image
        if stats.get("guild_id"):
            try:
                guild_id = str(stats["guild_id"])
                default_path = os.path.join(static_dir, "guilds", guild_id, "default_image.webp")
                if os.path.exists(default_path):
                    profile_img = Image.open(default_path).convert("RGBA")
                    profile_img.thumbnail((500, 500), Image.Resampling.LANCZOS)
                    logger.info(f"Loaded guild default image from: {default_path}")
                    return profile_img
                else:
                    # Try alternative default image names
                    alt_names = ["default_logo.webp", "logo.webp", "guild_logo.webp"]
                    for alt_name in alt_names:
                        alt_path = os.path.join(static_dir, "guilds", guild_id, alt_name)
                        if os.path.exists(alt_path):
                            profile_img = Image.open(alt_path).convert("RGBA")
                            profile_img.thumbnail((500, 500), Image.Resampling.LANCZOS)
                            logger.info(f"Loaded guild default image from: {alt_path}")
                            return profile_img
            except Exception as e:
                logger.warning(f"Failed to load guild default image: {e}")

        # Final fallback: Try generic default images
        try:
            generic_paths = [
                os.path.join(static_dir, "images", "default_user.webp"),
                os.path.join(static_dir, "images", "default_avatar.webp"),
                os.path.join(static_dir, "default_logo.webp"),
                os.path.join(static_dir, "images", "default_image.webp"),
            ]

            for generic_path in generic_paths:
                if os.path.exists(generic_path):
                    profile_img = Image.open(generic_path).convert("RGBA")
                    profile_img.thumbnail((500, 500), Image.Resampling.LANCZOS)
                    logger.info(f"Loaded generic default image from: {generic_path}")
                    return profile_img
        except Exception as e:
            logger.warning(f"Failed to load generic default image: {e}")

        return None

    def _create_stats_charts(self, fig, ax1, ax2, ax3, ax4, stats: Dict):
        """Create the statistical charts for the stats image."""
        # Chart 1: Win/Loss Ratio
        wins = stats.get("wins", 0)
        losses = stats.get("losses", 0)
        total_bets = wins + losses

        if total_bets > 0:
            win_rate = (wins / total_bets) * 100
            ax1.pie(
                [wins, losses],
                labels=["Wins", "Losses"],
                colors=["#00ff00", "#ff0000"],
                autopct="%1.1f%%",
            )
            ax1.set_title(
                "Win/Loss Ratio", color="white", fontsize=14, fontweight="bold"
            )
        else:
            ax1.text(
                0.5,
                0.5,
                "No bets yet",
                ha="center",
                va="center",
                transform=ax1.transAxes,
                color="white",
                fontsize=12,
            )
            ax1.set_title(
                "Win/Loss Ratio", color="white", fontsize=14, fontweight="bold"
            )

        # Chart 2: Monthly Performance
        monthly_stats = stats.get("monthly_stats", {})
        if monthly_stats:
            months = list(monthly_stats.keys())
            profits = [monthly_stats[month].get("profit", 0) for month in months]

            colors = ["#00ff00" if p >= 0 else "#ff0000" for p in profits]
            ax2.bar(months, profits, color=colors)
            ax2.set_title(
                "Monthly Performance", color="white", fontsize=14, fontweight="bold"
            )
            ax2.set_ylabel("Profit/Loss", color="white")
            ax2.tick_params(colors="white")
        else:
            ax2.text(
                0.5,
                0.5,
                "No monthly data",
                ha="center",
                va="center",
                transform=ax2.transAxes,
                color="white",
                fontsize=12,
            )
            ax2.set_title(
                "Monthly Performance", color="white", fontsize=14, fontweight="bold"
            )

        # Chart 3: Bet Type Distribution
        bet_types = stats.get("bet_types", {})
        if bet_types:
            types = list(bet_types.keys())
            counts = list(bet_types.values())
            ax3.pie(counts, labels=types, autopct="%1.1f%%")
            ax3.set_title(
                "Bet Type Distribution", color="white", fontsize=14, fontweight="bold"
            )
        else:
            ax3.text(
                0.5,
                0.5,
                "No bet type data",
                ha="center",
                va="center",
                transform=ax3.transAxes,
                color="white",
                fontsize=12,
            )
            ax3.set_title(
                "Bet Type Distribution", color="white", fontsize=14, fontweight="bold"
            )

        # Chart 4: Profit Trend
        profit_history = stats.get("profit_history", [])
        if profit_history:
            ax4.plot(
                range(len(profit_history)), profit_history, color="#00ff00", linewidth=2
            )
            ax4.set_title("Profit Trend", color="white", fontsize=14, fontweight="bold")
            ax4.set_ylabel("Profit", color="white")
            ax4.tick_params(colors="white")
        else:
            ax4.text(
                0.5,
                0.5,
                "No trend data",
                ha="center",
                va="center",
                transform=ax4.transAxes,
                color="white",
                fontsize=12,
            )
            ax4.set_title("Profit Trend", color="white", fontsize=14, fontweight="bold")

    def _add_profile_image_to_figure(self, fig, profile_img: Image.Image):
        """Add profile image to the figure."""
        if profile_img:
            # Convert PIL image to matplotlib format
            profile_array = np.array(profile_img)

            # Create a new axes for the profile image (top left)
            ax_profile = fig.add_axes([0.02, 0.85, 0.15, 0.15])
            ax_profile.imshow(profile_array)
            ax_profile.axis("off")

    def _add_stats_text(self, fig, stats: Dict, username: str):
        """Add statistical text information to the figure."""
        # Create text box for stats
        stats_text = f"""
Username: {username}
Total Bets: {stats.get('total_bets', 0)}
Wins: {stats.get('wins', 0)}
Losses: {stats.get('losses', 0)}
Win Rate: {(stats.get('wins', 0) / max(stats.get('total_bets', 1), 1) * 100):.1f}%
Total Profit: ${stats.get('total_profit', 0):.2f}
Average Bet Size: ${stats.get('avg_bet_size', 0):.2f}
Best Month: {stats.get('best_month', 'N/A')}
        """.strip()

        # Add text box
        fig.text(
            0.02,
            0.02,
            stats_text,
            fontsize=12,
            color="white",
            bbox=dict(boxstyle="round,pad=0.5", facecolor="#333333", alpha=0.8),
        )

    async def generate_capper_stats_image(
        self, stats: Dict, username: str, profile_image_url: str = None
    ) -> Image.Image:
        """Generate a flashy stats image with charts and graphs."""
        try:
            # Create figure with dark theme
            fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(20, 14))
            fig.patch.set_facecolor("#1a1a1a")

            # Load profile image
            profile_img = self._load_profile_image(profile_image_url, stats)

            # Create charts
            self._create_stats_charts(fig, ax1, ax2, ax3, ax4, stats)

            # Add profile image if available
            if profile_img:
                self._add_profile_image_to_figure(fig, profile_img)

            # Add stats text
            self._add_stats_text(fig, stats, username)

            # Convert matplotlib figure to PIL image
            canvas = FigureCanvas(fig)
            canvas.draw()

            # Get the RGBA buffer from the figure
            w, h = canvas.get_width_height()
            buf = np.frombuffer(canvas.tostring_rgb(), dtype=np.uint8)
            buf.shape = (h, w, 3)

            # Convert to PIL image
            img = Image.fromarray(buf)
            plt.close(fig)

            return img

        except Exception as e:
            logger.error(f"Error generating capper stats image: {e}")
            # Return a fallback image
            return self._generate_fallback_image(stats, username)

    def generate_top_cappers_image(self, cappers: List[Dict]) -> Image.Image:
        """Generate a flashy top cappers leaderboard image."""
        try:
            # Create figure with dark theme
            fig, ax = plt.subplots(1, 1, figsize=(16, 10))
            fig.patch.set_facecolor("#1a1a1a")

            if not cappers:
                ax.text(
                    0.5,
                    0.5,
                    "No cappers data available",
                    ha="center",
                    va="center",
                    transform=ax.transAxes,
                    color="white",
                    fontsize=16,
                )
                ax.set_title(
                    "Top Cappers", color="white", fontsize=20, fontweight="bold"
                )
            else:
                # Extract data
                names = [
                    capper.get("username", f"User {capper['user_id']}")
                    for capper in cappers
                ]
                net_units = [
                    float(capper.get("net_units", 0) or 0.0) for capper in cappers
                ]

                # Create horizontal bar chart
                colors = ["#00ff88" if units >= 0 else "#ff4444" for units in net_units]
                bars = ax.barh(
                    names,
                    net_units,
                    color=colors,
                    alpha=0.8,
                    edgecolor="white",
                    linewidth=2,
                )

                ax.set_title(
                    "Top Cappers by Net Units",
                    color="white",
                    fontsize=20,
                    fontweight="bold",
                )
                ax.set_xlabel("Net Units", color="white", fontsize=14)
                ax.tick_params(colors="white")

                # Add value labels on bars
                for bar, units in zip(bars, net_units):
                    width = bar.get_width()
                    ax.text(
                        width + (0.01 * max(abs(min(net_units)), max(net_units))),
                        bar.get_y() + bar.get_height() / 2.0,
                        f"{units:.2f}",
                        ha="left",
                        va="center",
                        color="white",
                        fontweight="bold",
                    )

            plt.tight_layout(pad=3.0)

            # Convert to PIL Image
            buf = BytesIO()
            plt.savefig(
                buf,
                format="png",
                dpi=150,
                bbox_inches="tight",
                facecolor="#1a1a1a",
                edgecolor="none",
            )
            buf.seek(0)

            img = Image.open(buf)
            img = img.convert("RGB")

            plt.close()

            return img

        except Exception as e:
            logger.error(f"Error generating top cappers image: {str(e)}")
            return self._generate_fallback_top_cappers_image(cappers)

    def _generate_fallback_top_cappers_image(self, cappers: List[Dict]) -> Image.Image:
        """Fallback top cappers image generation."""
        try:
            img = Image.new("RGB", (800, 600), color="#1a1a1a")
            draw = ImageDraw.Draw(img)

            try:
                font = ImageFont.truetype(self.font_path, 24)
                title_font = ImageFont.truetype(self.font_path, 32)
            except IOError:
                font = ImageFont.load_default()
                title_font = ImageFont.load_default()

            draw.text(
                (400, 50), "Top Cappers", fill="white", font=title_font, anchor="mm"
            )

            y = 150
            for capper in cappers:
                text = (
                    f"User ID: {capper['user_id']} - Net Units: {capper['net_units']}"
                )
                draw.text((400, y), text, fill="white", font=font, anchor="mm")
                y += 50

            return img
        except Exception as e:
            logger.error(f"Error generating fallback top cappers image: {str(e)}")
            raise

    def _generate_fallback_guild_image(self, stats: Dict) -> Image.Image:
        """Fallback guild image generation."""
        try:
            img = Image.new("RGB", (800, 600), color="#1a1a1a")
            draw = ImageDraw.Draw(img)

            try:
                font = ImageFont.truetype(self.font_path, 24)
                title_font = ImageFont.truetype(self.font_path, 32)
            except IOError:
                font = ImageFont.load_default()
                title_font = ImageFont.load_default()

            draw.text(
                (400, 50), "Guild Stats", fill="white", font=title_font, anchor="mm"
            )

            y = 150
            stats_text = [
                f"Total Bets: {stats.get('total_bets', 0)}",
                f"Total Cappers: {stats.get('total_cappers', 0)}",
                f"Total Units Wagered: {stats.get('total_units', 0)}",
                f"Net Units: {stats.get('net_units', 0)}",
            ]

            for text in stats_text:
                draw.text((400, y), text, fill="white", font=font, anchor="mm")
                y += 50

            return img
        except Exception as e:
            logger.error(f"Error generating fallback guild image: {str(e)}")
            raise

    def _generate_fallback_image(self, stats: Dict, username: str) -> Image.Image:
        """Fallback image generation for capper stats."""
        try:
            img = Image.new("RGB", (800, 600), color="#1a1a1a")
            draw = ImageDraw.Draw(img)

            try:
                font = ImageFont.truetype(self.font_path, 24)
                title_font = ImageFont.truetype(self.font_path, 32)
            except IOError:
                font = ImageFont.load_default()
                title_font = ImageFont.load_default()

            draw.text(
                (400, 50),
                f"{username}'s Stats",
                fill="white",
                font=title_font,
                anchor="mm",
            )

            y = 150
            stats_text = [
                f"Total Bets: {stats.get('total_bets', 0)}",
                f"Wins: {stats.get('wins', 0)}",
                f"Losses: {stats.get('losses', 0)}",
                f"Pushes: {stats.get('pushes', 0)}",
                "",
                f"Win Rate: {stats.get('win_rate', 0):.1f}%",
                f"Net Units: {stats.get('net_units', 0):.2f}",
                f"ROI: {stats.get('roi', 0):.1f}%",
            ]

            for text in stats_text:
                draw.text((400, y), text, fill="white", font=font, anchor="mm")
                y += 50

            return img
        except Exception as e:
            logger.error(f"Error generating fallback image: {str(e)}")
            raise
