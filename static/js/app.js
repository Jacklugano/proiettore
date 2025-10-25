// Proiettore Web Interface

class ProiettoreApp {
    constructor() {
        this.videos = [];
        this.selectedVideo = null;
        this.statusInterval = null;

        this.init();
    }

    init() {
        console.log('Initializing Proiettore...');

        // Bind event listeners
        this.bindEvents();

        // Start status updates
        this.startStatusUpdates();

        // Load initial data
        this.loadVideos();
        this.loadSchedules();
    }

    bindEvents() {
        // Player controls
        document.getElementById('btn-play').addEventListener('click', () => this.playSelected());
        document.getElementById('btn-pause').addEventListener('click', () => this.pause());
        document.getElementById('btn-stop').addEventListener('click', () => this.stop());
        document.getElementById('btn-next').addEventListener('click', () => this.playNext());
        document.getElementById('btn-previous').addEventListener('click', () => this.playPrevious());

        // Volume control
        const volumeSlider = document.getElementById('volume-slider');
        volumeSlider.addEventListener('input', (e) => {
            document.getElementById('volume-value').textContent = e.target.value;
        });
        volumeSlider.addEventListener('change', (e) => this.setVolume(e.target.value));

        // Network controls
        document.getElementById('btn-mount').addEventListener('click', () => this.mountShare());
        document.getElementById('btn-unmount').addEventListener('click', () => this.unmountShare());
        document.getElementById('btn-refresh-videos').addEventListener('click', () => this.loadVideos());
        document.getElementById('btn-load-playlist').addEventListener('click', () => this.loadPlaylist());

        // Schedule form
        document.getElementById('schedule-form').addEventListener('submit', (e) => {
            e.preventDefault();
            this.addSchedule();
        });
    }

    startStatusUpdates() {
        this.updateStatus();
        this.statusInterval = setInterval(() => this.updateStatus(), 2000);
    }

    async updateStatus() {
        try {
            const response = await fetch('/api/status');
            const data = await response.json();

            // Update status indicator
            const statusIndicator = document.getElementById('status-indicator');
            statusIndicator.innerHTML = '<span class="badge bg-success">Connesso</span>';

            // Update player status
            const player = data.player;
            document.getElementById('current-video').textContent =
                player.current_video ? player.current_video.split('/').pop() : 'Nessuno';

            const playingBadge = document.getElementById('is-playing');
            if (player.is_playing) {
                playingBadge.className = 'badge bg-success';
                playingBadge.textContent = player.is_paused ? 'In pausa' : 'In riproduzione';
            } else {
                playingBadge.className = 'badge bg-secondary';
                playingBadge.textContent = 'Fermo';
            }

            document.getElementById('playlist-info').textContent =
                `${player.playlist_length} video${player.playlist_length !== 1 ? '' : ''} (${player.current_index + 1}/${player.playlist_length})`;

            // Update network status
            const network = data.network;
            const networkStatus = document.getElementById('network-status');
            if (network.is_mounted) {
                networkStatus.className = 'badge bg-success';
                networkStatus.textContent = 'Montata';
            } else {
                networkStatus.className = 'badge bg-secondary';
                networkStatus.textContent = 'Non montata';
            }

            document.getElementById('network-path').textContent =
                network.share_path || 'Nessuna cartella configurata';

        } catch (error) {
            console.error('Error updating status:', error);
            document.getElementById('status-indicator').innerHTML =
                '<span class="badge bg-danger">Errore</span>';
        }
    }

    async loadVideos() {
        try {
            const response = await fetch('/api/videos');
            this.videos = await response.json();

            this.renderVideoList();
            this.updateScheduleVideoSelect();

        } catch (error) {
            console.error('Error loading videos:', error);
            this.showError('Errore nel caricamento dei video');
        }
    }

    renderVideoList() {
        const videoList = document.getElementById('video-list');

        if (this.videos.length === 0) {
            videoList.innerHTML = `
                <div class="text-center p-4 text-muted">
                    <i class="bi bi-film" style="font-size: 2rem;"></i>
                    <p class="mt-2">Nessun video disponibile</p>
                    <small>Monta la cartella di rete e clicca su "Aggiorna Video"</small>
                </div>
            `;
            document.getElementById('btn-play').disabled = true;
            return;
        }

        document.getElementById('btn-play').disabled = false;

        videoList.innerHTML = this.videos.map((video, index) => `
            <div class="video-item" data-index="${index}" data-path="${video.path}">
                <div class="video-name">${video.name}</div>
                <div class="video-size">${this.formatFileSize(video.size)}</div>
            </div>
        `).join('');

        // Add click handlers
        document.querySelectorAll('.video-item').forEach(item => {
            item.addEventListener('click', (e) => {
                document.querySelectorAll('.video-item').forEach(i => i.classList.remove('selected'));
                item.classList.add('selected');
                this.selectedVideo = item.dataset.path;
            });

            // Double-click to play
            item.addEventListener('dblclick', () => {
                this.selectedVideo = item.dataset.path;
                this.playSelected();
            });
        });
    }

