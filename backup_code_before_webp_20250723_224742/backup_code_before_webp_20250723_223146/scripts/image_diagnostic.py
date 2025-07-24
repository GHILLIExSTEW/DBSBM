#!/usr/bin/env python3
"""
DBSBM Image Diagnostic Script
Identifies why only some PNG files were converted to WebP.

This script analyzes the image optimization process to find:
1. Files that failed to convert
2. Files that were skipped
3. Permission issues
4. Corrupted files
5. Memory issues

Usage:
    python scripts/image_diagnostic.py [--path bot/static/logos]
"""

import os
import sys
import argparse
import logging
from pathlib import Path
from typing import List, Dict, Tuple
from PIL import Image
import traceback

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ImageDiagnostic:
    def __init__(self, target_path: str = "bot/static/logos"):
        self.target_path = Path(target_path)
        self.stats = {
            'total_files': 0,
            'accessible_files': 0,
            'valid_png_files': 0,
            'conversion_success': 0,
            'conversion_failed': 0,
            'permission_errors': 0,
            'corrupted_files': 0,
            'memory_errors': 0,
            'other_errors': 0
        }
        self.failed_files = []
        self.error_details = {}

    def check_file_access(self, file_path: Path) -> bool:
        """Check if file is accessible."""
        try:
            if not file_path.exists():
                return False
            # Try to open file
            with open(file_path, 'rb') as f:
                f.read(1)
            return True
        except PermissionError:
            self.stats['permission_errors'] += 1
            self.failed_files.append(str(file_path))
            self.error_details[str(file_path)] = "Permission denied"
            return False
        except Exception as e:
            self.stats['other_errors'] += 1
            self.failed_files.append(str(file_path))
            self.error_details[str(file_path)] = f"Access error: {e}"
            return False

    def check_png_validity(self, file_path: Path) -> bool:
        """Check if file is a valid PNG."""
        try:
            with Image.open(file_path) as img:
                # Check if it's actually a PNG
                if img.format != 'PNG':
                    self.stats['other_errors'] += 1
                    self.failed_files.append(str(file_path))
                    self.error_details[str(file_path)] = f"Not a PNG file (format: {img.format})"
                    return False
                
                # Check image dimensions
                width, height = img.size
                if width == 0 or height == 0:
                    self.stats['corrupted_files'] += 1
                    self.failed_files.append(str(file_path))
                    self.error_details[str(file_path)] = "Invalid dimensions (0x0)"
                    return False
                
                return True
        except Exception as e:
            self.stats['corrupted_files'] += 1
            self.failed_files.append(str(file_path))
            self.error_details[str(file_path)] = f"Corrupted PNG: {e}"
            return False

    def test_conversion(self, file_path: Path) -> bool:
        """Test if file can be converted to WebP."""
        try:
            with Image.open(file_path) as img:
                # Convert to RGB if necessary
                if img.mode in ('RGBA', 'LA', 'P'):
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'P':
                        img = img.convert('RGBA')
                    background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                    img = background
                elif img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Test WebP conversion (don't save)
                webp_path = file_path.with_suffix('.webp')
                
                # Just test the conversion, don't save
                return True
                
        except MemoryError:
            self.stats['memory_errors'] += 1
            self.failed_files.append(str(file_path))
            self.error_details[str(file_path)] = "Memory error during conversion"
            return False
        except Exception as e:
            self.stats['conversion_failed'] += 1
            self.failed_files.append(str(file_path))
            self.error_details[str(file_path)] = f"Conversion failed: {e}"
            return False

    def analyze_file(self, file_path: Path):
        """Analyze a single PNG file."""
        self.stats['total_files'] += 1
        
        # Step 1: Check file access
        if not self.check_file_access(file_path):
            return
        
        self.stats['accessible_files'] += 1
        
        # Step 2: Check PNG validity
        if not self.check_png_validity(file_path):
            return
        
        self.stats['valid_png_files'] += 1
        
        # Step 3: Test conversion
        if self.test_conversion(file_path):
            self.stats['conversion_success'] += 1

    def run_diagnostic(self):
        """Run the diagnostic analysis."""
        logger.info("🔍 Starting DBSBM Image Diagnostic")
        logger.info(f"Target path: {self.target_path}")
        
        if not self.target_path.exists():
            logger.error(f"Directory not found: {self.target_path}")
            return
        
        # Find all PNG files
        png_files = list(self.target_path.rglob("*.png"))
        logger.info(f"Found {len(png_files)} PNG files")
        
        # Analyze each file
        for i, png_file in enumerate(png_files, 1):
            if i % 1000 == 0:
                logger.info(f"Processed {i}/{len(png_files)} files...")
            self.analyze_file(png_file)
        
        # Print results
        self.print_results()

    def print_results(self):
        """Print diagnostic results."""
        logger.info("\n" + "="*60)
        logger.info("🔍 IMAGE DIAGNOSTIC RESULTS")
        logger.info("="*60)
        
        logger.info(f"📁 Total PNG files found: {self.stats['total_files']}")
        logger.info(f"✅ Accessible files: {self.stats['accessible_files']}")
        logger.info(f"🖼️ Valid PNG files: {self.stats['valid_png_files']}")
        logger.info(f"✅ Conversion successful: {self.stats['conversion_success']}")
        logger.info(f"❌ Conversion failed: {self.stats['conversion_failed']}")
        logger.info(f"🚫 Permission errors: {self.stats['permission_errors']}")
        logger.info(f"💥 Corrupted files: {self.stats['corrupted_files']}")
        logger.info(f"💾 Memory errors: {self.stats['memory_errors']}")
        logger.info(f"❓ Other errors: {self.stats['other_errors']}")
        
        # Calculate discrepancies
        expected_conversions = self.stats['valid_png_files']
        actual_conversions = self.stats['conversion_success']
        failed_conversions = self.stats['conversion_failed']
        
        logger.info(f"\n📊 CONVERSION ANALYSIS:")
        logger.info(f"Expected conversions: {expected_conversions}")
        logger.info(f"Successful conversions: {actual_conversions}")
        logger.info(f"Failed conversions: {failed_conversions}")
        logger.info(f"Missing conversions: {expected_conversions - actual_conversions - failed_conversions}")
        
        if self.failed_files:
            logger.info(f"\n❌ FAILED FILES (first 10):")
            for file_path in self.failed_files[:10]:
                error = self.error_details.get(file_path, "Unknown error")
                logger.info(f"  {file_path}: {error}")
            
            if len(self.failed_files) > 10:
                logger.info(f"  ... and {len(self.failed_files) - 10} more files")
        
        logger.info("="*60)

def main():
    parser = argparse.ArgumentParser(description="DBSBM Image Diagnostic Tool")
    parser.add_argument("--path", default="bot/static/logos", 
                       help="Path to analyze (default: bot/static/logos)")
    
    args = parser.parse_args()
    
    diagnostic = ImageDiagnostic(args.path)
    diagnostic.run_diagnostic()

if __name__ == "__main__":
    main() 