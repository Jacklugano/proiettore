"""
Main Flask application for Proiettore video player
"""
import os
import logging
from flask import Flask, render_template, jsonify, request, send_from_directory, send_file
from config import Config
from video_player import VideoPlayer
from network_manager import NetworkManager
from scheduler import PlaybackScheduler
from config_manager import ConfigManager

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(Config.LOG_FILE),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)

# Initialize components
config_manager = ConfigManager()
player = VideoPlayer(volume=Config.VOLUME)
network = NetworkManager()
scheduler = PlaybackScheduler()


def scheduled_play(video_path: str):
    """Callback for scheduled playback"""
    logger.info(f"Scheduled playback: {video_path}")
    player.play(video_path)


# Restore session on startup
def restore_session_on_startup():
    """Restore saved playback session if exists, or autoplay if configured"""
    try:
        logger.info("Checking for saved session...")
        session_restored = player.restore_session()

        if session_restored:
            logger.info("Session restored successfully")
        else:
            logger.info("No session to restore or restore failed")

            # Check if autoplay on startup is enabled
            player_config = config_manager.get_player_config()
            if player_config.get('auto_start', False):
                logger.info("Auto-start enabled, loading all videos and starting playback...")

                # Get all available videos
                videos = network.get_video_files()

                if videos:
                    # Load playlist with all videos
                    if player.load_playlist(videos):
                        logger.info(f"Loaded {len(videos)} videos for autoplay")

                        # Start playback with first video
                        if player.play(videos[0]):
                            logger.info("Autoplay started successfully")
                        else:
                            logger.warning("Failed to start autoplay")
                    else:
                        logger.warning("Failed to load playlist for autoplay")
                else:
                    logger.warning("No videos found for autoplay")
            else:
                logger.info("Auto-start disabled, no action taken")

    except Exception as e:
        logger.error(f"Error during session restore/autoplay: {e}")


# Call session restore after a short delay (let Flask finish initialization)
import threading
threading.Timer(2.0, restore_session_on_startup).start()


# Routes
@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')


@app.route('/api/status')
def api_status():
    """Get current status"""
    return jsonify({
        'player': player.get_status(),
        'network': network.get_status(),
        'scheduler_running': scheduler.scheduler.running,
        'hdmi': player.check_hdmi_status(),
        'cache': player.get_cache_status()
    })


@app.route('/api/hdmi/status')
def api_hdmi_status():
    """Get HDMI connection status"""
    return jsonify(player.check_hdmi_status())


@app.route('/api/preview')
def api_preview():
    """Get current playback screenshot preview"""
    preview_path = '/tmp/proiettore_preview.jpg'

    # Check if screenshot exists
    if os.path.exists(preview_path):
        return send_file(preview_path, mimetype='image/jpeg')
    else:
        # Return placeholder image or 404
        return jsonify({'error': 'No preview available'}), 404


@app.route('/api/videos')
def api_videos():
    """Get list of available videos"""
    videos = network.get_video_files()

    # Convert to relative paths for display
    video_list = []
    for video in videos:
        video_list.append({
            'path': video,
            'name': os.path.basename(video),
            'size': os.path.getsize(video) if os.path.exists(video) else 0
        })

    return jsonify(video_list)


@app.route('/api/play', methods=['POST'])
def api_play():
    """Play a video"""
    data = request.get_json()
    video_path = data.get('path')

    if not video_path:
        return jsonify({'success': False, 'error': 'No video path provided'}), 400

    success = player.play(video_path)
    return jsonify({'success': success})


@app.route('/api/stop', methods=['POST'])
def api_stop():
    """Stop playback"""
    success = player.stop()
    return jsonify({'success': success})


@app.route('/api/pause', methods=['POST'])
def api_pause():
    """Pause/resume playback"""
    success = player.pause()
    return jsonify({'success': success})


@app.route('/api/volume', methods=['POST'])
def api_volume():
    """Set volume"""
    data = request.get_json()
    volume = data.get('volume', 100)

    success = player.set_volume(int(volume))
    return jsonify({'success': success, 'volume': player.volume})


