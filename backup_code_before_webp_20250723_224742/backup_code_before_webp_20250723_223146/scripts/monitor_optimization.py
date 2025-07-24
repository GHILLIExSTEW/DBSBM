#!/usr/bin/env python3
"""
DBSBM Image Optimization Monitor
Monitors the progress of comprehensive image optimization.

This script provides real-time updates on:
1. Files processed
2. Files converted
3. Storage saved
4. Progress percentage
5. Estimated time remaining

Usage:
    python scripts/monitor_optimization.py
"""

import os
import time
import glob
from pathlib import Path
from typing import Dict, List

def count_webp_files():
    """Count WebP files in the static directory."""
    webp_files = glob.glob("bot/static/**/*.webp", recursive=True)
    return len(webp_files)

def count_original_files():
    """Count original image files (PNG, JPEG, etc.)."""
    patterns = [
        "bot/static/**/*.png",
        "bot/static/**/*.jpg", 
        "bot/static/**/*.jpeg",
        "bot/static/**/*.gif",
        "bot/static/**/*.bmp",
        "bot/static/**/*.tiff"
    ]
    
    total_files = 0
    for pattern in patterns:
        files = glob.glob(pattern, recursive=True)
        total_files += len(files)
    
    return total_files

def get_directory_size(directory: str) -> float:
    """Get directory size in MB."""
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(directory):
        for filename in filenames:
            filepath = os.path.join(dirpath, filename)
            if os.path.exists(filepath):
                total_size += os.path.getsize(filepath)
    return total_size / (1024 * 1024)  # Convert to MB

def main():
    print("🔄 DBSBM Image Optimization Monitor")
    print("=" * 50)
    
    # Initial counts
    initial_webp = count_webp_files()
    initial_size = get_directory_size("bot/static")
    
    print(f"📊 Initial Status:")
    print(f"   WebP files: {initial_webp}")
    print(f"   Directory size: {initial_size:.2f} MB")
    print()
    
    last_webp_count = initial_webp
    last_check_time = time.time()
    
    while True:
        try:
            # Current counts
            current_webp = count_webp_files()
            current_size = get_directory_size("bot/static")
            
            # Calculate progress
            files_converted = current_webp - initial_webp
            size_saved = initial_size - current_size
            
            # Calculate rate
            time_elapsed = time.time() - last_check_time
            if time_elapsed > 0:
                conversion_rate = (current_webp - last_webp_count) / time_elapsed
            else:
                conversion_rate = 0
            
            # Clear screen and show progress
            os.system('cls' if os.name == 'nt' else 'clear')
            
            print("🔄 DBSBM Image Optimization Monitor")
            print("=" * 50)
            print(f"📊 Progress Update:")
            print(f"   Files converted: {files_converted}")
            print(f"   Storage saved: {size_saved:.2f} MB")
            print(f"   Current directory size: {current_size:.2f} MB")
            print(f"   Conversion rate: {conversion_rate:.1f} files/sec")
            print()
            
            if files_converted > 0:
                compression_ratio = (size_saved / initial_size) * 100
                print(f"📈 Compression ratio: {compression_ratio:.1f}%")
                print()
            
            # Check if optimization is still running
            if current_webp > last_webp_count:
                print("✅ Optimization is actively running...")
            else:
                print("⏸️  No new conversions detected (may be paused or completed)")
            
            print()
            print("Press Ctrl+C to stop monitoring")
            
            last_webp_count = current_webp
            last_check_time = time.time()
            
            time.sleep(5)  # Update every 5 seconds
            
        except KeyboardInterrupt:
            print("\n🛑 Monitoring stopped by user")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main() 