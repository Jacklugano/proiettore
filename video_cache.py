"""
Video cache manager for local caching of playlist videos
"""
import os
import shutil
import logging
from typing import List, Dict
from pathlib import Path

logger = logging.getLogger(__name__)

# Cache directory
CACHE_DIR = '/tmp/video_cache'


class VideoCache:
    """Manages local caching of video files from network share"""

    def __init__(self):
        """Initialize video cache"""
        self.cache_dir = CACHE_DIR
        self._ensure_cache_dir()

    def _ensure_cache_dir(self):
        """Ensure cache directory exists"""
        try:
            os.makedirs(self.cache_dir, exist_ok=True)
            logger.info(f"Cache directory ready: {self.cache_dir}")
        except Exception as e:
            logger.error(f"Error creating cache directory: {e}")

    def cache_playlist(self, video_paths: List[str]) -> Dict[str, str]:
        """
        Cache all videos in playlist to local storage

        Args:
            video_paths: List of original video file paths

        Returns:
            Dictionary mapping original paths to cached paths
        """
        logger.info(f"Starting cache of {len(video_paths)} videos...")

        # Clear old cache before caching new playlist
        self.clear_cache()

        cached_paths = {}

        for idx, original_path in enumerate(video_paths, 1):
            try:
                if not os.path.exists(original_path):
                    logger.warning(f"Video not found, skipping: {original_path}")
                    continue

                # Generate cache filename (preserve original filename)
                filename = os.path.basename(original_path)
                cache_path = os.path.join(self.cache_dir, filename)

                # Handle duplicate filenames
                if os.path.exists(cache_path):
                    base, ext = os.path.splitext(filename)
                    cache_path = os.path.join(self.cache_dir, f"{base}_{idx}{ext}")

                logger.info(f"Caching video {idx}/{len(video_paths)}: {filename}")

                # Copy file to cache
                shutil.copy2(original_path, cache_path)

                cached_paths[original_path] = cache_path
                logger.info(f"Cached: {filename} -> {cache_path}")

            except Exception as e:
                logger.error(f"Error caching {original_path}: {e}")
                # Use original path as fallback
                cached_paths[original_path] = original_path

        logger.info(f"Cache complete: {len(cached_paths)}/{len(video_paths)} videos cached")
        return cached_paths

    def clear_cache(self):
        """Clear all cached videos"""
        try:
            if os.path.exists(self.cache_dir):
                # Remove all files in cache directory
                for filename in os.listdir(self.cache_dir):
                    file_path = os.path.join(self.cache_dir, filename)
                    try:
                        if os.path.isfile(file_path):
                            os.unlink(file_path)
                            logger.debug(f"Deleted cached file: {filename}")
                    except Exception as e:
                        logger.error(f"Error deleting {filename}: {e}")

                logger.info("Cache cleared")
            else:
                logger.debug("Cache directory does not exist, nothing to clear")

        except Exception as e:
            logger.error(f"Error clearing cache: {e}")

    def get_cache_status(self) -> Dict:
        """
        Get cache status information

        Returns:
            Dictionary with cache statistics
        """
        try:
            if not os.path.exists(self.cache_dir):
                return {
                    'exists': False,
                    'video_count': 0,
                    'total_size_mb': 0,
                    'files': []
                }

            files = []
            total_size = 0

            for filename in os.listdir(self.cache_dir):
                file_path = os.path.join(self.cache_dir, filename)
                if os.path.isfile(file_path):
                    size = os.path.getsize(file_path)
                    total_size += size
                    files.append({
                        'name': filename,
                        'size_mb': round(size / (1024 * 1024), 2)
                    })

            return {
                'exists': True,
                'video_count': len(files),
                'total_size_mb': round(total_size / (1024 * 1024), 2),
                'files': files
            }

        except Exception as e:
            logger.error(f"Error getting cache status: {e}")
            return {
                'exists': False,
                'video_count': 0,
                'total_size_mb': 0,
                'files': [],
                'error': str(e)
            }

    def is_cached(self, video_path: str) -> bool:
        """
        Check if a video is in cache

        Args:
            video_path: Path to check (original or cached)

        Returns:
            True if video exists in cache
        """
        if video_path.startswith(self.cache_dir):
            return os.path.exists(video_path)

        # Check if original filename exists in cache
        filename = os.path.basename(video_path)
        cache_path = os.path.join(self.cache_dir, filename)
        return os.path.exists(cache_path)
