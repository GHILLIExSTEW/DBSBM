"""Image optimization utilities for asset management."""

import hashlib
import logging
import os
from pathlib import Path
from typing import Optional, Tuple

from PIL import Image

logger = logging.getLogger(__name__)


class ImageOptimizer:
    """Handles image optimization and compression."""

    def __init__(self, quality: int = 85, max_size: Tuple[int, int] = (1920, 1080)):
        """
        Initialize the image optimizer.

        Args:
            quality: JPEG quality (1-100)
            max_size: Maximum dimensions (width, height)
        """
        self.quality = quality
        self.max_size = max_size
        self.cache_dir = Path("betting-bot/static/cache/optimized")
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def optimize_image(self, image_path: str, output_path: Optional[str] = None) -> str:
        """
        Optimize an image file.

        Args:
            image_path: Path to the input image
            output_path: Path for the optimized image (optional)

        Returns:
            Path to the optimized image
        """
        try:
            # Generate cache key
            cache_key = self._generate_cache_key(image_path)
            cache_path = self.cache_dir / f"{cache_key}.jpg"

            # Check if optimized version exists
            if cache_path.exists():
                logger.info(f"Using cached optimized image: {cache_path}")
                return str(cache_path)

            # Load and optimize image
            with Image.open(image_path) as img:
                # Convert to RGB if necessary
                if img.mode in ("RGBA", "LA", "P"):
                    img = img.convert("RGB")

                # Resize if too large
                img = self._resize_image(img)

                # Save optimized image
                output_path = output_path or str(cache_path)
                img.save(output_path, "JPEG", quality=self.quality, optimize=True)

                logger.info(f"Optimized image saved: {output_path}")
                return output_path

        except Exception as e:
            logger.error(f"Error optimizing image {image_path}: {e}")
            return image_path

    def _resize_image(self, img: Image.Image) -> Image.Image:
        """Resize image if it exceeds maximum dimensions."""
        if img.size[0] > self.max_size[0] or img.size[1] > self.max_size[1]:
            img.thumbnail(self.max_size, Image.Resampling.LANCZOS)
        return img

    def _generate_cache_key(self, image_path: str) -> str:
        """Generate a cache key based on file path and modification time."""
        stat = os.stat(image_path)
        content = f"{image_path}_{stat.st_mtime}_{stat.st_size}"
        return hashlib.md5(content.encode()).hexdigest()

    def batch_optimize(
        self, directory: str, extensions: Tuple[str, ...] = (".png", ".jpg", ".jpeg")
    ) -> dict:
        """
        Optimize all images in a directory.

        Args:
            directory: Directory containing images
            extensions: File extensions to process

        Returns:
            Dictionary with optimization results
        """
        results = {"processed": 0, "optimized": 0, "errors": 0, "saved_space": 0}

        for root, _, files in os.walk(directory):
            for file in files:
                if file.lower().endswith(extensions):
                    file_path = os.path.join(root, file)
                    try:
                        # Get original size
                        original_size = os.path.getsize(file_path)

                        # Optimize image
                        optimized_path = self.optimize_image(file_path)

                        # Calculate space saved
                        if optimized_path != file_path:
                            optimized_size = os.path.getsize(optimized_path)
                            results["saved_space"] += original_size - optimized_size
                            results["optimized"] += 1

                        results["processed"] += 1

                    except Exception as e:
                        logger.error(f"Error processing {file_path}: {e}")
                        results["errors"] += 1

        return results

    def create_thumbnail(
        self, image_path: str, size: Tuple[int, int] = (150, 150)
    ) -> str:
        """
        Create a thumbnail of an image.

        Args:
            image_path: Path to the input image
            size: Thumbnail size (width, height)

        Returns:
            Path to the thumbnail
        """
        try:
            cache_key = self._generate_cache_key(f"{image_path}_{size}")
            thumbnail_path = self.cache_dir / f"thumb_{cache_key}.jpg"

            if thumbnail_path.exists():
                return str(thumbnail_path)

            with Image.open(image_path) as img:
                # Convert to RGB if necessary
                if img.mode in ("RGBA", "LA", "P"):
                    img = img.convert("RGB")

                # Create thumbnail
                img.thumbnail(size, Image.Resampling.LANCZOS)

                # Save thumbnail
                img.save(thumbnail_path, "JPEG", quality=80, optimize=True)

                logger.info(f"Thumbnail created: {thumbnail_path}")
                return str(thumbnail_path)

        except Exception as e:
            logger.error(f"Error creating thumbnail for {image_path}: {e}")
            return image_path

    def cleanup_cache(self, max_age_days: int = 30) -> int:
        """
        Clean up old cached files.

        Args:
            max_age_days: Maximum age of cached files in days

        Returns:
            Number of files removed
        """
        import time

        current_time = time.time()
        max_age_seconds = max_age_days * 24 * 60 * 60
        removed_count = 0

        for cache_file in self.cache_dir.glob("*.jpg"):
            if current_time - cache_file.stat().st_mtime > max_age_seconds:
                cache_file.unlink()
                removed_count += 1

        logger.info(f"Cleaned up {removed_count} old cached files")
        return removed_count