@app.route('/api/playlist', methods=['POST'])
def api_playlist():
    """Load playlist"""
    data = request.get_json()
    videos = data.get('videos', [])

    logger.info(f"API received request to load playlist with {len(videos)} videos")
    logger.debug(f"Video paths: {videos}")

    # Check maximum limit
    if len(videos) > 20:
        logger.warning(f"Playlist rejected: too many videos ({len(videos)} > 20)")
        return jsonify({
            'success': False,
            'error': f'Troppi video! Massimo 20 per playlist. Ricevuti: {len(videos)}'
        }), 400

    success = player.load_playlist(videos)

    if success:
        return jsonify({'success': True})
    else:
        return jsonify({
            'success': False,
            'error': 'Errore durante caricamento playlist'
        }), 500


@app.route('/api/next', methods=['POST'])
def api_next():
    """Play next video"""
    success = player.play_next()
    return jsonify({'success': success})


@app.route('/api/previous', methods=['POST'])
def api_previous():
    """Play previous video"""
    success = player.play_previous()
    return jsonify({'success': success})


@app.route('/api/network/mount', methods=['POST'])
def api_mount():
    """Mount network share"""
    success = network.mount_share()
    return jsonify({'success': success, 'status': network.get_status()})


@app.route('/api/network/unmount', methods=['POST'])
def api_unmount():
    """Unmount network share"""
    success = network.unmount_share()
    return jsonify({'success': success, 'status': network.get_status()})


@app.route('/api/schedules', methods=['GET'])
def api_get_schedules():
    """Get all schedules"""
    schedules = scheduler.get_schedules()
    return jsonify(schedules)


@app.route('/api/schedules', methods=['POST'])
def api_add_schedule():
    """Add a new schedule"""
    data = request.get_json()

    schedule_id = scheduler.add_schedule(
        name=data.get('name'),
        video_path=data.get('video_path'),
        hour=int(data.get('hour')),
        minute=int(data.get('minute')),
        callback=scheduled_play,
        days_of_week=data.get('days_of_week')
    )

    return jsonify({'success': bool(schedule_id), 'id': schedule_id})


@app.route('/api/schedules/<int:schedule_id>', methods=['DELETE'])
def api_delete_schedule(schedule_id):
    """Delete a schedule"""
    success = scheduler.remove_schedule(schedule_id)
    return jsonify({'success': success})


@app.route('/api/schedules/<int:schedule_id>/toggle', methods=['POST'])
def api_toggle_schedule(schedule_id):
    """Enable/disable a schedule"""
    success = scheduler.toggle_schedule(schedule_id)
    return jsonify({'success': success})


# Configuration endpoints
@app.route('/api/config', methods=['GET'])
def api_get_config():
    """Get all configuration settings"""
    network_config = config_manager.get_network_config()
    player_config = config_manager.get_player_config()

    # Don't send password in response, only indicate if it's set
    response_config = {
        'network': {
            'share_path': network_config['share_path'],
            'username': network_config['username'],
            'has_password': bool(network_config['password']),
            'mount_point': network_config['mount_point']
        },
        'player': player_config
    }

    return jsonify(response_config)


@app.route('/api/config/network', methods=['POST'])
def api_set_network_config():
    """Set network configuration"""
    data = request.get_json()

    share_path = data.get('share_path', '')
    username = data.get('username', '')
    password = data.get('password', '')
    mount_point = data.get('mount_point', '/mnt/network_videos')

    # Save to database
    success = config_manager.set_network_config(
        share_path=share_path,
        username=username,
        password=password,
        mount_point=mount_point
    )

    if success:
        # Update network manager with new config
        network.update_config(
            share_path=share_path,
            username=username,
            password=password,
            mount_point=mount_point
        )

    return jsonify({'success': success})


