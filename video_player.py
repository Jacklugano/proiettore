"""
Video player controller using MPV
"""
import subprocess
import os
import logging
import time
import threading
import json
from typing import Optional, List, Dict
from hdmi_manager import HDMIManager
from session_manager import SessionManager
from video_cache import VideoCache

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
        self.hdmi_manager = HDMIManager()
        self.session_manager = SessionManager()
        self.video_cache = VideoCache()
        self.auto_save_session = True  # Auto-save session on changes
        self.original_to_cache: Dict[str, str] = {}  # Mapping original paths to cache paths
        self.loop_playlist = True  # Auto-play next video and loop playlist
        self.monitor_thread: Optional[threading.Thread] = None
        self.monitor_stop_event = threading.Event()

        # MPV IPC socket for playback progress
        self.ipc_socket_path = '/tmp/mpv-socket'
        self.playback_position = 0.0  # Current position in seconds
        self.playback_duration = 0.0  # Total duration in seconds
        self.video_metadata = {}  # Video metadata from ffprobe

        # Clear cache on initialization (fresh start)
        self.video_cache.clear_cache()

        # Set black screen on initialization
        self._set_black_screen()

    def play(self, video_path: str, skip_hdmi_check: bool = False, from_monitor: bool = False) -> bool:
        """
        Play a video file

        Args:
            video_path: Path to the video file
            skip_hdmi_check: Skip HDMI connection check (for testing)
            from_monitor: True if called from monitor thread (don't restart monitor)

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

            # Clear black screen to allow video to be visible
            self._clear_black_screen()

            # Get video metadata before playing
            self.video_metadata = self._get_video_metadata(video_path)
            self.playback_duration = self.video_metadata.get('duration', 0.0)
            self.playback_position = 0.0

            # Remove old IPC socket if exists
            if os.path.exists(self.ipc_socket_path):
                try:
                    os.remove(self.ipc_socket_path)
                except:
                    pass

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
                '--drm-device=/dev/dri/card1',  # Use DRM card1 (where HDMI is connected)
                '--drm-connector=HDMI-A-1',  # Use HDMI output
                f'--input-ipc-server={self.ipc_socket_path}',  # IPC socket for progress
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

            # Start monitor thread to auto-play next video when current finishes
            # (unless called from monitor thread itself to avoid stopping itself)
            if not from_monitor:
                self._start_monitor_thread()

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
            # Stop monitor thread
            self._stop_monitor_thread()

            if self.process:
                self.process.terminate()
                self.process.wait(timeout=5)
                self.process = None

            self.current_video = None
            self.is_playing = False
            self.is_paused = False

            # Set black screen after stopping playback
            self._set_black_screen()

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
            # Still try to set black screen even on error
            self._set_black_screen()
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
        Load a playlist of videos and cache them locally

        Args:
            videos: List of video file paths (from network share)
        """
        try:
            logger.info(f"load_playlist called with {len(videos)} videos")

            # Filter existing videos
            existing_videos = [v for v in videos if os.path.exists(v)]

            if not existing_videos:
                logger.warning("No valid videos found in playlist")
                return False

            # Maximum 20 videos per playlist (cache limit)
            if len(existing_videos) > 20:
                logger.error(f"Too many videos in playlist! Maximum 20, received {len(existing_videos)}")
                return False

            logger.info(f"Loading playlist with {len(existing_videos)} existing videos:")
            for idx, video in enumerate(existing_videos, 1):
                logger.info(f"  {idx}. {os.path.basename(video)}")

            # Cache all videos in playlist
            self.original_to_cache = self.video_cache.cache_playlist(existing_videos)

            # Update playlist to use cached paths
            self.playlist = list(self.original_to_cache.values())
            self.current_index = 0

            # Save playlist to file for persistence (use original paths)
            self.save_playlist_to_file(existing_videos)

            logger.info(f"Playlist loaded with {len(self.playlist)} cached videos")
            return True

        except Exception as e:
            logger.error(f"Error loading playlist: {e}")
            return False

    def play_next(self, from_monitor: bool = False) -> bool:
        """Play next video in playlist

        Args:
            from_monitor: True if called from monitor thread
        """
        if not self.playlist:
            return False

        self.current_index = (self.current_index + 1) % len(self.playlist)
        return self.play(self.playlist[self.current_index], from_monitor=from_monitor)

    def play_previous(self) -> bool:
        """Play previous video in playlist"""
        if not self.playlist:
            return False

        self.current_index = (self.current_index - 1) % len(self.playlist)
        return self.play(self.playlist[self.current_index])

    def save_playlist_to_file(self, video_paths: List[str]) -> bool:
        """
        Save playlist to JSON file for persistence

        Args:
            video_paths: List of original video paths (not cached paths)

        Returns:
            True if successful, False otherwise
        """
        try:
            playlist_file = os.path.join(os.path.dirname(__file__), 'playlist.json')

            with open(playlist_file, 'w') as f:
                json.dump({
                    'version': '1.0',
                    'videos': video_paths
                }, f, indent=2)

            logger.info(f"Playlist saved to {playlist_file} ({len(video_paths)} videos)")
            return True

        except Exception as e:
            logger.error(f"Error saving playlist to file: {e}")
            return False

    def load_playlist_from_file(self) -> List[str]:
        """
        Load playlist from JSON file

        Returns:
            List of video paths, empty list if file doesn't exist or error occurs
        """
        try:
            playlist_file = os.path.join(os.path.dirname(__file__), 'playlist.json')

            if not os.path.exists(playlist_file):
                logger.debug(f"Playlist file not found: {playlist_file}")
                return []

            with open(playlist_file, 'r') as f:
                data = json.load(f)

            videos = data.get('videos', [])
            logger.info(f"Playlist loaded from file ({len(videos)} videos)")

            return videos

        except Exception as e:
            logger.error(f"Error loading playlist from file: {e}")
            return []

    def _get_video_metadata(self, video_path: str) -> dict:
        """
        Get video metadata using ffprobe

        Args:
            video_path: Path to video file

        Returns:
            Dictionary with duration, resolution, size, etc.
        """
        metadata = {
            'duration': 0.0,
            'width': 0,
            'height': 0,
            'size': 0,
            'filename': os.path.basename(video_path)
        }

        try:
            # Get file size
            if os.path.exists(video_path):
                metadata['size'] = os.path.getsize(video_path)

            # Use ffprobe to get video metadata
            cmd = [
                '/usr/bin/ffprobe',
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_format',
                '-show_streams',
                video_path
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)

            if result.returncode == 0:
                data = json.loads(result.stdout)

                # Get duration from format
                if 'format' in data and 'duration' in data['format']:
                    metadata['duration'] = float(data['format']['duration'])

                # Get resolution from first video stream
                if 'streams' in data:
                    for stream in data['streams']:
                        if stream.get('codec_type') == 'video':
                            metadata['width'] = stream.get('width', 0)
                            metadata['height'] = stream.get('height', 0)
                            break

            logger.debug(f"Video metadata: {metadata}")

        except Exception as e:
            logger.error(f"Error getting video metadata: {e}")

        return metadata

    def _update_playback_position(self):
        """Update current playback position from MPV IPC socket"""
        try:
            import socket as sock

            if not os.path.exists(self.ipc_socket_path):
                return

            # Connect to MPV IPC socket
            client = sock.socket(sock.AF_UNIX, sock.SOCK_STREAM)
            client.settimeout(0.5)
            client.connect(self.ipc_socket_path)

            # Request time-pos property
            request = json.dumps({"command": ["get_property", "time-pos"]}) + '\n'
            client.send(request.encode('utf-8'))

            # Read response
            response = client.recv(4096).decode('utf-8')
            data = json.loads(response)

            if 'data' in data and data['data'] is not None:
                self.playback_position = float(data['data'])

            client.close()

        except Exception as e:
            # Socket errors are expected if MPV not ready yet
            pass

    def get_status(self) -> dict:
        """Get current player status"""
        # Update playback position if playing
        if self.is_playing:
            self._update_playback_position()

        return {
            'is_playing': self.is_playing,
            'is_paused': self.is_paused,
            'current_video': self.current_video,
            'volume': self.volume,
            'playlist_length': len(self.playlist),
            'current_index': self.current_index,
            'playback_position': self.playback_position,
            'playback_duration': self.playback_duration,
            'video_metadata': self.video_metadata
        }

    def get_cache_status(self) -> dict:
        """Get video cache status"""
        return self.video_cache.get_cache_status()

    def is_alive(self) -> bool:
        """Check if player process is alive"""
        if self.process:
            return self.process.poll() is None
        return False

    def _set_black_screen(self):
        """Set black screen on TTY (hide console, show black)"""
        try:
            # Clear the screen and hide cursor
            subprocess.run([
                'sh', '-c',
                'setterm -cursor off -blank force > /dev/tty0 2>/dev/null || true'
            ], check=False, timeout=1)

            # Alternative: blank the framebuffer if setterm doesn't work
            try:
                with open('/sys/class/graphics/fb0/blank', 'w') as f:
                    f.write('1')  # 1 = blank/black screen
            except:
                pass

            logger.debug("Black screen activated")
        except Exception as e:
            logger.debug(f"Could not set black screen: {e}")

    def _clear_black_screen(self):
        """Clear black screen (unblank)"""
        try:
            # Unblank the framebuffer
            try:
                with open('/sys/class/graphics/fb0/blank', 'w') as f:
                    f.write('0')  # 0 = unblank
            except:
                pass

            logger.debug("Black screen cleared")
        except Exception as e:
            logger.debug(f"Could not clear black screen: {e}")

    def _start_monitor_thread(self):
        """Start background thread to monitor MPV process and auto-play next video"""
        self._stop_monitor_thread()  # Stop any existing thread
        self.monitor_stop_event.clear()
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        logger.debug("Process monitor thread started")

    def _stop_monitor_thread(self):
        """Stop process monitor thread"""
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_stop_event.set()
            self.monitor_thread.join(timeout=2)
            logger.debug("Process monitor thread stopped")

    def _monitor_loop(self):
        """Background loop that monitors MPV process and auto-plays next video"""
        try:
            while not self.monitor_stop_event.is_set():
                # Check if process is still running
                if self.process and self.process.poll() is not None:
                    # Process has finished, check exit code
                    exit_code = self.process.returncode
                    video_name = os.path.basename(self.current_video) if self.current_video else 'unknown'

                    if exit_code == 0:
                        # Normal termination (video finished successfully)
                        logger.info(f"Video finished successfully: {video_name}")
                    else:
                        # Error termination (video playback error)
                        logger.error(f"Video playback error (exit code {exit_code}): {video_name}")
                        logger.warning(f"Skipping to next video due to playback error")

                    # Only auto-play next if loop is enabled and there's a playlist
                    if self.loop_playlist and self.playlist:
                        logger.info("Auto-playing next video in playlist...")
                        # Use play_next which handles looping with modulo
                        # Pass from_monitor=True to avoid restarting this monitor thread
                        self.play_next(from_monitor=True)
                        # Don't break - continue monitoring the new process
                        logger.debug("Continuing to monitor next video...")
                    else:
                        # No loop or no playlist, just stop
                        logger.info("Playback finished, no auto-play")
                        self.is_playing = False
                        self._set_black_screen()
                        break

                # Check every second
                time.sleep(1)
        except Exception as e:
            logger.error(f"Error in monitor loop: {e}")

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
