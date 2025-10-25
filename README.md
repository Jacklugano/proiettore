# Proiettore 🎬

Sistema di riproduzione video automatizzato per Raspberry Pi 5 con supporto per cartelle di rete e programmazione.

## Caratteristiche

- 📹 **Riproduzione video**: Supporta tutti i formati comuni (MP4, AVI, MKV, MOV, WMV, FLV, WebM)
- 🌐 **Cartelle di rete**: Accesso a video su share di rete SMB/CIFS
- 🖥️ **Output HDMI**: Video su HDMI con audio tramite uscita Raspberry Pi
- 📅 **Schedulazione**: Programmazione automatica di riproduzione video
- 🎛️ **Interfaccia web**: Controllo completo tramite browser
- 🔄 **Playlist**: Gestione playlist e riproduzione continua
- ⚡ **Auto-start**: Avvio automatico all'accensione del Raspberry Pi

## Requisiti

- Raspberry Pi 5 (compatibile anche con Pi 4)
- Raspberry Pi OS (Bullseye o superiore)
- Connessione di rete
- Share di rete SMB/CIFS (opzionale)

## Installazione

### 1. Clona il repository

```bash
git clone https://github.com/Jacklugano/proiettore.git
cd proiettore
```

### 2. Esegui lo script di installazione

```bash
chmod +x install.sh
./install.sh
```

Lo script installerà automaticamente:
- Python 3 e dipendenze
- MPV player
- Supporto CIFS
- Ambiente virtuale Python
- Servizio systemd

### 3. Configura la cartella di rete

Puoi configurare manualmente il file `.env` oppure usare lo script interattivo:

```bash
./setup_network.sh
```

Oppure modifica manualmente:

```bash
nano .env
```

Configura i seguenti parametri:

```bash
# Percorso share di rete (es: //192.168.1.100/videos)
NETWORK_SHARE_PATH=//tuo-server/cartella-video

# Credenziali (lascia vuoto per accesso guest)
NETWORK_SHARE_USER=nomeutente
NETWORK_SHARE_PASSWORD=password

# Punto di montaggio locale
NETWORK_SHARE_MOUNT_POINT=/mnt/network_videos

# Porta web (default: 5000)
FLASK_PORT=5000

# Volume di default (0-100)
VOLUME=100

# Estensioni video supportate
VIDEO_EXTENSIONS=mp4,avi,mkv,mov,wmv,flv,webm
```

### 4. Avvia il servizio

```bash
# Avvio manuale
sudo systemctl start proiettore

# Verifica stato
sudo systemctl status proiettore

# Abilita avvio automatico
sudo systemctl enable proiettore
```

## Utilizzo

### Accesso all'interfaccia web

Apri il browser e vai a:

```
http://<indirizzo-ip-raspberry>:5000
```

Per trovare l'IP del tuo Raspberry Pi:

```bash
hostname -I
```

### Interfaccia Web

L'interfaccia è divisa in tre sezioni principali:

#### 1. Controlli Riproduzione (Sinistra)
- **Play/Pausa/Stop**: Controllo riproduzione
- **Volume**: Regolazione volume (0-100%)
- **Precedente/Successivo**: Navigazione playlist
- **Stato**: Visualizzazione video corrente e stato player

#### 2. Lista Video (Centro)
- Visualizza tutti i video disponibili
- Click per selezionare
- Doppio click per riprodurre
- Pulsante "Carica Playlist" per caricare tutti i video

#### 3. Programmazione (Destra)
- **Aggiungi programmazione**: Imposta orari di riproduzione automatica
- **Giorni della settimana**: Specifica giorni (es: mon,wed,fri) o lascia vuoto per ogni giorno
- **Gestione**: Abilita/Disabilita o elimina programmazioni

### Gestione Cartella di Rete

1. **Monta**: Connette alla cartella di rete configurata
2. **Smonta**: Disconnette la cartella di rete
3. **Aggiorna Video**: Ricarica l'elenco dei video disponibili

### Esempi di Programmazione

**Riproduzione giornaliera:**
- Nome: "Video mattutino"
- Ora: 08:00
- Giorni: (lascia vuoto)

**Riproduzione settimanale:**
- Nome: "Video weekend"
- Ora: 10:00
- Giorni: sat,sun

**Riproduzione specifica:**
- Nome: "Promemoria lunedì"
- Ora: 09:00
- Giorni: mon

## Esecuzione Manuale (Sviluppo)

