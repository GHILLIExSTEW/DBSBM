#!/usr/bin/env python3
"""
Fix the cappers table by adding missing columns
"""

import asyncio
import os
import sys
from dotenv import load_dotenv

# Add the current directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data.db_manager import DatabaseManager

async def fix_cappers_table():
    """Fix the cappers table structure"""
    print("Fixing cappers table structure...")
    
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
        
        # Check and add missing columns
        async with pool.acquire() as conn:
            async with conn.cursor() as cursor:
                # Check current structure
                await cursor.execute("DESCRIBE cappers")
                columns = await cursor.fetchall()
                column_names = [col[0] for col in columns]
                
                print(f"Current columns: {column_names}")
                
                # Add created_at if missing
                if 'created_at' not in column_names:
                    print("Adding created_at column...")
                    try:
                        await cursor.execute("""
                            ALTER TABLE cappers 
                            ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        """)
                        print("✅ Successfully added created_at column")
                    except Exception as e:
                        print(f"❌ Failed to add created_at column: {e}")
                else:
                    print("✅ created_at column already exists")
                
                # Verify updated_at exists
                if 'updated_at' not in column_names:
                    print("Adding updated_at column...")
                    try:
                        await cursor.execute("""
                            ALTER TABLE cappers 
                            ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                        """)
                        print("✅ Successfully added updated_at column")
                    except Exception as e:
                        print(f"❌ Failed to add updated_at column: {e}")
                else:
                    print("✅ updated_at column already exists")
                
                # Show final structure
                await cursor.execute("DESCRIBE cappers")
                final_columns = await cursor.fetchall()
                
                print("\n📋 Final cappers table structure:")
                print("Column Name\t\tType\t\tNull\tKey\tDefault\tExtra")
                print("-" * 80)
                
                for column in final_columns:
                    print(f"{column[0]}\t\t{column[1]}\t\t{column[2]}\t{column[3]}\t{column[4]}\t{column[5]}")
        
        return True
        
    except Exception as e:
        print(f"❌ Database fix failed: {e}")
        return False
    finally:
        await db_manager.close()

if __name__ == "__main__":
    result = asyncio.run(fix_cappers_table())
    if result:
        print("\n🎉 Table fix completed!")
    else:
        print("\n💥 Table fix failed!")
        sys.exit(1) 