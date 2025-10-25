# Proiettore 🎬

Sistema di riproduzione video automatizzato per Raspberry Pi 5 con supporto per cartelle di rete e programmazione.

## Caratteristiche

- 📹 **Riproduzione video**: Supporta tutti i formati comuni (MP4, AVI, MKV, MOV, WMV, FLV, WebM)
- 🌐 **Cartelle di rete**: Accesso a video su share di rete SMB/CIFS
- 🖥️ **Output HDMI**: Video su HDMI con audio tramite uscita Raspberry Pi
- 📅 **Schedulazione**: Programmazione automatica di riproduzione video
- 🎛️ **Interfaccia web**: Controllo completo tramite browser
- ⚙️ **Configurazione web**: Configurazione completa tramite interfaccia web (nessun file da modificare!)
- 🔄 **Playlist**: Gestione playlist e riproduzione continua
- ⚡ **Auto-start**: Avvio automatico all'accensione del Raspberry Pi
- 💾 **Database**: Tutte le configurazioni persistono nel database

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

### 3. Avvia il servizio

```bash
# Avvio manuale
sudo systemctl start proiettore

# Verifica stato
sudo systemctl status proiettore

# Abilita avvio automatico
sudo systemctl enable proiettore
```

### 4. Configurazione Iniziale

**Apri l'interfaccia web** nel browser:
```
http://<indirizzo-ip-raspberry>:5000
```

Vai alla tab **"Impostazioni"** e configura:

1. **Cartella di Rete**:
   - Inserisci il percorso della share (es: //192.168.1.100/videos)
   - Inserisci username e password (se richieste)
   - Clicca "Testa Connessione" per verificare
   - Clicca "Salva Configurazione"

2. **Impostazioni Player** (opzionale):
   - Imposta volume predefinito
   - Configura estensioni video
   - Abilita loop playlist o avvio automatico

3. **Torna alla tab Player**:
   - Clicca "Monta" per montare la cartella di rete
   - Clicca "Aggiorna Video" per caricare la lista

Fatto! Ora puoi riprodurre i tuoi video.

> **Configurazione Alternativa (Opzionale)**: Se preferisci, puoi configurare manualmente modificando il file `.env` o usando lo script `./setup_network.sh`. Tuttavia, **la configurazione tramite web è il metodo raccomandato** perché più semplice e immediato.

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

L'interfaccia è organizzata in **3 tab principali**:

#### Tab 1: Player
Gestione della riproduzione video:
- **Controlli Riproduzione**: Play, Pausa, Stop, Precedente, Successivo
- **Volume**: Regolazione volume (0-100%)
- **Stato Player**: Visualizzazione video corrente e stato
- **Cartella di Rete**: Monta/smonta cartella e aggiorna lista video
- **Lista Video**: Tutti i video disponibili (click per selezionare, doppio click per riprodurre)
- **Carica Playlist**: Carica tutti i video nella playlist

#### Tab 2: Programmazione
Schedulazione automatica della riproduzione:
- **Nuova Programmazione**: Crea schedule con nome, video, ora e giorni
- **Programmazioni Attive**: Lista delle programmazioni con possibilità di abilitare/disabilitare ed eliminare
- **Giorni della settimana**: Specifica giorni (es: mon,wed,fri) o lascia vuoto per ogni giorno

#### Tab 3: Impostazioni
**Configurazione completa tramite interfaccia web** (nessun file da modificare manualmente!):

**Configurazione Cartella di Rete:**
- **Percorso Share**: Indirizzo della cartella di rete (es: //192.168.1.100/videos)
- **Username/Password**: Credenziali di accesso (opzionali, lascia vuoto per guest)
- **Punto di Montaggio**: Cartella locale dove montare (default: /mnt/network_videos)
- **Testa Connessione**: Verifica la connessione prima di salvare
- **Salva**: Salva la configurazione nel database (persistente)

**Configurazione Player:**
- **Volume Predefinito**: Volume iniziale (0-100%)
- **Estensioni Video**: Formati supportati (separati da virgola)
- **Loop Playlist**: Ripeti automaticamente la playlist
- **Avvio Automatico**: Carica e avvia la playlist all'avvio del sistema
- **Salva**: Salva la configurazione nel database (persistente)

> **Nota**: Tutte le configurazioni sono salvate nel database e non richiedono la modifica di file. Le impostazioni persistono anche dopo il riavvio del sistema.

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

## Aggiornamento

Per aggiornare Proiettore all'ultima versione disponibile, usa lo script automatico:

### Metodo 1: Script Automatico (Raccomandato)

```bash
cd proiettore
./update.sh
```

Lo script farà automaticamente:
1. ✅ Controlla aggiornamenti disponibili
2. ✅ Backup automatico di database e configurazione
3. ✅ Arresta il servizio
4. ✅ Scarica gli aggiornamenti da Git
5. ✅ Aggiorna le dipendenze Python
6. ✅ Riavvia il servizio
7. ✅ Verifica il corretto funzionamento

### Metodo 2: Aggiornamento Manuale

```bash
cd proiettore

# Backup manuale
cp proiettore.db proiettore.db.backup
cp .env .env.backup

# Ferma il servizio
sudo systemctl stop proiettore

# Aggiorna il codice
git pull

# Aggiorna dipendenze
source venv/bin/activate
pip install -r requirements.txt --upgrade

# Riavvia il servizio
sudo systemctl start proiettore

# Verifica stato
sudo systemctl status proiettore
```

### Verifica Versione

```bash
# Dalla directory proiettore
git log -1 --oneline

# Oppure controlla nella tab "Impostazioni" dell'interfaccia web
```

### Note Importanti

- ⚠️ **I backup sono automatici**: Database e configurazione vengono salvati prima dell'aggiornamento
- ⚠️ **Le configurazioni sono preservate**: Tutte le tue impostazioni rimarranno invariate
- ⚠️ **Il servizio si riavvia automaticamente**: Nessun intervento manuale necessario
- ✅ **Zero downtime**: L'aggiornamento richiede solo 10-30 secondi

### Rollback (se necessario)

Se qualcosa va storto, puoi tornare alla versione precedente:

```bash
# Ripristina database
cp proiettore.db.backup.YYYYMMDD_HHMMSS proiettore.db

# Ripristina configurazione
cp .env.backup.YYYYMMDD_HHMMSS .env

# Torna alla versione precedente
git log --oneline  # trova l'hash del commit precedente
git checkout HASH_COMMIT_PRECEDENTE

# Riavvia
sudo systemctl restart proiettore
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
