#!/usr/bin/env python3
"""
Clean up the cappers table structure
"""

import asyncio
import os
import sys
from dotenv import load_dotenv

# Add the current directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data.db_manager import DatabaseManager


async def clean_cappers_table():
    """Clean up the cappers table structure"""
    print("Cleaning up cappers table structure...")

    # Load environment variables
    load_dotenv()

    # Create database manager
    db_manager = DatabaseManager()

    try:
        # Connect to database
        pool = await db_manager.connect()
        if not pool:
            print("❌ Failed to connect to database")
            return False

        print("✅ Database connection successful")

        # Clean up table structure
        async with pool.acquire() as conn:
            async with conn.cursor() as cursor:
                # Check current structure
                await cursor.execute("DESCRIBE cappers")
                columns = await cursor.fetchall()
                column_names = [col[0] for col in columns]

                print(f"Current columns: {column_names}")

                # Remove duplicate updated_at column with space
                if " updated_at" in column_names:
                    print("Removing duplicate ' updated_at' column...")
                    try:
                        await cursor.execute(
                            "ALTER TABLE cappers DROP COLUMN ` updated_at`"
                        )
                        print("✅ Successfully removed duplicate column")
                    except Exception as e:
                        print(f"❌ Failed to remove duplicate column: {e}")

                # Add bet_push if missing
                if "bet_push" not in column_names:
                    print("Adding bet_push column...")
                    try:
                        await cursor.execute(
                            """
                            ALTER TABLE cappers 
                            ADD COLUMN bet_push INTEGER DEFAULT 0 NOT NULL
                        """
                        )
                        print("✅ Successfully added bet_push column")
                    except Exception as e:
                        print(f"❌ Failed to add bet_push column: {e}")
                else:
                    print("✅ bet_push column already exists")

                # Show final structure
                await cursor.execute("DESCRIBE cappers")
                final_columns = await cursor.fetchall()

                print("\n📋 Final cappers table structure:")
                print("Column Name\t\tType\t\tNull\tKey\tDefault\tExtra")
                print("-" * 80)

                for column in final_columns:
                    print(
                        f"{column[0]}\t\t{column[1]}\t\t{column[2]}\t{column[3]}\t{column[4]}\t{column[5]}"
                    )

        return True

    except Exception as e:
        print(f"❌ Database cleanup failed: {e}")
        return False
    finally:
        await db_manager.close()


if __name__ == "__main__":
    result = asyncio.run(clean_cappers_table())
    if result:
        print("\n🎉 Table cleanup completed!")
    else:
        print("\n💥 Table cleanup failed!")
        sys.exit(1)
