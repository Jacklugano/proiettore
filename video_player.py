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
        self.last_position_update = 0.0  # Track last position for watchdog
        self.position_stuck_count = 0  # Count how many times position hasn't changed
        self.video_start_time = 0.0  # When current video started playing
        self.transition_duration = 1.5  # Black screen transition between videos (seconds)

        # Screensaver management
        self.screensaver_process: Optional[subprocess.Popen] = None
        self.screensaver_enabled = True  # Enable/disable screensaver feature
        self.screensaver_delay = 2  # Seconds to wait before showing screensaver after stop

        # Black screen framebuffer process
        self.black_screen_process: Optional[subprocess.Popen] = None
        self.black_image_path = os.path.join(os.path.dirname(__file__), 'black.png')

        # Clear cache on initialization (fresh start)
        self.video_cache.clear_cache()

        # Hide terminal permanently on startup
        self._hide_terminal_permanently()

        # Set black screen on initialization
        self._set_black_screen()

        # Start screensaver initially (player is idle on startup)
        if self.screensaver_enabled:
            threading.Timer(self.screensaver_delay, self._start_screensaver).start()

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

            # Stop screensaver if running
            self._stop_screensaver()

            # Only stop previous playback if NOT called from monitor
            # (monitor thread already knows previous video finished)
            if not from_monitor:
                self.stop()
            else:
                # Just terminate the old process if it exists, don't stop monitor
                if self.process:
                    try:
                        self.process.terminate()
                        self.process.wait(timeout=1)
                    except:
                        try:
                            self.process.kill()
                        except:
                            pass
                    self.process = None

            # Clear black screen to allow video to be visible
            self._clear_black_screen()

            # Get video metadata before playing
            self.video_metadata = self._get_video_metadata(video_path)
            self.playback_duration = self.video_metadata.get('duration', 0.0)
            self.playback_position = 0.0

            # Reset watchdog counters for new video
            self.last_position_update = 0.0
            self.position_stuck_count = 0
            self.video_start_time = time.time()

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

            # Start screensaver after a short delay
            if self.screensaver_enabled:
                threading.Timer(self.screensaver_delay, self._start_screensaver).start()

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

    def _hide_terminal_permanently(self):
        """
        Hide terminal cursor and clear screen permanently on startup.
        This prevents the terminal from ever being visible during transitions.
        """
        try:
            logger.info("Hiding terminal permanently on all TTYs...")

            # Hide cursor and clear screen on all TTYs
            for tty in ['/dev/tty0', '/dev/tty1', '/dev/console']:
                try:
                    subprocess.run([
                        'sh', '-c',
                        # Clear screen, hide cursor permanently, disable screen blanking timeout
                        f'printf "\\033[2J\\033[H\\033[?25l" > {tty} 2>/dev/null; '
                        f'setterm -cursor off -blank 0 -powerdown 0 > {tty} 2>/dev/null'
                    ], check=False, timeout=2)
                    logger.debug(f"Terminal hidden on {tty}")
                except Exception as e:
                    logger.debug(f"Could not hide terminal on {tty}: {e}")

            logger.info("Terminal permanently hidden")
        except Exception as e:
            logger.error(f"Error hiding terminal permanently: {e}")

    def _set_black_screen(self):
        """Set black screen on TTY (hide console, show black) using framebuffer"""
        try:
            # Multiple approaches to ensure terminal is completely hidden:

            # 1. Clear terminal, hide cursor, and blank screen on all TTYs
            for tty in ['/dev/tty0', '/dev/tty1', '/dev/console']:
                try:
                    # Use ANSI escape codes for maximum compatibility:
                    # \033[2J - Clear entire screen
                    # \033[H - Move cursor to home (0,0)
                    # \033[?25l - Hide cursor
                    subprocess.run([
                        'sh', '-c',
                        f'printf "\\033[2J\\033[H\\033[?25l" > {tty} 2>/dev/null; '
                        f'setterm -cursor off > {tty} 2>/dev/null; '
                        f'setterm -blank force > {tty} 2>/dev/null'
                    ], check=False, timeout=1)
                except:
                    pass

            # 2. Show black image on framebuffer using fbi
            # This completely covers the terminal with a black image
            self._start_black_screen_display()

            logger.debug("Black screen activated (terminal hidden with framebuffer)")
        except Exception as e:
            logger.debug(f"Could not set black screen: {e}")

    def _start_black_screen_display(self):
        """Display black image on framebuffer to completely hide terminal"""
        try:
            # Stop any existing black screen display
            self._stop_black_screen_display()

            # Check if black image exists, create if not
            if not os.path.exists(self.black_image_path):
                logger.info("Creating black screen image...")
                # Try to create black image with ImageMagick
                try:
                    subprocess.run([
                        'convert', '-size', '1920x1080', 'xc:black', self.black_image_path
                    ], check=True, timeout=5, capture_output=True)
                    logger.info(f"Black image created at {self.black_image_path}")
                except (subprocess.CalledProcessError, FileNotFoundError):
                    logger.warning("ImageMagick not available, using framebuffer blank instead")
                    return

            # Use fbi to display black image on framebuffer
            # fbi writes directly to framebuffer, completely hiding terminal
            try:
                self.black_screen_process = subprocess.Popen([
                    'fbi',
                    '--noverbose',  # No verbose output
                    '--autozoom',   # Auto zoom to fit screen
                    '-T', '1',      # Use framebuffer /dev/fb0 via tty1
                    self.black_image_path
                ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                logger.debug(f"Black screen display started (PID: {self.black_screen_process.pid})")
            except FileNotFoundError:
                logger.warning("fbi not installed, cannot display black image on framebuffer")

        except Exception as e:
            logger.error(f"Error starting black screen display: {e}")

    def _stop_black_screen_display(self):
        """Stop black screen framebuffer display"""
        try:
            if self.black_screen_process:
                if self.black_screen_process.poll() is None:
                    try:
                        self.black_screen_process.terminate()
                        self.black_screen_process.wait(timeout=1)
                    except subprocess.TimeoutExpired:
                        self.black_screen_process.kill()
                        self.black_screen_process.wait(timeout=1)
                self.black_screen_process = None
                logger.debug("Black screen display stopped")
        except Exception as e:
            logger.error(f"Error stopping black screen display: {e}")

    def _clear_black_screen(self):
        """Clear black screen (stop fbi and unblank framebuffer for video playback)"""
        try:
            # Stop black screen framebuffer display (fbi)
            self._stop_black_screen_display()

            # Unblank all framebuffers to allow video display
            for fb in ['/sys/class/graphics/fb0/blank', '/sys/class/graphics/fb1/blank']:
                try:
                    if os.path.exists(fb):
                        with open(fb, 'w') as f:
                            f.write('0')  # 0 = unblank (allow display)
                except:
                    pass

            logger.debug("Black screen cleared (framebuffer unblanked for video)")
        except Exception as e:
            logger.debug(f"Could not clear black screen: {e}")

    def _start_screensaver(self):
        """Start screensaver in fullscreen kiosk mode"""
        try:
            # Don't start if player is currently playing
            if self.is_playing:
                logger.debug("Skipping screensaver - player is active")
                return

            # Don't start if already running
            if self.screensaver_process and self.screensaver_process.poll() is None:
                logger.debug("Screensaver already running")
                return

            logger.info("🎨 Starting screensaver...")

            # Get Flask server URL
            screensaver_url = "http://localhost:5000/screensaver"

            # Try chromium-browser first (more common on Raspberry Pi)
            chromium_command = [
                'chromium-browser',
                '--kiosk',
                '--noerrdialogs',
                '--disable-infobars',
                '--no-first-run',
                '--check-for-update-interval=31536000',
                '--disable-pinch',
                '--overscroll-history-navigation=0',
                screensaver_url
            ]

            try:
                # Clear black screen to show chromium
                self._clear_black_screen()

                # Start chromium in kiosk mode
                self.screensaver_process = subprocess.Popen(
                    chromium_command,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    start_new_session=True
                )

                logger.info(f"✅ Screensaver started (PID: {self.screensaver_process.pid})")

            except FileNotFoundError:
                # Try regular chromium if chromium-browser not found
                chromium_command[0] = 'chromium'
                try:
                    self.screensaver_process = subprocess.Popen(
                        chromium_command,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        start_new_session=True
                    )
                    logger.info(f"✅ Screensaver started with chromium (PID: {self.screensaver_process.pid})")
                except Exception as e:
                    logger.error(f"Failed to start screensaver with chromium: {e}")

        except Exception as e:
            logger.error(f"Error starting screensaver: {e}")

    def _stop_screensaver(self):
        """Stop screensaver if running"""
        try:
            if self.screensaver_process:
                if self.screensaver_process.poll() is None:  # Process is still running
                    logger.info("🛑 Stopping screensaver...")

                    # Terminate chromium gracefully
                    try:
                        self.screensaver_process.terminate()
                        self.screensaver_process.wait(timeout=2)
                    except subprocess.TimeoutExpired:
                        # Force kill if doesn't terminate
                        self.screensaver_process.kill()
                        self.screensaver_process.wait(timeout=1)

                    logger.info("✅ Screensaver stopped")

                self.screensaver_process = None

        except Exception as e:
            logger.error(f"Error stopping screensaver: {e}")
            # Try to kill anyway
            if self.screensaver_process:
                try:
                    self.screensaver_process.kill()
                except:
                    pass
                self.screensaver_process = None

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
            timeout_buffer = 5  # Max 5 seconds over duration before force skip

            while not self.monitor_stop_event.is_set():
                video_name = os.path.basename(self.current_video) if self.current_video else 'unknown'

                # ⏰ PRIORITY 1: ABSOLUTE TIMEOUT CHECK (most reliable, checked FIRST)
                if self.process and self.is_playing and self.playback_duration > 0:
                    elapsed_time = time.time() - self.video_start_time
                    max_allowed_time = self.playback_duration + timeout_buffer

                    if elapsed_time > max_allowed_time:
                        logger.warning(f"⏰ TIMEOUT! Video exceeded max allowed time")
                        logger.warning(f"   Video: {video_name}")
                        logger.warning(f"   Duration: {self.playback_duration:.1f}s")
                        logger.warning(f"   Elapsed: {elapsed_time:.1f}s")
                        logger.warning(f"   Max allowed: {max_allowed_time:.1f}s")
                        logger.warning(f"   Exceeded by: {elapsed_time - max_allowed_time:.1f}s")

                        # Kill process immediately
                        if self.process:
                            try:
                                logger.info("Terminating MPV process...")
                                self.process.terminate()
                                time.sleep(0.5)
                                if self.process.poll() is None:
                                    logger.info("Process still alive, killing...")
                                    self.process.kill()
                            except Exception as e:
                                logger.error(f"Error killing process: {e}")

                        # Reset counters
                        self.position_stuck_count = 0
                        self.last_position_update = 0.0

                        # Skip to next video
                        if self.loop_playlist and self.playlist:
                            logger.info("▶️  Skipping to next video after timeout...")

                            # BLACK TRANSITION
                            logger.info(f"⬛ BLACK TRANSITION: {self.transition_duration}s")
                            self._set_black_screen()
                            time.sleep(self.transition_duration)

                            self.play_next(from_monitor=True)
                            continue
                        else:
                            self.is_playing = False
                            self._set_black_screen()
                            break

                # 🎬 PRIORITY 2: Check if process has finished normally
                if self.process and self.process.poll() is not None:
                    # Process has finished, check exit code
                    exit_code = self.process.returncode

                    # Read stderr to see MPV errors
                    stderr_output = ""
                    if self.process.stderr:
                        try:
                            stderr_output = self.process.stderr.read().decode('utf-8', errors='ignore')
                        except:
                            pass

                    logger.warning(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
                    logger.warning(f"🎬 MPV PROCESS TERMINATED")
                    logger.warning(f"   Video: {video_name}")
                    logger.warning(f"   Exit code: {exit_code}")
                    logger.warning(f"   Current index: {self.current_index + 1}/{len(self.playlist)}")
                    logger.warning(f"   Loop enabled: {self.loop_playlist}")
                    logger.warning(f"   Playlist length: {len(self.playlist)}")

                    if stderr_output:
                        logger.error(f"📝 MPV stderr (last 20 lines):")
                        for line in stderr_output.split('\n')[-20:]:
                            if line.strip():
                                logger.error(f"     {line}")

                    if exit_code == 0:
                        logger.info(f"✅ Video finished normally")
                    else:
                        logger.error(f"❌ Video error (exit code {exit_code})")

                    # Reset counters
                    self.position_stuck_count = 0
                    self.last_position_update = 0.0

                    # Only auto-play next if loop is enabled and there's a playlist
                    if self.loop_playlist and self.playlist:
                        next_index = (self.current_index + 1) % len(self.playlist)
                        logger.info(f"▶️  AUTO-PLAY ENABLED - Attempting to play next video")
                        logger.info(f"   Next index will be: {next_index + 1}/{len(self.playlist)}")

                        # BLACK TRANSITION: Fade to black between videos
                        logger.info(f"⬛ BLACK TRANSITION: {self.transition_duration}s")
                        self._set_black_screen()
                        time.sleep(self.transition_duration)

                        try:
                            result = self.play_next(from_monitor=True)
                            logger.info(f"   ✓ play_next() returned: {result}")
                            if result:
                                logger.info(f"   ✅ Successfully started next video!")
                            else:
                                logger.error(f"   ❌ play_next() returned False - PLAYBACK FAILED!")
                                logger.error(f"   This is why you see the terminal!")
                        except Exception as e:
                            logger.error(f"   ❌ EXCEPTION in play_next(): {e}")
                            import traceback
                            logger.error(f"   Full traceback:")
                            for line in traceback.format_exc().split('\n'):
                                logger.error(f"     {line}")
                    else:
                        logger.warning(f"⏹️  AUTO-PLAY DISABLED - Stopping playback")
                        logger.warning(f"   loop_playlist={self.loop_playlist}")
                        logger.warning(f"   playlist_length={len(self.playlist)}")
                        self.is_playing = False
                        self._set_black_screen()
                        break

                    logger.warning(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

                # 📊 PRIORITY 3: Update position for status display
                elif self.process and self.is_playing:
                    self._update_playback_position()

                # ⏱️ Check every second
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
