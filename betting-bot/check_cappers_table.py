#!/usr/bin/env python3
"""
Check the actual structure of the cappers table
"""

import asyncio
import os
import sys
from dotenv import load_dotenv

# Add the current directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data.db_manager import DatabaseManager

async def check_cappers_table():
    """Check the structure of the cappers table"""
    print("Checking cappers table structure...")
    
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
        
        # Check table structure
        async with pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("DESCRIBE cappers")
                columns = await cursor.fetchall()
                
                print("\n📋 Cappers table structure:")
                print("Column Name\t\tType\t\tNull\tKey\tDefault\tExtra")
                print("-" * 80)
                
                for column in columns:
                    print(f"{column[0]}\t\t{column[1]}\t\t{column[2]}\t{column[3]}\t{column[4]}\t{column[5]}")
                
                # Check if updated_at column exists
                column_names = [col[0] for col in columns]
                if 'updated_at' in column_names:
                    print("\n✅ updated_at column exists")
                else:
                    print("\n❌ updated_at column is missing")
                    
                    # Try to add the column
                    print("Attempting to add updated_at column...")
                    try:
                        await cursor.execute("""
                            ALTER TABLE cappers 
                            ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                        """)
                        print("✅ Successfully added updated_at column")
                    except Exception as e:
                        print(f"❌ Failed to add updated_at column: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Database check failed: {e}")
        return False
    finally:
        await db_manager.close()

if __name__ == "__main__":
    result = asyncio.run(check_cappers_table())
    if result:
        print("\n🎉 Table check completed!")
    else:
        print("\n💥 Table check failed!")
        sys.exit(1) 