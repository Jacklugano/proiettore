"""
Video player controller using MPV
"""
import subprocess
import os
import logging
import threading
import time
import json
from typing import Optional, List
from hdmi_manager import HDMIManager
from session_manager import SessionManager

logger = logging.getLogger(__name__)

# Path for preview screenshot
PREVIEW_SCREENSHOT_PATH = '/tmp/proiettore_preview.jpg'
MPV_SOCKET_PATH = '/tmp/mpv-socket-proiettore'


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
        self.screenshot_thread: Optional[threading.Thread] = None
        self.screenshot_stop_event = threading.Event()
        self.hdmi_manager = HDMIManager()
        self.session_manager = SessionManager()
        self.auto_save_session = True  # Auto-save session on changes

    def play(self, video_path: str, skip_hdmi_check: bool = False) -> bool:
        """
        Play a video file

        Args:
            video_path: Path to the video file
            skip_hdmi_check: Skip HDMI connection check (for testing)

        Returns:
            True if playback started successfully, False otherwise
        """
        try:
            if not os.path.exists(video_path):
                logger.error(f"Video file not found: {video_path}")
                return False

            # Check HDMI connection before playing
            if not skip_hdmi_check:
                if not self.hdmi_manager.is_hdmi_connected():
                    logger.error("HDMI display not connected! Cannot start playback.")
                    return False
                else:
                    logger.info("HDMI display detected, starting playback")

            self.stop()

            # MPV command for Raspberry Pi
            # Uses DRM for direct framebuffer access (bypasses X11/desktop)
            # This ensures video is displayed fullscreen without desktop visible
            # Use full path for systemd compatibility
            cmd = [
                '/usr/bin/mpv',
                '--fs',  # Fullscreen
                '--no-osc',  # No on-screen controller
                '--no-input-default-bindings',  # Disable keyboard controls
                f'--volume={self.volume}',
                '--audio-device=auto',  # Auto select audio device
                '--vo=drm',  # DRM video output - direct to framebuffer, bypasses X11
                '--hwdec=auto',  # Hardware decode
                '--drm-connector=HDMI-A-1',  # Use HDMI output (try HDMI-A-1 first)
                f'--input-ipc-server={MPV_SOCKET_PATH}',  # IPC for screenshot control
                f'--screenshot-directory=/tmp',  # Screenshot directory
                '--screenshot-template=proiettore_preview',  # Screenshot filename
                '--screenshot-format=jpg',  # JPEG format for web
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

            # Start screenshot capture thread
            self._start_screenshot_thread()

            # Save session after starting playback
            if self.auto_save_session:
                self._save_current_session()

            logger.info(f"Started playing: {video_path}")
            return True

        except Exception as e:
            logger.error(f"Error playing video: {e}")
            return False

    def stop(self) -> bool:
        """Stop current playback"""
        try:
            # Stop screenshot thread
            self._stop_screenshot_thread()

            if self.process:
                self.process.terminate()
                self.process.wait(timeout=5)
                self.process = None

            self.current_video = None
            self.is_playing = False
            self.is_paused = False

            # Clean up socket
            if os.path.exists(MPV_SOCKET_PATH):
                try:
                    os.unlink(MPV_SOCKET_PATH)
                except:
                    pass

            # Save session after stopping
            if self.auto_save_session:
                self._save_current_session()

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

                # Save session after pause state change
                if self.auto_save_session:
                    self._save_current_session()

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

    def _start_screenshot_thread(self):
        """Start background thread for capturing screenshots"""
        self._stop_screenshot_thread()  # Stop any existing thread
        self.screenshot_stop_event.clear()
        self.screenshot_thread = threading.Thread(target=self._screenshot_loop, daemon=True)
        self.screenshot_thread.start()
        logger.info("Screenshot capture thread started")

    def _stop_screenshot_thread(self):
        """Stop screenshot capture thread"""
        if self.screenshot_thread and self.screenshot_thread.is_alive():
            self.screenshot_stop_event.set()
            self.screenshot_thread.join(timeout=2)
            logger.info("Screenshot capture thread stopped")

    def _screenshot_loop(self):
        """Background loop that captures screenshots periodically"""
        # Wait a bit for MPV to start and create the socket
        time.sleep(1)

        while not self.screenshot_stop_event.is_set():
            try:
                if self.is_playing and os.path.exists(MPV_SOCKET_PATH):
                    # Send screenshot command to MPV via IPC
                    self._send_mpv_command('screenshot')
                    logger.debug("Screenshot captured")
            except Exception as e:
                logger.error(f"Error capturing screenshot: {e}")

            # Wait 3 seconds before next screenshot
            self.screenshot_stop_event.wait(3)

    def _send_mpv_command(self, command: str):
        """Send command to MPV via IPC socket"""
        try:
            import socket
            sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            sock.connect(MPV_SOCKET_PATH)

            # MPV IPC uses JSON commands
            cmd = json.dumps({"command": [command]}) + "\n"
            sock.sendall(cmd.encode('utf-8'))
            sock.close()
        except Exception as e:
            logger.debug(f"Could not send command to MPV: {e}")

    def _save_current_session(self):
        """Save current playback session"""
        try:
            self.session_manager.save_session(
                playlist=self.playlist,
                current_index=self.current_index,
                current_video=self.current_video,
                is_playing=self.is_playing,
                is_paused=self.is_paused,
                volume=self.volume
            )
        except Exception as e:
            logger.error(f"Error saving session: {e}")

    def restore_session(self) -> bool:
        """
        Restore saved playback session

        Returns:
            True if session restored successfully, False otherwise
        """
        try:
            session = self.session_manager.load_session()
            if not session:
                logger.info("No session to restore")
                return False

            # Restore playlist
            self.playlist = session['playlist']
            self.current_index = session['current_index']
            self.volume = session['volume']

            logger.info(f"Session restored: {len(self.playlist)} videos, index {self.current_index}")

            # If was playing, resume playback
            if session['is_playing'] and session['current_video']:
                # Check if files still exist
                if os.path.exists(session['current_video']):
                    logger.info(f"Resuming playback: {session['current_video']}")
                    success = self.play(session['current_video'])

                    # If was paused, pause again
                    if success and session['is_paused']:
                        time.sleep(1)  # Wait for playback to start
                        self.pause()

                    return success
                else:
                    logger.warning(f"Saved video no longer exists: {session['current_video']}")

            return True

        except Exception as e:
            logger.error(f"Error restoring session: {e}")
            return False

    def check_hdmi_status(self) -> dict:
        """Get current HDMI connection status"""
        return self.hdmi_manager.get_hdmi_info()