@app.route('/api/config/network/test', methods=['POST'])
def api_test_network():
    """Test network configuration without saving"""
    data = request.get_json()

    share_path = data.get('share_path', '')
    username = data.get('username', '')
    password = data.get('password', '')
    mount_point = data.get('mount_point', '/mnt/network_videos')

    # Validate inputs
    if not share_path:
        return jsonify({
            'success': False,
            'message': 'Errore: Percorso share mancante',
            'error': 'Share path is required'
        })

    # Create temporary network manager for testing
    test_network = NetworkManager()
    test_network.update_config(
        share_path=share_path,
        username=username,
        password=password,
        mount_point=mount_point
    )

    # Try to mount
    success = test_network.mount_share()

    # Get error details if failed
    error_detail = test_network.get_last_error() if not success else None

    # Clean up - unmount if successful
    if success:
        test_network.unmount_share()

    # Build response message
    if success:
        message = 'Connessione riuscita! ✓'
    else:
        message = 'Connessione fallita. Controlla i parametri.'
        if error_detail:
            # Try to provide helpful error message in Italian
            if 'Permission denied' in error_detail or 'access denied' in error_detail.lower():
                message = 'Errore: Credenziali non valide o permessi insufficienti'
            elif 'No route to host' in error_detail or 'Network is unreachable' in error_detail:
                message = 'Errore: NAS non raggiungibile. Controlla indirizzo IP e connessione di rete'
            elif 'Host is down' in error_detail:
                message = 'Errore: NAS spento o non raggiungibile'
            elif 'timeout' in error_detail.lower():
                message = 'Errore: Timeout connessione. Controlla firewall e connessione di rete'
            elif 'Invalid argument' in error_detail:
                message = 'Errore: Formato percorso share non valido. Usa: //IP/cartella'

    return jsonify({
        'success': success,
        'message': message,
        'error': error_detail,
        'details': {
            'share_path': share_path,
            'has_username': bool(username),
            'mount_point': mount_point
        }
    })


@app.route('/api/config/network/browse', methods=['POST'])
def api_browse_shares():
    """Browse available SMB shares on a host"""
    data = request.get_json()

    host = data.get('host', '')
    username = data.get('username', '')
    password = data.get('password', '')

    if not host:
        return jsonify({
            'success': False,
            'message': 'Indirizzo host mancante',
            'shares': []
        })

    # Clean up host (remove // and /share if present)
    host_clean = host.replace('//', '').split('/')[0]

    # Create temporary network manager
    temp_network = NetworkManager()

    # List shares
    shares = temp_network.list_shares(host_clean, username, password)

    return jsonify({
        'success': len(shares) > 0,
        'message': f'Trovate {len(shares)} cartelle condivise' if shares else 'Nessuna cartella trovata o errore di connessione',
        'shares': shares,
        'host': host_clean
    })


@app.route('/api/config/player', methods=['POST'])
def api_set_player_config():
    """Set player configuration"""
    data = request.get_json()

    volume = data.get('volume')
    loop_playlist = data.get('loop_playlist')
    auto_start = data.get('auto_start')
    video_extensions = data.get('video_extensions')

    # Save to database
    success = config_manager.set_player_config(
        volume=int(volume) if volume is not None else None,
        loop_playlist=loop_playlist,
        auto_start=auto_start,
        video_extensions=video_extensions
    )

    if success and volume is not None:
        # Update player volume immediately
        player.set_volume(int(volume))

    return jsonify({'success': success})


def initialize_app():
    """Initialize application components"""
    logger.info("Initializing Proiettore...")

    # Load configuration from database (overrides .env if present)
    network_config = config_manager.get_network_config()
    if network_config['share_path']:
        logger.info("Loading network configuration from database...")
        network.update_config(
            share_path=network_config['share_path'],
            username=network_config['username'],
            password=network_config['password'],
            mount_point=network_config['mount_point']
        )
    elif Config.NETWORK_SHARE_PATH:
        # Fallback to .env config
        logger.info("Loading network configuration from .env...")

    # Mount network share if configured
    if network.share_path:
        logger.info("Mounting network share...")
        network.mount_share()

    # Load player configuration from database
    player_config = config_manager.get_player_config()
    if player_config['volume']:
        player.set_volume(player_config['volume'])

    # Start scheduler
    logger.info("Starting scheduler...")
    scheduler.start()
    scheduler.load_schedules(scheduled_play)

    # Auto-start if configured
    auto_start = player_config.get('auto_start', Config.AUTO_START)
    if auto_start:
        videos = network.get_video_files()
        if videos:
            logger.info("Auto-start enabled, loading playlist...")
            player.load_playlist(videos)
            loop_playlist = player_config.get('loop_playlist', Config.LOOP_PLAYLIST)
            if loop_playlist:
                player.play(videos[0])

    logger.info("Proiettore initialized successfully!")


def shutdown_app():
    """Cleanup on shutdown"""
    logger.info("Shutting down Proiettore...")
    player.stop()
    scheduler.stop()
    # Note: Network unmount should be done manually or on system shutdown


if __name__ == '__main__':
    try:
        initialize_app()
        app.run(
            host=Config.FLASK_HOST,
            port=Config.FLASK_PORT,
            debug=False
        )
    except KeyboardInterrupt:
        shutdown_app()
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        shutdown_app()
