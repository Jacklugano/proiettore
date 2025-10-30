"""
Playlist Manager for multiple named playlists with persistent cache
"""
import os
import json
import shutil
import logging
from typing import List, Dict, Optional
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

# Base directory for all playlists
# Use absolute path from project root to ensure it's always accessible
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
PLAYLISTS_BASE_DIR = os.path.join(PROJECT_ROOT, 'playlists')

logger.info(f"Playlist base directory: {PLAYLISTS_BASE_DIR}")


class PlaylistManager:
    """Manages multiple named playlists with persistent local cache"""

    def __init__(self):
        """Initialize playlist manager"""
        self.base_dir = PLAYLISTS_BASE_DIR
        self._ensure_base_dir()

    def _ensure_base_dir(self):
        """Ensure playlists base directory exists"""
        try:
            os.makedirs(self.base_dir, mode=0o755, exist_ok=True)

            # Verify directory is writable
            test_file = os.path.join(self.base_dir, '.test')
            try:
                with open(test_file, 'w') as f:
                    f.write('test')
                os.remove(test_file)
                logger.info(f"✅ Playlists directory ready: {self.base_dir}")
            except Exception as e:
                logger.error(f"❌ Playlists directory not writable: {self.base_dir}")
                logger.error(f"   Error: {e}")

        except Exception as e:
            logger.error(f"❌ Error creating playlists directory: {self.base_dir}")
            logger.error(f"   Error: {e}")

    def _sanitize_name(self, name: str) -> str:
        """Sanitize playlist name for filesystem"""
        # Remove invalid characters
        invalid_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
        sanitized = name
        for char in invalid_chars:
            sanitized = sanitized.replace(char, '_')
        return sanitized.strip()

    def _get_playlist_dir(self, name: str) -> str:
        """Get directory path for a playlist"""
        sanitized_name = self._sanitize_name(name)
        return os.path.join(self.base_dir, sanitized_name)

    def _get_cache_dir(self, name: str) -> str:
        """Get cache directory path for a playlist"""
        return os.path.join(self._get_playlist_dir(name), 'cache')

    def _get_metadata_file(self, name: str) -> str:
        """Get metadata file path for a playlist"""
        return os.path.join(self._get_playlist_dir(name), 'playlist.json')

    def list_playlists(self) -> List[Dict]:
        """
        List all saved playlists with metadata

        Returns:
            List of playlist dictionaries with name, video_count, size, etc.
        """
        playlists = []

        try:
            if not os.path.exists(self.base_dir):
                return []

            for item in os.listdir(self.base_dir):
                playlist_dir = os.path.join(self.base_dir, item)
                if os.path.isdir(playlist_dir):
                    metadata_file = os.path.join(playlist_dir, 'playlist.json')

                    if os.path.exists(metadata_file):
                        try:
                            with open(metadata_file, 'r') as f:
                                metadata = json.load(f)

                            # Calculate cache size
                            cache_dir = os.path.join(playlist_dir, 'cache')
                            cache_size = 0
                            cached_count = 0

                            if os.path.exists(cache_dir):
                                for file in os.listdir(cache_dir):
                                    file_path = os.path.join(cache_dir, file)
                                    if os.path.isfile(file_path):
                                        cache_size += os.path.getsize(file_path)
                                        cached_count += 1

                            playlists.append({
                                'name': metadata.get('name', item),
                                'video_count': len(metadata.get('videos', [])),
                                'cached_count': cached_count,
                                'cache_size_mb': round(cache_size / (1024 * 1024), 2),
                                'created_at': metadata.get('created_at', 'Unknown'),
                                'updated_at': metadata.get('updated_at', 'Unknown')
                            })
                        except Exception as e:
                            logger.error(f"Error reading playlist {item}: {e}")

            return sorted(playlists, key=lambda x: x.get('updated_at', ''), reverse=True)

        except Exception as e:
            logger.error(f"Error listing playlists: {e}")
            return []

    def save_playlist(self, name: str, video_paths: List[str]) -> bool:
        """
        Save a playlist with name and cache videos locally

        Args:
            name: Playlist name
            video_paths: List of video file paths

        Returns:
            True if successful
        """
        try:
            logger.info(f"Saving playlist '{name}' with {len(video_paths)} videos...")

            # Create playlist directory
            playlist_dir = self._get_playlist_dir(name)
            cache_dir = self._get_cache_dir(name)

            os.makedirs(playlist_dir, exist_ok=True)
            os.makedirs(cache_dir, exist_ok=True)

            # Clear old cache for this playlist
            self._clear_playlist_cache(name)

            # Cache videos
            cached_videos = []
            for idx, original_path in enumerate(video_paths, 1):
                try:
                    if not os.path.exists(original_path):
                        logger.warning(f"Video not found, skipping: {original_path}")
                        continue

                    filename = os.path.basename(original_path)
                    cache_path = os.path.join(cache_dir, filename)

                    # Handle duplicate filenames
                    if os.path.exists(cache_path):
                        base, ext = os.path.splitext(filename)
                        cache_path = os.path.join(cache_dir, f"{base}_{idx}{ext}")

                    logger.info(f"Caching {idx}/{len(video_paths)}: {filename}")
                    shutil.copy2(original_path, cache_path)

                    cached_videos.append({
                        'original_path': original_path,
                        'cache_path': cache_path,
                        'filename': os.path.basename(cache_path)
                    })

                except Exception as e:
                    logger.error(f"Error caching {original_path}: {e}")

            # Save metadata
            now = datetime.now().isoformat()
            metadata = {
                'name': name,
                'videos': cached_videos,
                'video_count': len(cached_videos),
                'created_at': now,
                'updated_at': now
            }

            metadata_file = self._get_metadata_file(name)
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)

            logger.info(f"✅ Playlist '{name}' saved successfully ({len(cached_videos)} videos)")
            return True

        except Exception as e:
            logger.error(f"Error saving playlist '{name}': {e}")
            return False

    def load_playlist(self, name: str) -> Optional[Dict]:
        """
        Load a playlist by name

        Args:
            name: Playlist name

        Returns:
            Playlist metadata with cached video paths, or None if not found
        """
        try:
            metadata_file = self._get_metadata_file(name)

            if not os.path.exists(metadata_file):
                logger.warning(f"Playlist '{name}' not found")
                return None

            with open(metadata_file, 'r') as f:
                metadata = json.load(f)

            # Verify cached videos still exist
            valid_videos = []
            for video in metadata.get('videos', []):
                cache_path = video.get('cache_path')
                if os.path.exists(cache_path):
                    valid_videos.append(cache_path)
                else:
                    logger.warning(f"Cached video not found: {cache_path}")

            logger.info(f"Loaded playlist '{name}' with {len(valid_videos)}/{metadata.get('video_count', 0)} videos")

            return {
                'name': name,
                'videos': valid_videos,
                'metadata': metadata
            }

        except Exception as e:
            logger.error(f"Error loading playlist '{name}': {e}")
            return None

    def delete_playlist(self, name: str) -> bool:
        """
        Delete a playlist and its cache

        Args:
            name: Playlist name

        Returns:
            True if successful
        """
        try:
            playlist_dir = self._get_playlist_dir(name)

            if not os.path.exists(playlist_dir):
                logger.warning(f"Playlist '{name}' not found")
                return False

            # Delete entire playlist directory (metadata + cache)
            shutil.rmtree(playlist_dir)

            logger.info(f"✅ Playlist '{name}' deleted successfully")
            return True

        except Exception as e:
            logger.error(f"Error deleting playlist '{name}': {e}")
            return False

    def _clear_playlist_cache(self, name: str):
        """Clear cache for a specific playlist"""
        try:
            cache_dir = self._get_cache_dir(name)

            if os.path.exists(cache_dir):
                for filename in os.listdir(cache_dir):
                    file_path = os.path.join(cache_dir, filename)
                    try:
                        if os.path.isfile(file_path):
                            os.unlink(file_path)
                    except Exception as e:
                        logger.error(f"Error deleting cached file {filename}: {e}")

                logger.debug(f"Cache cleared for playlist '{name}'")

        except Exception as e:
            logger.error(f"Error clearing cache for playlist '{name}': {e}")

    def get_total_cache_size(self) -> Dict:
        """
        Get total cache size across all playlists

        Returns:
            Dictionary with cache statistics
        """
        try:
            total_size = 0
            total_files = 0

            if os.path.exists(self.base_dir):
                for root, dirs, files in os.walk(self.base_dir):
                    for file in files:
                        if file.endswith(('.mp4', '.avi', '.mkv', '.mov')):  # Video files
                            file_path = os.path.join(root, file)
                            total_size += os.path.getsize(file_path)
                            total_files += 1

            return {
                'total_size_mb': round(total_size / (1024 * 1024), 2),
                'total_size_gb': round(total_size / (1024 * 1024 * 1024), 2),
                'total_files': total_files
            }

        except Exception as e:
            logger.error(f"Error getting total cache size: {e}")
            return {'total_size_mb': 0, 'total_size_gb': 0, 'total_files': 0}
