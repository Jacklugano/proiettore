"""
Video player controller using MPV
"""
import subprocess
import os
import logging
from typing import Optional, List

logger = logging.getLogger(__name__)


class VideoPlayer:
    """Controls video playback using MPV player"""

    def __init__(self, volume: int = 100):
        self.process: Optional[subprocess.Popen] = None
        self.current_video: Optional[str] = None
        self.playlist: List[str] = []
        self.current_index: int = 0
        self.volume = volume
        self.is_playing = False
        self.is_paused = False

    def play(self, video_path: str) -> bool:
        """
        Play a video file

        Args:
            video_path: Path to the video file

        Returns:
            True if playback started successfully, False otherwise
        """
        try:
            if not os.path.exists(video_path):
                logger.error(f"Video file not found: {video_path}")
                return False

            self.stop()

            # MPV command for Raspberry Pi
            # Uses HDMI for video and auto for audio (will use default audio output)
            cmd = [
                'mpv',
                '--fs',  # Fullscreen
                '--no-osc',  # No on-screen controller
                '--no-input-default-bindings',  # Disable keyboard controls
                f'--volume={self.volume}',
                '--audio-device=auto',  # Auto select audio device
                '--vo=gpu',  # GPU video output (better for RPi5)
                video_path
            ]

            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

            self.current_video = video_path
            self.is_playing = True
            self.is_paused = False

            logger.info(f"Started playing: {video_path}")
            return True

        except Exception as e:
            logger.error(f"Error playing video: {e}")
            return False

    def stop(self) -> bool:
        """Stop current playback"""
        try:
            if self.process:
                self.process.terminate()
                self.process.wait(timeout=5)
                self.process = None

            self.current_video = None
            self.is_playing = False
            self.is_paused = False

            logger.info("Playback stopped")
            return True

        except Exception as e:
            logger.error(f"Error stopping playback: {e}")
            if self.process:
                self.process.kill()
                self.process = None
            return False

    def pause(self) -> bool:
        """Pause/resume playback"""
        try:
            if self.process and self.is_playing:
                # Send pause command via echo to mpv's input
                subprocess.run(['killall', '-USR1', 'mpv'], check=False)
                self.is_paused = not self.is_paused
                logger.info(f"Playback {'paused' if self.is_paused else 'resumed'}")
                return True
            return False

        except Exception as e:
            logger.error(f"Error toggling pause: {e}")
            return False

    def set_volume(self, volume: int) -> bool:
        """
        Set playback volume

        Args:
            volume: Volume level (0-100)
        """
        try:
            self.volume = max(0, min(100, volume))
            # Volume will be applied to next video
            logger.info(f"Volume set to: {self.volume}")
            return True

        except Exception as e:
            logger.error(f"Error setting volume: {e}")
            return False

    def load_playlist(self, videos: List[str]) -> bool:
        """
        Load a playlist of videos

        Args:
            videos: List of video file paths
        """
        try:
            self.playlist = [v for v in videos if os.path.exists(v)]
            self.current_index = 0
            logger.info(f"Loaded playlist with {len(self.playlist)} videos")
            return True

        except Exception as e:
            logger.error(f"Error loading playlist: {e}")
            return False

    def play_next(self) -> bool:
        """Play next video in playlist"""
        if not self.playlist:
            return False

        self.current_index = (self.current_index + 1) % len(self.playlist)
        return self.play(self.playlist[self.current_index])

    def play_previous(self) -> bool:
        """Play previous video in playlist"""
        if not self.playlist:
            return False

        self.current_index = (self.current_index - 1) % len(self.playlist)
        return self.play(self.playlist[self.current_index])

    def get_status(self) -> dict:
        """Get current player status"""
        return {
            'is_playing': self.is_playing,
            'is_paused': self.is_paused,
            'current_video': self.current_video,
            'volume': self.volume,
            'playlist_length': len(self.playlist),
            'current_index': self.current_index
        }

    def is_alive(self) -> bool:
        """Check if player process is alive"""
        if self.process:
            return self.process.poll() is None
        return False
