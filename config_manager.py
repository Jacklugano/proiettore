"""
Configuration manager for storing and retrieving settings from database
"""
import sqlite3
import logging
from typing import Optional, Dict
from config import Config

logger = logging.getLogger(__name__)


class ConfigManager:
    """Manages application configuration in database"""

    def __init__(self, db_path: str = None):
        self.db_path = db_path or Config.DATABASE_PATH
        self._init_database()

    def _init_database(self):
        """Initialize configuration table"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            conn.commit()
            conn.close()
            logger.info("Configuration database initialized")

        except Exception as e:
            logger.error(f"Error initializing configuration database: {e}")

    def get_setting(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Get a configuration setting"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('SELECT value FROM settings WHERE key = ?', (key,))
            row = cursor.fetchone()
            conn.close()

            return row[0] if row else default

        except Exception as e:
            logger.error(f"Error getting setting {key}: {e}")
            return default

    def set_setting(self, key: str, value: str) -> bool:
        """Set a configuration setting"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                INSERT OR REPLACE INTO settings (key, value, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
            ''', (key, value))

            conn.commit()
            conn.close()

            logger.info(f"Setting updated: {key}")
            return True

        except Exception as e:
            logger.error(f"Error setting {key}: {e}")
            return False

    def get_all_settings(self) -> Dict[str, str]:
        """Get all configuration settings"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute('SELECT key, value FROM settings')
            rows = cursor.fetchall()
            conn.close()

            return {row['key']: row['value'] for row in rows}

        except Exception as e:
            logger.error(f"Error getting all settings: {e}")
            return {}

    def get_network_config(self) -> Dict[str, str]:
        """Get network share configuration"""
        return {
            'share_path': self.get_setting('network_share_path', ''),
            'username': self.get_setting('network_share_user', ''),
            'password': self.get_setting('network_share_password', ''),
            'mount_point': self.get_setting('network_share_mount_point', '/mnt/network_videos')
        }

    def set_network_config(self, share_path: str, username: str = '', password: str = '', mount_point: str = '/mnt/network_videos') -> bool:
        """Set network share configuration"""
        try:
            self.set_setting('network_share_path', share_path)
            self.set_setting('network_share_user', username)
            self.set_setting('network_share_password', password)
            self.set_setting('network_share_mount_point', mount_point)

            logger.info("Network configuration updated")
            return True

        except Exception as e:
            logger.error(f"Error setting network config: {e}")
            return False

    def get_player_config(self) -> Dict[str, any]:
        """Get player configuration"""
        return {
            'volume': int(self.get_setting('volume', '100')),
            'loop_playlist': self.get_setting('loop_playlist', 'false') == 'true',
            'auto_start': self.get_setting('auto_start', 'false') == 'true',
            'video_extensions': self.get_setting('video_extensions', 'mp4,avi,mkv,mov,wmv,flv,webm')
        }

    def set_player_config(self, volume: int = None, loop_playlist: bool = None, auto_start: bool = None, video_extensions: str = None) -> bool:
        """Set player configuration"""
        try:
            if volume is not None:
                self.set_setting('volume', str(volume))

            if loop_playlist is not None:
                self.set_setting('loop_playlist', 'true' if loop_playlist else 'false')

            if auto_start is not None:
                self.set_setting('auto_start', 'true' if auto_start else 'false')

            if video_extensions is not None:
                self.set_setting('video_extensions', video_extensions)

            logger.info("Player configuration updated")
            return True

        except Exception as e:
            logger.error(f"Error setting player config: {e}")
            return False

    def delete_setting(self, key: str) -> bool:
        """Delete a configuration setting"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('DELETE FROM settings WHERE key = ?', (key,))
            conn.commit()
            conn.close()

            logger.info(f"Setting deleted: {key}")
            return True

        except Exception as e:
            logger.error(f"Error deleting setting {key}: {e}")
            return False

    def reset_all_settings(self) -> bool:
        """Reset all settings to defaults"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('DELETE FROM settings')
            conn.commit()
            conn.close()

            logger.info("All settings reset")
            return True

        except Exception as e:
            logger.error(f"Error resetting settings: {e}")
            return False
