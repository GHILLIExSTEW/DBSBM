#!/usr/bin/env python3
"""
DBSBM Image Optimization Script
Converts PNG images to WebP format for better compression and performance.

This script performs the following optimizations:
1. Converts PNG images to WebP format
2. Maintains quality while reducing file size
3. Creates optimized versions of team logos and other images
4. Provides size comparison reports

Usage:
    python scripts/image_optimizer.py [--dry-run] [--quality 85] [--path bot/static/logos]
"""

import os
import sys
import argparse
import logging
from pathlib import Path
from typing import List, Dict, Tuple
from PIL import Image
import asyncio

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ImageOptimizer:
    def __init__(self, dry_run: bool = False, quality: int = 85, target_path: str = "bot/static/logos"):
        self.dry_run = dry_run
        self.quality = quality
        self.target_path = Path(target_path)
        self.project_root = Path(__file__).parent.parent
        self.stats = {
            'files_processed': 0,
            'files_converted': 0,
            'bytes_saved': 0,
            'original_size': 0,
            'optimized_size': 0,
            'errors': 0
        }

    def log_action(self, action: str, path: str, size_saved: int = 0):
        """Log an action with appropriate prefix for dry run."""
        prefix = "[DRY RUN] " if self.dry_run else ""
        size_str = f" (saved {size_saved} bytes)" if size_saved > 0 else ""
        logger.info(f"{prefix}{action}: {path}{size_str}")

    def convert_png_to_webp(self, png_path: Path) -> bool:
        """Convert a PNG file to WebP format."""
        try:
            if not png_path.exists():
                logger.warning(f"File not found: {png_path}")
                return False

            # Get original file size
            original_size = png_path.stat().st_size
            
            # Create WebP path
            webp_path = png_path.with_suffix('.webp')
            
            if not self.dry_run:
                # Open and convert image
                with Image.open(png_path) as img:
                    # Convert to RGB if necessary (WebP doesn't support RGBA)
                    if img.mode in ('RGBA', 'LA', 'P'):
                        # Create white background for transparent images
                        background = Image.new('RGB', img.size, (255, 255, 255))
                        if img.mode == 'P':
                            img = img.convert('RGBA')
                        background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                        img = background
                    elif img.mode != 'RGB':
                        img = img.convert('RGB')
                    
                    # Save as WebP
                    img.save(webp_path, 'WEBP', quality=self.quality, optimize=True)
                
                # Get optimized file size
                optimized_size = webp_path.stat().st_size
                size_saved = original_size - optimized_size
                
                self.log_action("Converted PNG to WebP", str(png_path), size_saved)
                
                # Update statistics
                self.stats['files_converted'] += 1
                self.stats['original_size'] += original_size
                self.stats['optimized_size'] += optimized_size
                self.stats['bytes_saved'] += size_saved
                
                return True
            else:
                # Dry run - just log what would be done
                self.log_action("Would convert PNG to WebP", str(png_path))
                self.stats['files_processed'] += 1
                return True
                
        except Exception as e:
            logger.error(f"Error converting {png_path}: {e}")
            self.stats['errors'] += 1
            return False

    def optimize_directory(self, directory: Path) -> int:
        """Optimize all PNG files in a directory recursively."""
        converted_count = 0
        
        if not directory.exists():
            logger.warning(f"Directory not found: {directory}")
            return 0
        
        # Find all PNG files
        png_files = list(directory.rglob("*.webp"))
        logger.info(f"Found {len(png_files)} PNG files in {directory}")
        
        for png_file in png_files:
            if self.convert_png_to_webp(png_file):
                converted_count += 1
            self.stats['files_processed'] += 1
        
        return converted_count

    def generate_report(self) -> Dict:
        """Generate optimization report."""
        if self.stats['original_size'] > 0:
            compression_ratio = (1 - self.stats['optimized_size'] / self.stats['original_size']) * 100
            mb_saved = self.stats['bytes_saved'] / (1024 * 1024)
        else:
            compression_ratio = 0
            mb_saved = 0
        
        report = {
            'files_processed': self.stats['files_processed'],
            'files_converted': self.stats['files_converted'],
            'original_size_mb': self.stats['original_size'] / (1024 * 1024),
            'optimized_size_mb': self.stats['optimized_size'] / (1024 * 1024),
            'compression_ratio': compression_ratio,
            'mb_saved': mb_saved,
            'errors': self.stats['errors']
        }
        
        return report

    def print_summary(self):
        """Print optimization summary."""
        report = self.generate_report()
        
        logger.info("\n" + "="*50)
        logger.info("🖼️ IMAGE OPTIMIZATION SUMMARY")
        logger.info("="*50)
        
        if self.dry_run:
            logger.info("📋 DRY RUN MODE - No files were actually converted")
        
        logger.info(f"📁 Files processed: {report['files_processed']}")
        logger.info(f"🔄 Files converted: {report['files_converted']}")
        logger.info(f"💾 Original size: {report['original_size_mb']:.2f} MB")
        logger.info(f"💾 Optimized size: {report['optimized_size_mb']:.2f} MB")
        logger.info(f"📉 Compression ratio: {report['compression_ratio']:.1f}%")
        logger.info(f"💾 Storage saved: {report['mb_saved']:.2f} MB")
        logger.info(f"❌ Errors: {report['errors']}")
        
        logger.info("="*50)

    def run_optimization(self) -> Dict:
        """Run the image optimization process."""
        logger.info("🚀 Starting DBSBM Image Optimization")
        logger.info(f"Target path: {self.target_path}")
        logger.info(f"Quality setting: {self.quality}")
        
        if self.dry_run:
            logger.info("🔍 Running in DRY RUN mode - no files will be modified")
        
        # Run optimization
        converted_count = self.optimize_directory(self.target_path)
        
        # Print summary
        self.print_summary()
        
        return self.generate_report()

def main():
    parser = argparse.ArgumentParser(description="DBSBM Image Optimization Script")
    parser.add_argument("--dry-run", action="store_true", 
                       help="Show what would be optimized without actually converting files")
    parser.add_argument("--quality", type=int, default=85,
                       help="WebP quality setting (1-100, default: 85)")
    parser.add_argument("--path", type=str, default="bot/static/logos",
                       help="Path to directory containing images to optimize")
    
    args = parser.parse_args()
    
    # Validate quality setting
    if args.quality < 1 or args.quality > 100:
        logger.error("Quality must be between 1 and 100")
        sys.exit(1)
    
    # Create optimizer instance
    optimizer = ImageOptimizer(
        dry_run=args.dry_run,
        quality=args.quality,
        target_path=args.path
    )
    
    # Run optimization
    try:
        report = optimizer.run_optimization()
        
        if not args.dry_run and report['files_converted'] > 0:
            logger.info("✅ Image optimization completed successfully!")
        elif args.dry_run:
            logger.info("✅ Dry run completed - review the output above")
        else:
            logger.info("✅ No images needed optimization")
            
    except KeyboardInterrupt:
        logger.info("❌ Image optimization interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Image optimization failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 