"""
Network share manager for mounting and accessing network folders
"""
import os
import subprocess
import logging
from typing import List, Optional
from config import Config

logger = logging.getLogger(__name__)


class NetworkManager:
    """Manages network share mounting and file access"""

    def __init__(self):
        self.mount_point = Config.NETWORK_SHARE_MOUNT_POINT
        self.share_path = Config.NETWORK_SHARE_PATH
        self.username = Config.NETWORK_SHARE_USER
        self.password = Config.NETWORK_SHARE_PASSWORD
        self.is_mounted = False
        self.last_error = None  # Store last error for debugging

    def update_config(self, share_path: str = None, username: str = None, password: str = None, mount_point: str = None):
        """Update network configuration dynamically"""
        if share_path is not None:
            self.share_path = share_path
        if username is not None:
            self.username = username
        if password is not None:
            self.password = password
        if mount_point is not None:
            self.mount_point = mount_point

        logger.info("Network configuration updated dynamically")

    def _try_mount(self, smb_version: str, extra_options: list = None) -> tuple:
        """
        Try to mount with specific SMB version

        Returns:
            (success: bool, error_message: str)
        """
        try:
            # Build mount options
            options = []
            if self.username:
                options.append(f'username={self.username}')
            else:
                options.append('guest')

            if self.password:
                options.append(f'password={self.password}')

            # Base options
            options.extend([
                'iocharset=utf8',
                'file_mode=0777',
                'dir_mode=0777',
                f'vers={smb_version}',
                'sec=ntlmssp',
                'noperm',
                'rw'
            ])

            # Add extra options if provided
            if extra_options:
                options.extend(extra_options)

            # Build mount command
            mount_cmd = [
                'sudo', 'mount', '-t', 'cifs',
                self.share_path,
                self.mount_point,
                '-o',
                ','.join(options)
            ]

            logger.info(f"Trying mount with SMB {smb_version}: {self.share_path}")

            result = subprocess.run(
                mount_cmd,
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                logger.info(f"Successfully mounted with SMB {smb_version}")
                return True, None
            else:
                error_msg = result.stderr.strip() if result.stderr else "Unknown error"
                logger.warning(f"SMB {smb_version} failed: {error_msg}")
                return False, error_msg

        except subprocess.TimeoutExpired:
            return False, "Connection timeout - Check network connectivity"
        except Exception as e:
            return False, str(e)

    def mount_share(self) -> bool:
        """
        Mount network share using CIFS/SMB with multiple fallback attempts

        Returns:
            True if mount successful, False otherwise
        """
        try:
            # Create mount point if it doesn't exist
            if not os.path.exists(self.mount_point):
                os.makedirs(self.mount_point, exist_ok=True)
                logger.info(f"Created mount point: {self.mount_point}")

            # Check if already mounted
            if self._is_mounted():
                logger.info("Network share already mounted")
                self.is_mounted = True
                self.last_error = None
                return True

            if not self.share_path:
                self.last_error = "No network share path configured"
                logger.warning(self.last_error)
                return False

            # Try multiple SMB versions and configurations
            mount_attempts = [
                ('3.0', ['cache=loose']),  # SMB 3.0 with cache
                ('3.0', []),  # SMB 3.0 without cache
                ('2.1', []),  # SMB 2.1
                ('2.0', []),  # SMB 2.0
                ('1.0', []),  # SMB 1.0 (legacy)
            ]

            errors = []
            for smb_version, extra_opts in mount_attempts:
                success, error = self._try_mount(smb_version, extra_opts)
                if success:
                    self.is_mounted = True
                    self.last_error = None
                    return True
                errors.append(f"SMB {smb_version}: {error}")

            # All attempts failed
            self.last_error = " | ".join(errors)
            logger.error(f"All mount attempts failed: {self.last_error}")
            return False

        except Exception as e:
            self.last_error = f"Unexpected error: {str(e)}"
            logger.error(f"Error mounting share: {e}")
            return False

    def get_last_error(self) -> Optional[str]:
        """Get the last error message"""
        return self.last_error

    def unmount_share(self) -> bool:
        """
        Unmount network share

        Returns:
            True if unmount successful, False otherwise
        """
        try:
            if not self._is_mounted():
                logger.info("Network share not mounted")
                self.is_mounted = False
                return True

            result = subprocess.run(
                ['sudo', 'umount', self.mount_point],
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                self.is_mounted = False
                logger.info(f"Successfully unmounted {self.mount_point}")
                return True
            else:
                logger.error(f"Failed to unmount share: {result.stderr}")
                return False

        except Exception as e:
            logger.error(f"Error unmounting share: {e}")
            return False

    def _is_mounted(self) -> bool:
        """Check if share is currently mounted"""
        try:
            result = subprocess.run(
                ['mount'],
                capture_output=True,
                text=True
            )
            return self.mount_point in result.stdout

        except Exception:
            return False

    def get_video_files(self, extensions: Optional[List[str]] = None) -> List[str]:
        """
        Get list of video files from network share

        Args:
            extensions: List of video file extensions to filter

        Returns:
            List of full paths to video files
        """
        if extensions is None:
            extensions = Config.VIDEO_EXTENSIONS

        video_files = []

        try:
            if not os.path.exists(self.mount_point):
                logger.warning(f"Mount point does not exist: {self.mount_point}")
                return []

            # Walk through directory tree
            for root, dirs, files in os.walk(self.mount_point):
                for file in files:
                    # Check file extension
                    ext = file.split('.')[-1].lower()
                    if ext in extensions:
                        full_path = os.path.join(root, file)
                        video_files.append(full_path)

            video_files.sort()
            logger.info(f"Found {len(video_files)} video files")

        except Exception as e:
            logger.error(f"Error getting video files: {e}")

        return video_files

    def get_status(self) -> dict:
        """Get network manager status"""
        return {
            'is_mounted': self._is_mounted(),
            'mount_point': self.mount_point,
            'share_path': self.share_path,
            'configured': bool(self.share_path)
        }
