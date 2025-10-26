"""
HDMI detection and management for Raspberry Pi
"""
import subprocess
import logging
import os
import glob

logger = logging.getLogger(__name__)


class HDMIManager:
    """Manages HDMI connection detection"""

    @staticmethod
    def is_hdmi_connected() -> bool:
        """
        Check if HDMI display is connected

        Returns:
            True if HDMI is connected, False otherwise
        """
        # Try multiple methods for different Raspberry Pi versions

        # Method 1: Check via DRM (works on RPi 4 and 5 with KMS)
        try:
            drm_paths = glob.glob('/sys/class/drm/card*/status')
            for path in drm_paths:
                if 'HDMI' in path or 'hdmi' in path.lower():
                    with open(path, 'r') as f:
                        status = f.read().strip()
                        if status == 'connected':
                            logger.info(f"HDMI connected via {path}")
                            return True
        except Exception as e:
            logger.debug(f"DRM check failed: {e}")

        # Method 2: tvservice (legacy, works on older RPi)
        try:
            result = subprocess.run(
                ['tvservice', '-s'],
                capture_output=True,
                text=True,
                timeout=2
            )
            if result.returncode == 0:
                output = result.stdout.strip()
                # Check if display is active (not "no device present")
                if 'HDMI' in output and 'no device present' not in output.lower():
                    logger.info(f"HDMI connected via tvservice: {output}")
                    return True
        except FileNotFoundError:
            logger.debug("tvservice not available")
        except Exception as e:
            logger.debug(f"tvservice check failed: {e}")

        # Method 3: Check /proc/device-tree (fallback)
        try:
            display_paths = glob.glob('/proc/device-tree/chosen/display*')
            if display_paths:
                logger.info(f"Display detected via device-tree")
                return True
        except Exception as e:
            logger.debug(f"device-tree check failed: {e}")

        # Method 4: Check if framebuffer exists and has resolution
        try:
            fb_path = '/sys/class/graphics/fb0/virtual_size'
            if os.path.exists(fb_path):
                with open(fb_path, 'r') as f:
                    size = f.read().strip()
                    # If we have a non-zero resolution, display is probably connected
                    if size != '0,0':
                        logger.info(f"Display detected via framebuffer: {size}")
                        return True
        except Exception as e:
            logger.debug(f"framebuffer check failed: {e}")

        logger.warning("No HDMI display detected")
        return False

    @staticmethod
    def get_hdmi_info() -> dict:
        """
        Get detailed HDMI connection information

        Returns:
            Dictionary with HDMI status and details
        """
        info = {
            'connected': False,
            'resolution': None,
            'method': None
        }

        # Check connection
        info['connected'] = HDMIManager.is_hdmi_connected()

        # Try to get resolution
        if info['connected']:
            try:
                # Try tvservice for resolution
                result = subprocess.run(
                    ['tvservice', '-s'],
                    capture_output=True,
                    text=True,
                    timeout=2
                )
                if result.returncode == 0:
                    output = result.stdout.strip()
                    info['resolution'] = output
                    info['method'] = 'tvservice'
            except:
                pass

            # Fallback: try to get from framebuffer
            if not info['resolution']:
                try:
                    with open('/sys/class/graphics/fb0/virtual_size', 'r') as f:
                        size = f.read().strip()
                        info['resolution'] = size.replace(',', 'x')
                        info['method'] = 'framebuffer'
                except:
                    pass

        return info
