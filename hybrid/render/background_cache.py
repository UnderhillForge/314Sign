#!/usr/bin/env python3
"""
Background Image Cache Management
Intelligent caching and retrieval of background images for LMS rendering
"""

import os
import hashlib
import json
import time
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import requests

class BackgroundCache:
    """
    Manages background image caching with intelligent deduplication
    and automatic cleanup based on usage patterns.
    """

    def __init__(self, cache_dir: str = "/home/pi/backgrounds",
                 max_cache_size_mb: int = 500,
                 kiosk_url: str = "http://kiosk.local:80"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.max_cache_size_mb = max_cache_size_mb
        self.kiosk_url = kiosk_url.rstrip('/')

        # Cache metadata
        self.metadata_file = self.cache_dir / "cache_metadata.json"
        self.metadata = self._load_metadata()

        # Setup logging
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    def _load_metadata(self) -> Dict[str, Any]:
        """Load cache metadata from disk"""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logging.warning(f"Failed to load cache metadata: {e}")

        # Default metadata structure
        return {
            "version": "1.0",
            "images": {},  # filename -> metadata
            "last_cleanup": time.time(),
            "total_size_bytes": 0
        }

    def _save_metadata(self) -> None:
        """Save cache metadata to disk"""
        try:
            with open(self.metadata_file, 'w') as f:
                json.dump(self.metadata, f, indent=2)
        except Exception as e:
            logging.error(f"Failed to save cache metadata: {e}")

    def calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA256 hash of a file"""
        hash_sha256 = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_sha256.update(chunk)
            return hash_sha256.hexdigest()
        except Exception:
            return ""

    def get_cache_key(self, filename: str, expected_hash: Optional[str] = None) -> str:
        """
        Generate a unique cache key for a background image.
        If hash is provided, use it for precise identification.
        Otherwise, use filename (less reliable but backward compatible).
        """
        if expected_hash:
            return f"{filename}_{expected_hash[:8]}"  # Use first 8 chars of hash
        else:
            return filename

    def is_cached(self, filename: str, expected_hash: Optional[str] = None) -> bool:
        """
        Check if a background image is cached and matches expected hash
        """
        cache_key = self.get_cache_key(filename, expected_hash)

        if cache_key not in self.metadata["images"]:
            return False

        image_meta = self.metadata["images"][cache_key]
        cached_path = self.cache_dir / image_meta["cached_filename"]

        # Check if file exists
        if not cached_path.exists():
            logging.warning(f"Cached file missing: {cached_path}")
            # Remove from metadata
            del self.metadata["images"][cache_key]
            self._save_metadata()
            return False

        # Check hash if provided
        if expected_hash:
            actual_hash = self.calculate_file_hash(cached_path)
            if actual_hash != expected_hash:
                logging.warning(f"Hash mismatch for {filename}: expected {expected_hash}, got {actual_hash}")
                # Remove corrupted file
                cached_path.unlink()
                del self.metadata["images"][cache_key]
                self._save_metadata()
                return False

        # Update access time
        image_meta["last_accessed"] = time.time()
        self._save_metadata()

        return True

    def get_cached_path(self, filename: str, expected_hash: Optional[str] = None) -> Optional[Path]:
        """
        Get the cached file path for a background image
        """
        if not self.is_cached(filename, expected_hash):
            return None

        cache_key = self.get_cache_key(filename, expected_hash)
        image_meta = self.metadata["images"][cache_key]
        return self.cache_dir / image_meta["cached_filename"]

    def download_and_cache(self, filename: str, expected_hash: Optional[str] = None,
                          force: bool = False) -> Optional[Path]:
        """
        Download a background image from kiosk and cache it locally
        """
        # Check if already cached (unless force refresh)
        if not force and self.is_cached(filename, expected_hash):
            cache_key = self.get_cache_key(filename, expected_hash)
            image_meta = self.metadata["images"][cache_key]
            cached_path = self.cache_dir / image_meta["cached_filename"]
            logging.info(f"Using cached background: {filename}")
            return cached_path

        # Download from kiosk
        image_url = f"{self.kiosk_url}/backgrounds/{filename}"
        logging.info(f"Downloading background: {image_url}")

        try:
            response = requests.get(image_url, timeout=30, stream=True)
            response.raise_for_status()

            # Create temporary file first
            temp_path = self.cache_dir / f"{filename}.tmp"
            with open(temp_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            # Verify hash if provided
            if expected_hash:
                actual_hash = self.calculate_file_hash(temp_path)
                if actual_hash != expected_hash:
                    temp_path.unlink()
                    raise ValueError(f"Downloaded file hash mismatch: expected {expected_hash}, got {actual_hash}")

            # Generate unique cached filename to avoid conflicts
            cache_key = self.get_cache_key(filename, expected_hash)
            timestamp = int(time.time())
            cached_filename = f"{cache_key}_{timestamp}.bg"

            # Move to final location
            cached_path = self.cache_dir / cached_filename
            temp_path.rename(cached_path)

            # Update metadata
            file_size = cached_path.stat().st_size
            self.metadata["images"][cache_key] = {
                "original_filename": filename,
                "cached_filename": cached_filename,
                "hash": expected_hash or self.calculate_file_hash(cached_path),
                "size_bytes": file_size,
                "downloaded_at": timestamp,
                "last_accessed": timestamp
            }

            # Update total cache size
            self.metadata["total_size_bytes"] += file_size

            self._save_metadata()
            logging.info(f"Cached background: {filename} ({file_size} bytes)")

            # Cleanup old files if cache too large
            self._cleanup_if_needed()

            return cached_path

        except Exception as e:
            logging.error(f"Failed to download/cache background {filename}: {e}")
            # Clean up temp file if it exists
            temp_path = self.cache_dir / f"{filename}.tmp"
            if temp_path.exists():
                temp_path.unlink()
            return None

    def _cleanup_if_needed(self) -> None:
        """Clean up old cached files if cache size exceeds limit"""
        max_bytes = self.max_cache_size_mb * 1024 * 1024
        current_bytes = self.metadata["total_size_bytes"]

        if current_bytes <= max_bytes:
            return

        logging.info(f"Cache size ({current_bytes} bytes) exceeds limit ({max_bytes} bytes), cleaning up...")

        # Sort images by last accessed time (oldest first)
        images_by_age = sorted(
            self.metadata["images"].items(),
            key=lambda x: x[1]["last_accessed"]
        )

        bytes_to_free = current_bytes - max_bytes
        bytes_freed = 0

        for cache_key, image_meta in images_by_age:
            if bytes_freed >= bytes_to_free:
                break

            cached_path = self.cache_dir / image_meta["cached_filename"]
            try:
                file_size = cached_path.stat().st_size
                cached_path.unlink()
                bytes_freed += file_size
                del self.metadata["images"][cache_key]
                logging.info(f"Removed old cached background: {image_meta['original_filename']}")
            except Exception as e:
                logging.warning(f"Failed to remove cached file {cached_path}: {e}")

        self.metadata["total_size_bytes"] -= bytes_freed
        self.metadata["last_cleanup"] = time.time()
        self._save_metadata()

        logging.info(f"Cache cleanup complete: freed {bytes_freed} bytes")

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_images = len(self.metadata["images"])
        total_size_mb = self.metadata["total_size_bytes"] / (1024 * 1024)

        # Count images by age
        now = time.time()
        last_hour = sum(1 for img in self.metadata["images"].values()
                       if now - img["last_accessed"] < 3600)
        last_day = sum(1 for img in self.metadata["images"].values()
                      if now - img["last_accessed"] < 86400)
        last_week = sum(1 for img in self.metadata["images"].values()
                       if now - img["last_accessed"] < 604800)

        return {
            "total_images": total_images,
            "total_size_mb": round(total_size_mb, 2),
            "max_size_mb": self.max_cache_size_mb,
            "usage_percent": round((total_size_mb / self.max_cache_size_mb) * 100, 1),
            "images_last_hour": last_hour,
            "images_last_day": last_day,
            "images_last_week": last_week,
            "last_cleanup": self.metadata.get("last_cleanup", 0)
        }

    def list_cached_images(self) -> List[Dict[str, Any]]:
        """List all cached images with metadata"""
        images = []
        for cache_key, meta in self.metadata["images"].items():
            cached_path = self.cache_dir / meta["cached_filename"]
            exists = cached_path.exists()

            images.append({
                "cache_key": cache_key,
                "original_filename": meta["original_filename"],
                "cached_filename": meta["cached_filename"],
                "hash": meta["hash"],
                "size_bytes": meta["size_bytes"],
                "downloaded_at": meta["downloaded_at"],
                "last_accessed": meta["last_accessed"],
                "exists": exists
            })

        # Sort by last accessed (most recent first)
        images.sort(key=lambda x: x["last_accessed"], reverse=True)
        return images

    def clear_cache(self) -> None:
        """Clear all cached images"""
        logging.info("Clearing background image cache...")

        for cache_key, image_meta in self.metadata["images"].items():
            cached_path = self.cache_dir / image_meta["cached_filename"]
            try:
                if cached_path.exists():
                    cached_path.unlink()
            except Exception as e:
                logging.warning(f"Failed to remove {cached_path}: {e}")

        self.metadata["images"] = {}
        self.metadata["total_size_bytes"] = 0
        self.metadata["last_cleanup"] = time.time()
        self._save_metadata()

        logging.info("Cache cleared successfully")

# Convenience functions
def get_background_image(cache: BackgroundCache, filename: str,
                        expected_hash: Optional[str] = None) -> Optional[Path]:
    """
    Get a background image, downloading if necessary
    """
    # Try cache first
    cached_path = cache.get_cached_path(filename, expected_hash)
    if cached_path:
        return cached_path

    # Download and cache
    return cache.download_and_cache(filename, expected_hash)

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Background Image Cache Manager')
    parser.add_argument('--cache-dir', default='/home/pi/backgrounds', help='Cache directory')
    parser.add_argument('--kiosk-url', default='http://kiosk.local:80', help='Kiosk base URL')
    parser.add_argument('--max-size', type=int, default=500, help='Max cache size in MB')
    parser.add_argument('--list', action='store_true', help='List cached images')
    parser.add_argument('--stats', action='store_true', help='Show cache statistics')
    parser.add_argument('--clear', action='store_true', help='Clear all cached images')
    parser.add_argument('--download', help='Download and cache specific image')
    parser.add_argument('--hash', help='Expected hash for downloaded image')

    args = parser.parse_args()

    cache = BackgroundCache(args.cache_dir, args.max_size, args.kiosk_url)

    if args.list:
        images = cache.list_cached_images()
        if images:
            print(f"Cached Images ({len(images)}):")
            print("-" * 80)
            for img in images:
                age = time.time() - img['last_accessed']
                age_str = f"{age/3600:.1f}h ago" if age < 86400 else f"{age/86400:.1f}d ago"
                status = "✓" if img['exists'] else "✗"
                print(f"{status} {img['original_filename']} ({img['size_bytes']} bytes) - {age_str}")
        else:
            print("No cached images")

    elif args.stats:
        stats = cache.get_cache_stats()
        print("Cache Statistics:")
        print(f"  Total Images: {stats['total_images']}")
        print(f"  Cache Size: {stats['total_size_mb']}MB / {stats['max_size_mb']}MB ({stats['usage_percent']}%)")
        print(f"  Images (last hour/day/week): {stats['images_last_hour']}/{stats['images_last_day']}/{stats['images_last_week']}")

    elif args.clear:
        cache.clear_cache()
        print("Cache cleared")

    elif args.download:
        result = cache.download_and_cache(args.download, args.hash)
        if result:
            print(f"Downloaded and cached: {result}")
        else:
            print("Download failed")
            exit(1)

    else:
        parser.print_help()