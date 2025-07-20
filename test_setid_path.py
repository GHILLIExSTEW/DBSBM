#!/usr/bin/env python3
"""
Test script to verify the path calculation for the setid command
"""

import os

def test_path_calculation():
    """Test the path calculation used in setid.py"""
    
    # Simulate the path calculation from setid.py
    # File location: bot/commands/setid.py
    file_path = "bot/commands/setid.py"
    
    # Original (incorrect) calculation
    original_base_dir = os.path.dirname(os.path.dirname(os.path.dirname(file_path)))
    original_save_dir = os.path.join(original_base_dir, "static", "guilds", "1328116926903353398", "users")
    
    # Corrected calculation
    corrected_base_dir = os.path.dirname(os.path.dirname(file_path))
    corrected_save_dir = os.path.join(corrected_base_dir, "static", "guilds", "1328116926903353398", "users")
    
    print("Path Calculation Test")
    print("=" * 50)
    print(f"File path: {file_path}")
    print()
    print("Original (incorrect) calculation:")
    print(f"  base_dir: {original_base_dir}")
    print(f"  save_dir: {original_save_dir}")
    print()
    print("Corrected calculation:")
    print(f"  base_dir: {corrected_base_dir}")
    print(f"  save_dir: {corrected_save_dir}")
    print()
    
    # Check if the corrected path exists
    if os.path.exists(corrected_save_dir):
        print("✅ Corrected path exists!")
        print(f"Contents of {corrected_save_dir}:")
        try:
            files = os.listdir(corrected_save_dir)
            for file in files:
                print(f"  - {file}")
        except Exception as e:
            print(f"  Error listing directory: {e}")
    else:
        print("❌ Corrected path does not exist")
        print(f"Creating directory: {corrected_save_dir}")
        try:
            os.makedirs(corrected_save_dir, exist_ok=True)
            print("✅ Directory created successfully")
        except Exception as e:
            print(f"❌ Failed to create directory: {e}")

if __name__ == "__main__":
    test_path_calculation() 