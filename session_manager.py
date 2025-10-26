"""
Session manager for saving and restoring playback state
"""
import json
import os
import logging
from typing import Optional, Dict, List
from datetime import datetime

logger = logging.getLogger(__name__)

SESSION_FILE = '/tmp/proiettore_session.json'


class SessionManager:
    """Manages playback session persistence"""

    @staticmethod
    def save_session(
        playlist: List[str],
        current_index: int,
        current_video: Optional[str],
        is_playing: bool,
        is_paused: bool,
        volume: int
    ) -> bool:
        """
        Save current playback session to file

        Args:
            playlist: List of video paths in playlist
            current_index: Current position in playlist
            current_video: Path to currently playing video
            is_playing: Whether player is currently playing
            is_paused: Whether player is paused
            volume: Current volume level

        Returns:
            True if save successful, False otherwise
        """
        try:
            session_data = {
                'timestamp': datetime.now().isoformat(),
                'playlist': playlist,
                'current_index': current_index,
                'current_video': current_video,
                'is_playing': is_playing,
                'is_paused': is_paused,
                'volume': volume
            }

            with open(SESSION_FILE, 'w') as f:
                json.dump(session_data, f, indent=2)

            logger.info(f"Session saved: {len(playlist)} videos, index {current_index}")
            return True

        except Exception as e:
            logger.error(f"Error saving session: {e}")
            return False

    @staticmethod
    def load_session() -> Optional[Dict]:
        """
        Load saved playback session from file

        Returns:
            Dictionary with session data if exists, None otherwise
        """
        try:
            if not os.path.exists(SESSION_FILE):
                logger.info("No saved session found")
                return None

            with open(SESSION_FILE, 'r') as f:
                session_data = json.load(f)

            # Check if session is not too old (e.g., less than 24 hours)
            timestamp = datetime.fromisoformat(session_data['timestamp'])
            age_hours = (datetime.now() - timestamp).total_seconds() / 3600

            if age_hours > 24:
                logger.info(f"Session too old ({age_hours:.1f} hours), ignoring")
                SessionManager.clear_session()
                return None

            logger.info(f"Session loaded: {len(session_data['playlist'])} videos, index {session_data['current_index']}")
            return session_data

        except Exception as e:
            logger.error(f"Error loading session: {e}")
            return None

    @staticmethod
    def clear_session() -> bool:
        """
        Clear saved session file

        Returns:
            True if clear successful, False otherwise
        """
        try:
            if os.path.exists(SESSION_FILE):
                os.unlink(SESSION_FILE)
                logger.info("Session cleared")
            return True

        except Exception as e:
            logger.error(f"Error clearing session: {e}")
            return False

    @staticmethod
    def session_exists() -> bool:
        """
        Check if a saved session exists

        Returns:
            True if session file exists, False otherwise
        """
        return os.path.exists(SESSION_FILE)
