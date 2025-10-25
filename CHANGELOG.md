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
- 🐛 **CRITICO: Permission denied con mount.cifs** - File credentials ora creato come root usando sudo tee/chmod. Mount.cifs richiede che il file credentials sia di proprietà di root quando mount viene eseguito con sudo. Risolve definitivamente l'errore "mount error(13): Permission denied"
- 🐛 Problemi di connessione con NAS Synology
- 🐛 Compatibilità SMB con diverse versioni

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
