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
        this.loadConfig();
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

        // Configuration forms
        document.getElementById('network-config-form').addEventListener('submit', (e) => {
            e.preventDefault();
            this.saveNetworkConfig();
        });

        document.getElementById('player-config-form').addEventListener('submit', (e) => {
            e.preventDefault();
            this.savePlayerConfig();
        });

        document.getElementById('btn-test-network').addEventListener('click', () => this.testNetworkConfig());
        document.getElementById('btn-browse-shares').addEventListener('click', () => this.browseShares());

        // Video selection buttons
        document.getElementById('btn-select-all').addEventListener('click', () => this.selectAllVideos());
        document.getElementById('btn-deselect-all').addEventListener('click', () => this.deselectAllVideos());

        // Config volume slider
        const configVolumeSlider = document.getElementById('config-volume');
        configVolumeSlider.addEventListener('input', (e) => {
            document.getElementById('config-volume-value').textContent = e.target.value;
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

            // Update video preview
            this.updatePreview(player);

        } catch (error) {
            console.error('Error updating status:', error);
            document.getElementById('status-indicator').innerHTML =
                '<span class="badge bg-danger">Errore</span>';
        }
    }

    updatePreview(playerStatus) {
        const previewImg = document.getElementById('video-preview');
        const placeholder = document.getElementById('preview-placeholder');
        const videoName = document.getElementById('preview-video-name');

        if (playerStatus.is_playing && playerStatus.current_video) {
            // Show video name
            videoName.textContent = playerStatus.current_video.split('/').pop();

            // Update preview image with cache-busting timestamp
            const timestamp = new Date().getTime();
            previewImg.src = `/api/preview?t=${timestamp}`;

            // Show image when loaded, hide placeholder
            previewImg.onload = () => {
                previewImg.classList.add('active');
                placeholder.style.display = 'none';
            };

            previewImg.onerror = () => {
                // If image fails to load, show placeholder
                previewImg.classList.remove('active');
                placeholder.style.display = 'flex';
            };
        } else {
            // No playback, show placeholder
            previewImg.classList.remove('active');
            previewImg.src = '';
            placeholder.style.display = 'flex';
            videoName.textContent = '-';
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
            document.getElementById('video-count').textContent = '0 video';
            this.updateSelectedCount();
            return;
        }

        document.getElementById('btn-play').disabled = false;
        document.getElementById('video-count').textContent = `${this.videos.length} video`;

        videoList.innerHTML = this.videos.map((video, index) => `
            <div class="video-item" data-index="${index}" data-path="${video.path}">
                <input type="checkbox" class="video-checkbox" data-path="${video.path}">
                <div class="video-info">
                    <div class="video-name">${video.name}</div>
                    <div class="video-size">${this.formatFileSize(video.size)}</div>
                </div>
            </div>
        `).join('');

        // Add click handlers for checkboxes
        document.querySelectorAll('.video-checkbox').forEach(checkbox => {
            checkbox.addEventListener('change', () => this.updateSelectedCount());
        });

        // Add click handlers for video items (click on video-info selects it for single play)
        document.querySelectorAll('.video-item .video-info').forEach(info => {
            const item = info.closest('.video-item');

            info.addEventListener('click', (e) => {
                document.querySelectorAll('.video-item').forEach(i => i.classList.remove('selected'));
                item.classList.add('selected');
                this.selectedVideo = item.dataset.path;
            });

            // Double-click to play
            info.addEventListener('dblclick', () => {
                this.selectedVideo = item.dataset.path;
                this.playSelected();
            });
        });

        this.updateSelectedCount();
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

    updateSelectedCount() {
        const checkboxes = document.querySelectorAll('.video-checkbox:checked');
        const count = checkboxes.length;
        document.getElementById('selected-count').textContent = count;
    }

    selectAllVideos() {
        document.querySelectorAll('.video-checkbox').forEach(checkbox => {
            checkbox.checked = true;
        });
        this.updateSelectedCount();
    }

    deselectAllVideos() {
        document.querySelectorAll('.video-checkbox').forEach(checkbox => {
            checkbox.checked = false;
        });
        this.updateSelectedCount();
    }

    getSelectedVideos() {
        const selectedPaths = [];
        document.querySelectorAll('.video-checkbox:checked').forEach(checkbox => {
            selectedPaths.push(checkbox.dataset.path);
        });
        return selectedPaths;
    }

    async loadPlaylist() {
        if (this.videos.length === 0) {
            alert('Nessun video disponibile');
            return;
        }

        // Get selected videos, or all videos if none selected
        let videoPaths = this.getSelectedVideos();

        if (videoPaths.length === 0) {
            // No videos selected, use all videos
            videoPaths = this.videos.map(v => v.path);
        }

        if (videoPaths.length === 0) {
            alert('Nessun video da caricare');
            return;
        }

        try {
            const response = await fetch('/api/playlist', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ videos: videoPaths })
            });

            const data = await response.json();
            if (data.success) {
                alert(`Playlist caricata con ${videoPaths.length} video`);
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

    async loadConfig() {
        try {
            const response = await fetch('/api/config');
            const config = await response.json();

            // Populate network config form
            document.getElementById('config-share-path').value = config.network.share_path || '';
            document.getElementById('config-username').value = config.network.username || '';
            document.getElementById('config-mount-point').value = config.network.mount_point || '/mnt/network_videos';
            // Don't set password field

            // Populate player config form
            document.getElementById('config-volume').value = config.player.volume || 100;
            document.getElementById('config-volume-value').textContent = config.player.volume || 100;
            document.getElementById('config-video-extensions').value = config.player.video_extensions || 'mp4,avi,mkv,mov,wmv,flv,webm';
            document.getElementById('config-loop-playlist').checked = config.player.loop_playlist || false;
            document.getElementById('config-auto-start').checked = config.player.auto_start || false;

            console.log('Configuration loaded');

        } catch (error) {
            console.error('Error loading configuration:', error);
        }
    }

    async saveNetworkConfig() {
        const sharePath = document.getElementById('config-share-path').value;
        const username = document.getElementById('config-username').value;
        const password = document.getElementById('config-password').value;
        const mountPoint = document.getElementById('config-mount-point').value;

        if (!sharePath) {
            alert('Inserisci il percorso della share di rete');
            return;
        }

        try {
            const response = await fetch('/api/config/network', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    share_path: sharePath,
                    username: username,
                    password: password,
                    mount_point: mountPoint
                })
            });

            const data = await response.json();

            if (data.success) {
                alert('Configurazione di rete salvata con successo!');
                // Clear password field for security
                document.getElementById('config-password').value = '';
            } else {
                alert('Errore nel salvare la configurazione');
            }

        } catch (error) {
            console.error('Error saving network config:', error);
            alert('Errore nel salvare la configurazione');
        }
    }

    async testNetworkConfig() {
        const sharePath = document.getElementById('config-share-path').value;
        const username = document.getElementById('config-username').value;
        const password = document.getElementById('config-password').value;
        const mountPoint = document.getElementById('config-mount-point').value;

        if (!sharePath) {
            alert('Inserisci il percorso della share di rete');
            return;
        }

        const resultDiv = document.getElementById('network-test-result');
        resultDiv.innerHTML = `
            <div class="alert alert-info">
                <i class="bi bi-hourglass-split spinner-border-sm"></i>
                <strong>Test in corso...</strong><br>
                <small>Tentativo di connessione al NAS. Questo potrebbe richiedere alcuni secondi...</small>
            </div>
        `;
        resultDiv.style.display = 'block';

        try {
            const response = await fetch('/api/config/network/test', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    share_path: sharePath,
                    username: username,
                    password: password,
                    mount_point: mountPoint
                })
            });

            const data = await response.json();

            if (data.success) {
                resultDiv.innerHTML = `
                    <div class="alert alert-success">
                        <i class="bi bi-check-circle-fill"></i>
                        <strong>${data.message}</strong><br>
                        <small>Il NAS è raggiungibile e le credenziali sono corrette. Puoi salvare la configurazione.</small>
                    </div>
                `;
            } else {
                // Build detailed error message
                let errorHtml = `
                    <div class="alert alert-danger">
                        <i class="bi bi-x-circle-fill"></i>
                        <strong>${data.message}</strong><br>
                `;

                // Add technical details if available
                if (data.error) {
                    errorHtml += `<hr><small><strong>Dettagli tecnici:</strong><br>${data.error}</small>`;
                }

                // Add troubleshooting tips
                errorHtml += `
                    <hr>
                    <small><strong>Suggerimenti:</strong>
                    <ul class="mb-0" style="margin-top: 8px;">
                        <li>Verifica che il NAS sia acceso e raggiungibile</li>
                        <li>Controlla che l'indirizzo IP sia corretto</li>
                        <li>Assicurati che username e password siano corretti</li>
                        <li>Verifica che SMB sia abilitato sul NAS</li>
                        <li>Controlla che la cartella esista e sia condivisa</li>
                    </ul>
                    </small>
                    </div>
                `;

                resultDiv.innerHTML = errorHtml;
            }

        } catch (error) {
            console.error('Error testing network:', error);
            resultDiv.innerHTML = `
                <div class="alert alert-danger">
                    <i class="bi bi-exclamation-triangle-fill"></i>
                    <strong>Errore durante il test</strong><br>
                    <small>${error.message}</small>
                </div>
            `;
        }
    }

    async browseShares() {
        const sharePath = document.getElementById('config-share-path').value;
        const username = document.getElementById('config-username').value;
        const password = document.getElementById('config-password').value;

        // Extract host from share path (e.g., "//192.168.1.100/share" -> "192.168.1.100")
        let host = '';
        if (sharePath) {
            host = sharePath.replace('//', '').split('/')[0];
        }

        if (!host) {
            alert('Inserisci almeno l\'indirizzo IP/hostname del NAS nel campo "Percorso Share" (es: //192.168.1.100/cartella)');
            return;
        }

        const resultDiv = document.getElementById('shares-browser-result');
        resultDiv.innerHTML = `
            <div class="alert alert-info">
                <i class="bi bi-hourglass-split spinner-border-sm"></i>
                <strong>Ricerca cartelle condivise...</strong><br>
                <small>Connessione a ${host}...</small>
            </div>
        `;
        resultDiv.style.display = 'block';

        try {
            const response = await fetch('/api/config/network/browse', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    host: host,
                    username: username,
                    password: password
                })
            });

            const data = await response.json();

            if (data.success && data.shares.length > 0) {
                // Build shares list with click handlers
                let sharesHtml = `
                    <div class="card border-success">
                        <div class="card-header bg-success text-white">
                            <i class="bi bi-folder-fill"></i> ${data.message}
                        </div>
                        <div class="card-body">
                            <p class="mb-2"><strong>Host:</strong> ${data.host}</p>
                            <p class="mb-3"><small class="text-muted">Clicca su una cartella per selezionarla</small></p>
                            <div class="list-group">
                `;

                data.shares.forEach(share => {
                    sharesHtml += `
                        <a href="#" class="list-group-item list-group-item-action d-flex justify-content-between align-items-center share-item"
                           data-share-path="${share.full_path}">
                            <div>
                                <i class="bi bi-hdd-fill text-primary"></i>
                                <strong>${share.name}</strong>
                                <small class="text-muted ms-2">${share.type}</small>
                            </div>
                            <i class="bi bi-chevron-right"></i>
                        </a>
                    `;
                });

                sharesHtml += `
                            </div>
                        </div>
                    </div>
                `;

                resultDiv.innerHTML = sharesHtml;

                // Add click handlers to shares
                document.querySelectorAll('.share-item').forEach(item => {
                    item.addEventListener('click', (e) => {
                        e.preventDefault();
                        const sharePath = item.getAttribute('data-share-path');
                        document.getElementById('config-share-path').value = sharePath;

                        // Visual feedback
                        document.querySelectorAll('.share-item').forEach(i => i.classList.remove('active'));
                        item.classList.add('active');

                        // Show success message
                        this.showShareSelected(sharePath);
                    });
                });

            } else {
                resultDiv.innerHTML = `
                    <div class="alert alert-warning">
                        <i class="bi bi-exclamation-triangle-fill"></i>
                        <strong>${data.message}</strong><br>
                        <hr>
                        <small><strong>Possibili cause:</strong>
                        <ul class="mb-0" style="margin-top: 8px;">
                            <li>Il NAS non è raggiungibile dalla rete</li>
                            <li>Il servizio SMB non è abilitato sul NAS</li>
                            <li>Le credenziali potrebbero essere necessarie (compila username e password)</li>
                            <li>Il firewall potrebbe bloccare le connessioni SMB</li>
                        </ul>
                        </small>
                    </div>
                `;
            }

        } catch (error) {
            console.error('Error browsing shares:', error);
            resultDiv.innerHTML = `
                <div class="alert alert-danger">
                    <i class="bi bi-exclamation-triangle-fill"></i>
                    <strong>Errore durante la ricerca</strong><br>
                    <small>${error.message}</small>
                </div>
            `;
        }
    }

    showShareSelected(sharePath) {
        const resultDiv = document.getElementById('shares-browser-result');
        const successMsg = document.createElement('div');
        successMsg.className = 'alert alert-success mt-2';
        successMsg.innerHTML = `
            <i class="bi bi-check-circle-fill"></i>
            <strong>Cartella selezionata:</strong> ${sharePath}<br>
            <small>Ora puoi testare la connessione o salvare la configurazione</small>
        `;

        // Find and replace any existing success message
        const existingMsg = resultDiv.querySelector('.alert-success.mt-2');
        if (existingMsg) {
            existingMsg.remove();
        }

        resultDiv.appendChild(successMsg);

        // Scroll to the success message
        successMsg.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }

    async savePlayerConfig() {
        const volume = parseInt(document.getElementById('config-volume').value);
        const videoExtensions = document.getElementById('config-video-extensions').value;
        const loopPlaylist = document.getElementById('config-loop-playlist').checked;
        const autoStart = document.getElementById('config-auto-start').checked;

        try {
            const response = await fetch('/api/config/player', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    volume: volume,
                    video_extensions: videoExtensions,
                    loop_playlist: loopPlaylist,
                    auto_start: autoStart
                })
            });

            const data = await response.json();

            if (data.success) {
                alert('Configurazione player salvata con successo!');
                // Update the main volume slider as well
                document.getElementById('volume-slider').value = volume;
                document.getElementById('volume-value').textContent = volume;
            } else {
                alert('Errore nel salvare la configurazione');
            }

        } catch (error) {
            console.error('Error saving player config:', error);
            alert('Errore nel salvare la configurazione');
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
