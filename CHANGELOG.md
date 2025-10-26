# Changelog

Tutte le modifiche importanti a questo progetto saranno documentate in questo file.

## [1.1.0] - 2025-01-XX

### Aggiunto
- ✨ **Configurazione completa tramite interfaccia web**
  - Form per configurazione cartella di rete (path, username, password)
  - Form per configurazione player (volume, estensioni, auto-start)
  - Test connessione di rete prima del salvataggio
  - Salvataggio configurazione persistente in database
  - **Browser cartelle condivise SMB**: Esplora e seleziona cartelle disponibili sul NAS con un click

- ✨ **Selezione video personalizzata per playlist**
  - Checkbox per ogni video nella lista
  - Pulsanti "Seleziona Tutti" / "Deseleziona Tutti"
  - Contatore video selezionati in tempo reale
  - Carica in playlist solo i video selezionati
  - Se nessun video è selezionato, carica tutti (comportamento precedente)

- ✨ **Anteprima live della riproduzione**
  - Riquadro preview nella pagina Player che mostra screenshot del video in riproduzione
  - Aggiornamento automatico ogni 3 secondi
  - Mostra il nome del video corrente
  - Permette di monitorare la riproduzione da remoto senza vedere l'HDMI
  - Screenshot catturati tramite MPV IPC

- ✨ **Rilevamento HDMI automatico**
  - Controllo presenza display HDMI prima della riproduzione
  - Supporta multiple metodi di detection (DRM, tvservice, framebuffer)
  - Compatibile con Raspberry Pi 4 e 5
  - Avviso visivo nell'interfaccia se HDMI non collegato
  - Previene errori di riproduzione quando display assente
  - API endpoint `/api/hdmi/status` per controllo manuale

- ✨ **Salvataggio e ripristino sessione automatico**
  - Salva automaticamente playlist, video corrente, stato riproduzione
  - Ripristina sessione automaticamente dopo riavvio sistema/servizio
  - Riprende riproduzione dal punto esatto dove era stata interrotta
  - Mantiene stato pausa/play e volume
  - Sessione salvata in `/tmp/proiettore_session.json`
  - Sessioni più vecchie di 24 ore vengono ignorate

- ✨ **Interfaccia web completamente ridisegnata**
  - Design moderno con gradienti colorati
  - Animazioni smooth su tutti i componenti
  - Tabs Bootstrap per organizzazione contenuti
  - Card con effetti hover ed elevazione 3D
  - Scrollbar custom stilizzate
  - Badges pulsanti con animazioni
  - Responsive design migliorato

- ✨ **Supporto migliorato per Synology NAS**
  - Supporto SMB 3.0 con fallback automatico a SMB 2.1
  - Opzioni ottimizzate per NAS Synology
  - Guida integrata nella pagina Impostazioni
  - Logging avanzato per debugging

- 📝 **Guida Synology NAS**
  - Card dedicata con istruzioni dettagliate
  - Prerequisiti e checklist SMB
  - Tips e best practices

- 🔄 **Script di aggiornamento automatico**
  - `update.sh` per aggiornamenti semplificati
  - Backup automatico di database e configurazione
  - Verifica stato e rollback se necessario

### Migliorato
- 🎨 Interfaccia utente con palette colori moderna
- 🚀 Performance di mount cartelle di rete
- 📊 Visualizzazione stato player in tempo reale
- 🎯 UX migliorata per configurazione iniziale

### Corretto
- 🐛 **CRITICO: MPV usa DRM card sbagliata - RISOLTO**
  - Aggiunto --drm-device=/dev/dri/card1 per specificare esplicitamente la scheda DRM corretta
  - L'HDMI su Raspberry Pi 5 è collegato a card1-HDMI-A-1, non card0
  - Senza questo parametro MPV usava card0 (senza HDMI) causando schermo vuoto
  - Video ora viene effettivamente visualizzato sull'output HDMI
- 🐛 **CRITICO: Video non va in fullscreen (si vede desktop) - RISOLTO CON DRM**
  - Cambiato video output da --vo=gpu a --vo=drm
  - DRM bypassa completamente X11/Wayland scrivendo direttamente al framebuffer
  - Aggiunto --drm-connector=HDMI-A-1 per output HDMI esplicito
  - Rimosse opzioni X11 non più necessarie (--ontop, --no-border, ecc.)
  - Video ora copre COMPLETAMENTE lo schermo, desktop NON più visibile
  - Funziona anche con desktop manager attivo (LXDE, GNOME, KDE)
- 🐛 **CRITICO: Permission denied con Synology NAS risolto!**
  - Rimossa opzione `sec=ntlmssp` che causava errore di autenticazione con Synology DSM
  - SMB ora auto-negozia il metodo di sicurezza ottimale (funziona con Synology, QNAP, Windows Server)
  - File credentials creato come root usando sudo tee/chmod per massima compatibilità
  - Risolve definitivamente "mount error(13): Permission denied"
- 🐛 **MPV player non trovato dal servizio systemd**
  - Usato path completo `/usr/bin/mpv` invece di `mpv` per compatibilità systemd
  - Risolve errore "[Errno 2] No such file or directory: 'mpv'"
- 🐛 Autenticazione SMB con vari tipi di NAS
- 🐛 Compatibilità con Synology DSM 6.x e 7.x

## [1.0.0] - 2025-01-XX

### Aggiunto
- 🎬 Sistema completo di riproduzione video con MPV
- 🌐 Supporto cartelle di rete SMB/CIFS
- 🖥️ Output HDMI per video + audio Raspberry Pi
- 📅 Schedulazione automatica video
- 🎛️ Interfaccia web completa
- 🔄 Gestione playlist
- ⚡ Auto-start all'avvio
- 💾 Database SQLite per configurazione e schedulazione
- 🐍 Backend Python/Flask
- 🎨 Frontend Bootstrap responsive
- 📦 Script di installazione automatica
- 🔧 Servizio systemd per auto-start
- 📖 Documentazione completa

### Caratteristiche Principali
- Player MPV con controlli completi (play, pause, stop, volume)
- Mount automatico cartelle di rete
- Schedulazione con cron patterns
- API REST complete
- Interfaccia web in italiano
- Supporto formati: MP4, AVI, MKV, MOV, WMV, FLV, WebM

---

## Formato

Questo changelog segue il formato [Keep a Changelog](https://keepachangelog.com/it/1.0.0/),
e questo progetto aderisce al [Semantic Versioning](https://semver.org/lang/it/).

### Tipi di modifiche
- **Aggiunto** - per nuove funzionalità
- **Modificato** - per modifiche a funzionalità esistenti
- **Deprecato** - per funzionalità che saranno rimosse
- **Rimosso** - per funzionalità rimosse
- **Corretto** - per bug fix
- **Sicurezza** - per vulnerabilità corrette
