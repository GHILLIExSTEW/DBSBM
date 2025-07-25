#!/usr/bin/env python3
"""
DBSBM Comprehensive Image Optimization Script
Converts multiple image formats (PNG, JPEG, GIF, etc.) to WebP format for better compression.

This script performs the following optimizations:
1. Converts PNG, JPEG, GIF, BMP, TIFF images to WebP format
2. Maintains quality while reducing file size
3. Handles files with wrong extensions
4. Provides detailed conversion reports
5. Supports batch processing of entire directories

Usage:
    python scripts/comprehensive_image_optimizer.py [--dry-run] [--quality 85] [--path bot/static/logos]
"""

import argparse
import asyncio
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple

from PIL import Image

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class ComprehensiveImageOptimizer:
    def __init__(
        self,
        dry_run: bool = False,
        quality: int = 85,
        target_path: str = "bot/static/logos",
    ):
        self.dry_run = dry_run
        self.quality = quality
        self.target_path = Path(target_path)

        # Supported input formats
        self.supported_formats = {
            ".webp",
            ".jpg",
            ".jpeg",
            ".gif",
            ".bmp",
            ".tiff",
            ".tif",
        }

        # Statistics
        self.stats = {
            "files_processed": 0,
            "files_converted": 0,
            "original_size": 0,
            "optimized_size": 0,
            "bytes_saved": 0,
            "errors": 0,
            "skipped_files": 0,
            "format_breakdown": {},
        }

    def log_action(self, action: str, path: str, size_saved: int = 0):
        """Log an action with optional size savings."""
        if size_saved > 0:
            logger.info(f"{action}: {path} (saved {size_saved:,} bytes)")
        else:
            logger.info(f"{action}: {path}")

    def get_image_format(self, file_path: Path) -> str:
        """Detect the actual image format of a file."""
        try:
            with Image.open(file_path) as img:
                return img.format.lower() if img.format else "unknown"
        except Exception as e:
            logger.warning(f"Could not detect format for {file_path}: {e}")
            return "unknown"

    def is_supported_format(self, file_path: Path) -> bool:
        """Check if file is a supported image format."""
        # Check file extension first
        if file_path.suffix.lower() in self.supported_formats:
            return True

        # Check actual image format
        actual_format = self.get_image_format(file_path)
        return actual_format in ["png", "jpeg", "jpg", "gif", "bmp", "tiff"]

    def convert_to_webp(self, image_path: Path) -> bool:
        """Convert an image file to WebP format."""
        try:
            if not image_path.exists():
                logger.warning(f"File not found: {image_path}")
                return False

            # Get original file size
            original_size = image_path.stat().st_size

            # Create WebP path
            webp_path = image_path.with_suffix(".webp")

            # Get actual image format for logging
            actual_format = self.get_image_format(image_path)

            if not self.dry_run:
                # Open and convert image
                with Image.open(image_path) as img:
                    # Convert to RGB if necessary (WebP doesn't support RGBA)
                    if img.mode in ("RGBA", "LA", "P"):
                        # Create white background for transparent images
                        background = Image.new("RGB", img.size, (255, 255, 255))
                        if img.mode == "P":
                            img = img.convert("RGBA")
                        background.paste(
                            img, mask=img.split()[-1] if img.mode == "RGBA" else None
                        )
                        img = background
                    elif img.mode != "RGB":
                        img = img.convert("RGB")

                    # Save as WebP
                    img.save(webp_path, "WEBP", quality=self.quality, optimize=True)

                # Get optimized file size
                optimized_size = webp_path.stat().st_size
                size_saved = original_size - optimized_size

                self.log_action(
                    f"Converted {actual_format.upper()} to WebP",
                    str(image_path),
                    size_saved,
                )

                # Update statistics
                self.stats["files_converted"] += 1
                self.stats["original_size"] += original_size
                self.stats["optimized_size"] += optimized_size
                self.stats["bytes_saved"] += size_saved

                # Update format breakdown
                if actual_format not in self.stats["format_breakdown"]:
                    self.stats["format_breakdown"][actual_format] = 0
                self.stats["format_breakdown"][actual_format] += 1

                return True
            else:
                # Dry run - just log what would be done
                self.log_action(
                    f"Would convert {actual_format.upper()} to WebP", str(image_path)
                )
                self.stats["files_processed"] += 1

                # Update format breakdown for dry run
                if actual_format not in self.stats["format_breakdown"]:
                    self.stats["format_breakdown"][actual_format] = 0
                self.stats["format_breakdown"][actual_format] += 1

                return True

        except Exception as e:
            logger.error(f"Error converting {image_path}: {e}")
            self.stats["errors"] += 1
            return False

    def optimize_directory(self, directory: Path) -> int:
        """Optimize all image files in a directory recursively."""
        converted_count = 0

        if not directory.exists():
            logger.warning(f"Directory not found: {directory}")
            return 0

        # Find all potential image files
        image_files = []
        for ext in self.supported_formats:
            image_files.extend(directory.rglob(f"*{ext}"))

        # Also find files with wrong extensions but valid image content
        all_files = list(directory.rglob("*"))
        for file_path in all_files:
            if (
                file_path.is_file()
                and file_path.suffix.lower() not in self.supported_formats
            ):
                if self.is_supported_format(file_path):
                    image_files.append(file_path)

        # Remove duplicates
        image_files = list(set(image_files))

        logger.info(f"Found {len(image_files)} image files in {directory}")

        for image_file in image_files:
            if self.convert_to_webp(image_file):
                converted_count += 1
            self.stats["files_processed"] += 1

        return converted_count

    def generate_report(self) -> Dict:
        """Generate optimization report."""
        if self.stats["original_size"] > 0:
            compression_ratio = (
                1 - self.stats["optimized_size"] / self.stats["original_size"]
            ) * 100
            mb_saved = self.stats["bytes_saved"] / (1024 * 1024)
        else:
            compression_ratio = 0
            mb_saved = 0

        report = {
            "files_processed": self.stats["files_processed"],
            "files_converted": self.stats["files_converted"],
            "original_size_mb": self.stats["original_size"] / (1024 * 1024),
            "optimized_size_mb": self.stats["optimized_size"] / (1024 * 1024),
            "compression_ratio": compression_ratio,
            "mb_saved": mb_saved,
            "errors": self.stats["errors"],
            "format_breakdown": self.stats["format_breakdown"],
        }

        return report

    def print_summary(self):
        """Print optimization summary."""
        report = self.generate_report()

        logger.info("\n" + "=" * 60)
        logger.info("🖼️ COMPREHENSIVE IMAGE OPTIMIZATION SUMMARY")
        logger.info("=" * 60)

        if self.dry_run:
            logger.info("📋 DRY RUN MODE - No files were actually converted")

        logger.info(f"📁 Files processed: {report['files_processed']}")
        logger.info(f"🔄 Files converted: {report['files_converted']}")
        logger.info(f"💾 Original size: {report['original_size_mb']:.2f} MB")
        logger.info(f"💾 Optimized size: {report['optimized_size_mb']:.2f} MB")
        logger.info(f"📉 Compression ratio: {report['compression_ratio']:.1f}%")
        logger.info(f"💾 Storage saved: {report['mb_saved']:.2f} MB")
        logger.info(f"❌ Errors: {report['errors']}")

        if report["format_breakdown"]:
            logger.info(f"\n📊 FORMAT BREAKDOWN:")
            for format_name, count in sorted(report["format_breakdown"].items()):
                logger.info(f"  {format_name.upper()}: {count} files")

        logger.info("=" * 60)

    def run_optimization(self) -> Dict:
        """Run the comprehensive image optimization process."""
        logger.info("🚀 Starting DBSBM Comprehensive Image Optimization")
        logger.info(f"Target path: {self.target_path}")
        logger.info(f"Quality setting: {self.quality}")
        logger.info(f"Supported formats: {', '.join(sorted(self.supported_formats))}")

        if self.dry_run:
            logger.info("🔍 Running in DRY RUN mode - no files will be modified")

        # Run optimization
        converted_count = self.optimize_directory(self.target_path)

        # Print summary
        self.print_summary()

        return self.generate_report()


def main():
    parser = argparse.ArgumentParser(
        description="DBSBM Comprehensive Image Optimization Tool"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run in dry-run mode (no files will be modified)",
    )
    parser.add_argument(
        "--quality",
        type=int,
        default=85,
        help="WebP quality setting (1-100, default: 85)",
    )
    parser.add_argument(
        "--path",
        default="bot/static/logos",
        help="Path to optimize (default: bot/static/logos)",
    )

    args = parser.parse_args()

    # Validate quality setting
    if not 1 <= args.quality <= 100:
        logger.error("Quality must be between 1 and 100")
        sys.exit(1)

    optimizer = ComprehensiveImageOptimizer(
        dry_run=args.dry_run, quality=args.quality, target_path=args.path
    )

    try:
        result = optimizer.run_optimization()
        logger.info("✅ Optimization completed successfully!")

        if not args.dry_run and result["files_converted"] > 0:
            logger.info(
                f"🎉 Converted {result['files_converted']} files to WebP format"
            )
            logger.info(f"💾 Saved {result['mb_saved']:.2f} MB of storage")

    except KeyboardInterrupt:
        logger.info("⚠️ Optimization interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Optimization failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
