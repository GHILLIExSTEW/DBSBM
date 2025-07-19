#!/usr/bin/env python3
"""
UFC Logo Relocator
Moves existing UFC fighter logos from MMA/UFC to FIGHTING/UFC directory.
"""

import os
import shutil
from pathlib import Path

def relocate_ufc_logos():
    """Move UFC fighter logos to the correct directory structure."""
    
    # Source and destination paths
    source_dir = "bot/static/logos/teams/MMA/UFC"
    dest_dir = "bot/static/logos/teams/FIGHTING/UFC"
    
    print("🥊 Relocating UFC fighter logos...")
    
    # Check if source directory exists
    if not os.path.exists(source_dir):
        print(f"❌ Source directory not found: {source_dir}")
        return
    
    # Create destination directory
    os.makedirs(dest_dir, exist_ok=True)
    print(f"📁 Created destination directory: {dest_dir}")
    
    # Get all PNG files from source
    source_files = [f for f in os.listdir(source_dir) if f.endswith('.png')]
    print(f"📊 Found {len(source_files)} fighter logos to move")
    
    # Move each file
    moved_count = 0
    for filename in source_files:
        source_path = os.path.join(source_dir, filename)
        dest_path = os.path.join(dest_dir, filename)
        
        try:
            shutil.move(source_path, dest_path)
            moved_count += 1
            if moved_count % 100 == 0:  # Progress update every 100 files
                print(f"✅ Moved {moved_count}/{len(source_files)} logos...")
        except Exception as e:
            print(f"❌ Error moving {filename}: {e}")
    
    print(f"✅ Successfully moved {moved_count}/{len(source_files)} fighter logos!")
    print(f"📁 From: {source_dir}")
    print(f"📁 To: {dest_dir}")
    
    # Remove empty source directory
    try:
        os.rmdir(source_dir)
        print(f"🗑️ Removed empty source directory: {source_dir}")
    except Exception as e:
        print(f"⚠️ Could not remove source directory: {e}")
    
    # Verify the move
    dest_files = [f for f in os.listdir(dest_dir) if f.endswith('.png')]
    print(f"🔍 Verification: {len(dest_files)} logos now in destination directory")

if __name__ == "__main__":
    relocate_ufc_logos() 