Per test e sviluppo, puoi eseguire l'applicazione manualmente:

```bash
./run.sh
```

Oppure:

```bash
source venv/bin/activate
python3 app.py
```

## Log e Debug

### Visualizza log del servizio

```bash
# Log in tempo reale
sudo journalctl -u proiettore -f

# Ultimi 100 log
sudo journalctl -u proiettore -n 100

# Log di oggi
sudo journalctl -u proiettore --since today
```

### File di log

```bash
# Log applicazione
tail -f proiettore.log
```

## Risoluzione Problemi

### La cartella di rete non si monta

1. Verifica la connettività di rete:
   ```bash
   ping <indirizzo-server>
   ```

2. Testa manualmente il mount:
   ```bash
   sudo mount -t cifs //server/share /mnt/test -o username=user,password=pass
   ```

3. Verifica i permessi:
   ```bash
   ls -la /mnt/network_videos
   ```

### Video non si riproduce

1. Verifica che MPV sia installato:
   ```bash
   mpv --version
   ```

2. Testa la riproduzione manualmente:
   ```bash
   mpv /path/to/video.mp4
   ```

3. Controlla i log per errori:
   ```bash
   sudo journalctl -u proiettore -f
   ```

### Interfaccia web non accessibile

1. Verifica che il servizio sia attivo:
   ```bash
   sudo systemctl status proiettore
   ```

2. Verifica la porta configurata:
   ```bash
   netstat -tlnp | grep 5000
   ```

3. Controlla il firewall:
   ```bash
   sudo ufw status
   ```

### Audio non funziona

1. Verifica le uscite audio disponibili:
   ```bash
   aplay -l
   ```

2. Testa l'audio:
   ```bash
   speaker-test -t wav
   ```

3. Configura l'uscita audio predefinita:
   ```bash
   sudo raspi-config
   # System Options > Audio > Seleziona output
   ```

## Aggiornamento

```bash
cd proiettore
git pull
source venv/bin/activate
pip install -r requirements.txt --upgrade
sudo systemctl restart proiettore
```

## Disinstallazione

```bash
# Ferma e disabilita il servizio
sudo systemctl stop proiettore
sudo systemctl disable proiettore

# Rimuovi il servizio
sudo rm /etc/systemd/system/proiettore.service
sudo systemctl daemon-reload

# Smonta la cartella di rete
sudo umount /mnt/network_videos

# Rimuovi i file (opzionale)
cd ..
rm -rf proiettore
```

## API REST

L'applicazione espone API REST per integrazione con altri sistemi:

### Status
```
GET /api/status
```

### Video
```
GET /api/videos
POST /api/play {"path": "/path/to/video.mp4"}
POST /api/stop
POST /api/pause
POST /api/next
POST /api/previous
POST /api/volume {"volume": 50}
POST /api/playlist {"videos": ["/path1.mp4", "/path2.mp4"]}
```

### Network
```
POST /api/network/mount
POST /api/network/unmount
```

### Schedules
```
GET /api/schedules
POST /api/schedules {"name": "...", "video_path": "...", "hour": 10, "minute": 30, "days_of_week": "mon,wed"}
DELETE /api/schedules/<id>
POST /api/schedules/<id>/toggle
```

## Configurazione Avanzata

### Auto-start con video specifico

Modifica `.env`:
```bash
AUTO_START=true
LOOP_PLAYLIST=true
```

### Cambio porta web

Modifica `.env`:
```bash
FLASK_PORT=8080
```

Poi riavvia:
```bash
sudo systemctl restart proiettore
```

### Supporto HTTPS

Per accesso sicuro, usa un reverse proxy come Nginx:

```bash
sudo apt install nginx
```

Configura Nginx per fare proxy verso `http://localhost:5000`

## Contribuire

Contributi sono benvenuti! Per favore:

1. Fork del repository
2. Crea un branch per la tua feature
3. Commit delle modifiche
4. Push al branch
5. Apri una Pull Request

## Licenza

MIT License - vedi file LICENSE per dettagli

## Supporto

Per problemi o domande:
- Apri una issue su GitHub
- Consulta la documentazione

## Autore

Creato per Raspberry Pi 5

---

**Nota**: Questo software è stato sviluppato e testato su Raspberry Pi 5. Dovrebbe funzionare anche su Pi 4 e Pi 3, ma potrebbero essere necessari aggiustamenti delle prestazioni.