    async playSelected() {
        if (!this.selectedVideo) {
            alert('Seleziona un video prima di riprodurre');
            return;
        }

        try {
            const response = await fetch('/api/play', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ path: this.selectedVideo })
            });

            const data = await response.json();
            if (!data.success) {
                this.showError('Errore nella riproduzione');
            }

        } catch (error) {
            console.error('Error playing video:', error);
            this.showError('Errore nella riproduzione');
        }
    }

    async pause() {
        try {
            await fetch('/api/pause', { method: 'POST' });
        } catch (error) {
            console.error('Error pausing:', error);
        }
    }

    async stop() {
        try {
            await fetch('/api/stop', { method: 'POST' });
        } catch (error) {
            console.error('Error stopping:', error);
        }
    }

    async playNext() {
        try {
            await fetch('/api/next', { method: 'POST' });
        } catch (error) {
            console.error('Error playing next:', error);
        }
    }

    async playPrevious() {
        try {
            await fetch('/api/previous', { method: 'POST' });
        } catch (error) {
            console.error('Error playing previous:', error);
        }
    }

    async setVolume(volume) {
        try {
            await fetch('/api/volume', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ volume: parseInt(volume) })
            });
        } catch (error) {
            console.error('Error setting volume:', error);
        }
    }

    async loadPlaylist() {
        if (this.videos.length === 0) {
            alert('Nessun video disponibile');
            return;
        }

        try {
            const videoPaths = this.videos.map(v => v.path);
            const response = await fetch('/api/playlist', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ videos: videoPaths })
            });

            const data = await response.json();
            if (data.success) {
                alert(`Playlist caricata con ${this.videos.length} video`);
            }

        } catch (error) {
            console.error('Error loading playlist:', error);
        }
    }

    async mountShare() {
        try {
            const response = await fetch('/api/network/mount', { method: 'POST' });
            const data = await response.json();

            if (data.success) {
                this.showSuccess('Cartella montata con successo');
                setTimeout(() => this.loadVideos(), 1000);
            } else {
                this.showError('Errore nel montaggio della cartella');
            }

        } catch (error) {
            console.error('Error mounting share:', error);
            this.showError('Errore nel montaggio della cartella');
        }
    }

    async unmountShare() {
        try {
            const response = await fetch('/api/network/unmount', { method: 'POST' });
            const data = await response.json();

            if (data.success) {
                this.showSuccess('Cartella smontata');
            }

        } catch (error) {
            console.error('Error unmounting share:', error);
        }
    }

    async loadSchedules() {
        try {
            const response = await fetch('/api/schedules');
            const schedules = await response.json();

            this.renderSchedules(schedules);

        } catch (error) {
            console.error('Error loading schedules:', error);
        }
    }

    renderSchedules(schedules) {
        const schedulesList = document.getElementById('schedules-list');

        if (schedules.length === 0) {
            schedulesList.innerHTML = '<p class="text-muted small">Nessuna programmazione</p>';
            return;
        }

        schedulesList.innerHTML = schedules.map(schedule => `
            <div class="schedule-item ${schedule.enabled ? '' : 'disabled'}">
                <h6>${schedule.name}</h6>
                <p><strong>Ora:</strong> ${String(schedule.hour).padStart(2, '0')}:${String(schedule.minute).padStart(2, '0')}</p>
                <p><strong>Video:</strong> ${schedule.video_path.split('/').pop()}</p>
                ${schedule.days_of_week ? `<p><strong>Giorni:</strong> ${schedule.days_of_week}</p>` : ''}
                <div class="schedule-controls">
                    <button class="btn btn-sm btn-outline-${schedule.enabled ? 'warning' : 'success'}"
                            onclick="app.toggleSchedule(${schedule.id})">
                        ${schedule.enabled ? 'Disabilita' : 'Abilita'}
                    </button>
                    <button class="btn btn-sm btn-outline-danger"
                            onclick="app.deleteSchedule(${schedule.id})">
                        Elimina
                    </button>
                </div>
            </div>
        `).join('');
    }

    updateScheduleVideoSelect() {
        const select = document.getElementById('schedule-video');
        select.innerHTML = '<option value="">Seleziona video...</option>' +
            this.videos.map(v => `<option value="${v.path}">${v.name}</option>`).join('');
    }

    async addSchedule() {
        const name = document.getElementById('schedule-name').value;
        const videoPath = document.getElementById('schedule-video').value;
        const hour = parseInt(document.getElementById('schedule-hour').value);
        const minute = parseInt(document.getElementById('schedule-minute').value);
        const days = document.getElementById('schedule-days').value;

        try {
            const response = await fetch('/api/schedules', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    name,
                    video_path: videoPath,
                    hour,
                    minute,
                    days_of_week: days || null
                })
            });

            const data = await response.json();

            if (data.success) {
                this.showSuccess('Programmazione aggiunta');
                document.getElementById('schedule-form').reset();
                this.loadSchedules();
            } else {
                this.showError('Errore nell\'aggiunta della programmazione');
            }

        } catch (error) {
            console.error('Error adding schedule:', error);
            this.showError('Errore nell\'aggiunta della programmazione');
        }
    }

    async deleteSchedule(id) {
        if (!confirm('Confermi l\'eliminazione di questa programmazione?')) {
            return;
        }

        try {
            const response = await fetch(`/api/schedules/${id}`, { method: 'DELETE' });
            const data = await response.json();

            if (data.success) {
                this.showSuccess('Programmazione eliminata');
                this.loadSchedules();
            }

        } catch (error) {
            console.error('Error deleting schedule:', error);
        }
    }

    async toggleSchedule(id) {
        try {
            const response = await fetch(`/api/schedules/${id}/toggle`, { method: 'POST' });
            const data = await response.json();

            if (data.success) {
                this.loadSchedules();
            }

        } catch (error) {
            console.error('Error toggling schedule:', error);
        }
    }

    formatFileSize(bytes) {
        if (bytes === 0) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
    }

    showSuccess(message) {
        // Simple alert for now - could be replaced with toast notifications
        console.log('Success:', message);
    }

    showError(message) {
        console.error('Error:', message);
        alert(message);
    }
}

// Initialize app when DOM is ready
let app;
document.addEventListener('DOMContentLoaded', () => {
    app = new ProiettoreApp();
});
