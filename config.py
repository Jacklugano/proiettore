"""
Configuration module for Proiettore video player
"""
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Application configuration"""

    # Flask settings
    FLASK_HOST = os.getenv('FLASK_HOST', '0.0.0.0')
    FLASK_PORT = int(os.getenv('FLASK_PORT', 5000))
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')

    # Network share settings
    NETWORK_SHARE_PATH = os.getenv('NETWORK_SHARE_PATH', '')
    NETWORK_SHARE_USER = os.getenv('NETWORK_SHARE_USER', '')
    NETWORK_SHARE_PASSWORD = os.getenv('NETWORK_SHARE_PASSWORD', '')
    NETWORK_SHARE_MOUNT_POINT = os.getenv('NETWORK_SHARE_MOUNT_POINT', '/mnt/network_videos')

    # Video settings
    VIDEO_EXTENSIONS = os.getenv('VIDEO_EXTENSIONS', 'mp4,avi,mkv,mov,wmv,flv,webm').split(',')

    # Player settings
    VOLUME = int(os.getenv('VOLUME', 100))
    LOOP_PLAYLIST = os.getenv('LOOP_PLAYLIST', 'false').lower() == 'true'
    AUTO_START = os.getenv('AUTO_START', 'false').lower() == 'true'

    # Database
    DATABASE_PATH = os.path.join(os.path.dirname(__file__), 'proiettore.db')

    # Logs
    LOG_FILE = os.path.join(os.path.dirname(__file__), 'proiettore.log')
