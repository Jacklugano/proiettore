"""
Main Flask application for Proiettore video player
"""
import os
import logging
from flask import Flask, render_template, jsonify, request, send_from_directory
from config import Config
from video_player import VideoPlayer
from network_manager import NetworkManager
from scheduler import PlaybackScheduler

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
player = VideoPlayer(volume=Config.VOLUME)
network = NetworkManager()
scheduler = PlaybackScheduler()


def scheduled_play(video_path: str):
    """Callback for scheduled playback"""
    logger.info(f"Scheduled playback: {video_path}")
    player.play(video_path)


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
        'scheduler_running': scheduler.scheduler.running
    })


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

    success = player.load_playlist(videos)
    return jsonify({'success': success})


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


def initialize_app():
    """Initialize application components"""
    logger.info("Initializing Proiettore...")

    # Mount network share if configured
    if Config.NETWORK_SHARE_PATH:
        logger.info("Mounting network share...")
        network.mount_share()

    # Start scheduler
    logger.info("Starting scheduler...")
    scheduler.start()
    scheduler.load_schedules(scheduled_play)

    # Auto-start if configured
    if Config.AUTO_START:
        videos = network.get_video_files()
        if videos:
            logger.info("Auto-start enabled, loading playlist...")
            player.load_playlist(videos)
            if Config.LOOP_PLAYLIST:
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
