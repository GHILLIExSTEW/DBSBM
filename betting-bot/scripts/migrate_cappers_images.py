import asyncio
import os
import shutil
import sys

import requests

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from data.db_manager import DatabaseManager


async def migrate_cappers_images():
    db = DatabaseManager()
    await db.connect()
    cappers = await db.fetch_all(
        "SELECT guild_id, user_id, image_path FROM cappers WHERE image_path IS NOT NULL AND image_path != ''"
    )
    for capper in cappers:
        guild_id = str(capper["guild_id"])
        user_id = str(capper["user_id"])
        old_path = capper["image_path"]
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        new_dir = os.path.join(base_dir, "static", "guilds", guild_id, "users")
        os.makedirs(new_dir, exist_ok=True)
        new_abs_path = os.path.join(new_dir, f"{user_id}.png")
        new_url = f"/static/guilds/{guild_id}/users/{user_id}.png"
        try:
            if old_path.startswith("http://") or old_path.startswith("https://"):
                # Download the image from the URL
                try:
                    response = requests.get(old_path, timeout=15, stream=True)
                    response.raise_for_status()
                    with open(new_abs_path, "wb") as f:
                        for chunk in response.iter_content(1024):
                            f.write(chunk)
                    print(f"Downloaded {old_path} -> {new_abs_path}")
                    await db.execute(
                        "UPDATE cappers SET image_path = %s WHERE guild_id = %s AND user_id = %s",
                        new_url,
                        guild_id,
                        user_id,
                    )
                    print(f"Updated DB for guild {guild_id}, user {user_id}")
                except Exception as e:
                    print(
                        f"Error downloading image for guild {guild_id}, user {user_id}: {e}"
                    )
            else:
                # Local file path
                if old_path.startswith("/"):
                    old_abs_path = os.path.join(base_dir, old_path.lstrip("/"))
                else:
                    old_abs_path = os.path.join(base_dir, old_path)
                if os.path.exists(old_abs_path):
                    shutil.copy2(old_abs_path, new_abs_path)
                    print(f"Copied {old_abs_path} -> {new_abs_path}")
                    await db.execute(
                        "UPDATE cappers SET image_path = %s WHERE guild_id = %s AND user_id = %s",
                        new_url,
                        guild_id,
                        user_id,
                    )
                    print(f"Updated DB for guild {guild_id}, user {user_id}")
                else:
                    print(f"Old image not found: {old_abs_path}")
        except Exception as e:
            print(f"Error migrating image for guild {guild_id}, user {user_id}: {e}")
    await db.close()


if __name__ == "__main__":
    asyncio.run(migrate_cappers_images())
