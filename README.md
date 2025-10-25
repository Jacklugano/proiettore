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

### Configurazione Sudoers (Importante!)

Per permettere al servizio di montare cartelle di rete senza richiedere password:

```bash
cd proiettore
sudo ./setup_sudoers.sh
```

Questo script configura automaticamente i permessi necessari per l'utente corrente.

> **Nota**: Se hai già installato Proiettore e hai problemi di mount con errore "No such file or directory: 'sudo'", esegui questo comando e poi riavvia il servizio con `sudo systemctl restart proiettore`

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

### Problemi connessione NAS Synology

#### ❌ Errore: "Connessione fallita"

**Causa 1: SMB non abilitato o versione non compatibile**
- Soluzione: Sul Synology vai in `Pannello di Controllo` → `Servizi File` → `SMB`
- Abilita SMB/CIFS
- Imposta versione minima su `SMB2` o superiore
- Riavvia il servizio SMB

**Causa 2: Percorso share errato**
```bash
✗ ERRATO: /volume1/video
✗ ERRATO: \\192.168.1.50\video
✓ CORRETTO: //192.168.1.50/video
✓ CORRETTO: //synology-nas/video
```

**Causa 3: Credenziali non valide**
- Usa un utente Synology esistente (non admin DSM se disabilitato)
- La password deve essere corretta
- L'utente deve avere permessi di lettura sulla cartella

**Causa 4: Firewall blocca connessione**
- Sul Synology: `Pannello di Controllo` → `Sicurezza` → `Firewall`
- Assicurati che la porta SMB (445) sia aperta
- Oppure disabilita temporaneamente il firewall per test

**Causa 5: Cartella non condivisa**
- Sul Synology: `Pannello di Controllo` → `Cartella Condivisa`
- Verifica che la cartella sia effettivamente condivisa
- Controlla i permessi dell'utente sulla cartella

#### 🔧 Test Diagnostici

**1. Verifica connettività di rete**
```bash
# Dal Raspberry Pi, verifica che il NAS risponda
ping 192.168.1.50

# Verifica che la porta SMB sia aperta
telnet 192.168.1.50 445
# Dovresti vedere "Connected" se la porta è aperta
```

**2. Test mount manuale con logging dettagliato**
```bash
# Prova mount manuale per vedere errore preciso
sudo mount -t cifs //192.168.1.50/video /mnt/test \
  -o username=tuoutente,password=tuapassword,vers=3.0,sec=ntlmssp -v

# Se fallisce, prova con SMB 2.1
sudo mount -t cifs //192.168.1.50/video /mnt/test \
  -o username=tuoutente,password=tuapassword,vers=2.1,sec=ntlmssp -v
```

**3. Verifica versioni SMB supportate dal NAS**
```bash
# Installa smbclient
sudo apt-get install smbclient

# Testa connessione e vedi versioni supportate
smbclient -L //192.168.1.50 -U tuoutente
```

**4. Controlla i log di sistema**
```bash
# Guarda log mount dettagliati
sudo dmesg | tail -20

# Log del servizio
sudo journalctl -u proiettore -n 50
```

#### 📋 Checklist Synology

Prima di contattare il supporto, verifica:

- [ ] NAS acceso e raggiungibile in rete
- [ ] Indirizzo IP corretto (prova a pingare)
- [ ] SMB abilitato su Synology
- [ ] Versione SMB 2.0 o superiore attivata
- [ ] Cartella effettivamente condivisa
- [ ] Username e password corretti
- [ ] Utente ha permessi di lettura sulla cartella
- [ ] Firewall Synology permette connessioni SMB
- [ ] Formato percorso corretto: `//IP/cartella`
- [ ] Testato con pulsante "Testa Connessione" nell'interfaccia web

#### 💡 Soluzioni Rapide

**Problema: "Permission denied" (mount error 13)**

Questo è l'errore più comune. Segui questi step IN ORDINE:

**Step 1: Verifica credenziali Synology**
```bash
# Testa login SSH sul Synology (se possibile)
ssh Giacomo@192.168.178.29

# Se funziona, le credenziali sono corrette
```

**Step 2: Verifica permessi cartella sul NAS**
1. Apri DSM (interfaccia web Synology)
2. Vai in **Pannello di Controllo** → **Cartella Condivisa**
3. Trova la cartella "Video" (o come si chiama)
4. Clicca **Modifica** → Tab **Permessi**
5. Assicurati che l'utente "Giacomo" sia nella lista
6. Imposta permessi **Lettura/Scrittura** (o almeno Lettura)
7. Clicca **Salva**

**Step 3: Verifica servizio SMB**
1. **Pannello di Controllo** → **Servizi File** → **SMB/AFP/NFS**
2. Tab **SMB**
3. Spunta **Abilita servizio SMB**
4. **Versione SMB massima**: SMB3
5. **Versione SMB minima**: SMB2 (non SMB1!)
6. Clicca **Applica**

**Step 4: Verifica utente abilitato per SMB**
1. **Pannello di Controllo** → **Utente & Gruppo**
2. Seleziona utente "Giacomo"
3. Clicca **Modifica**
4. Tab **Applicazioni**
5. Assicurati che "Deny access to all applications" NON sia spuntato
6. Clicca **OK**

**Step 5: Test manuale dal Raspberry Pi**
```bash
# Crea directory di test
sudo mkdir -p /mnt/test

# Crea file credenziali
cat > /tmp/creds.txt <<EOF
username=Giacomo
password=TUA_PASSWORD_QUI
EOF

chmod 600 /tmp/creds.txt

# Prova mount SENZA sec=ntlmssp (Synology non lo supporta!)
sudo mount -t cifs //192.168.178.29/Video /mnt/test -o credentials=/tmp/creds.txt,vers=3.0,iocharset=utf8

# Se funziona:
ls /mnt/test  # Dovresti vedere i tuoi video

# Pulisci
sudo umount /mnt/test
rm /tmp/creds.txt
```

**⚠️ NOTA IMPORTANTE per Synology NAS:**
- **NON usare** `sec=ntlmssp` con Synology - causa "Permission denied"!
- Il sistema auto-negozia automaticamente il metodo di sicurezza corretto
- Funziona con Synology DSM 6.x, 7.x, QNAP, e Windows Server

Se il test manuale funziona, allora riprova dall'interfaccia web!

**Problema: "Host is down"**
- Verifica che il NAS non sia in ibernazione
- Su Synology: Pannello di Controllo → Hardware e alimentazione → Ibernazione HDD
- Disabilita ibernazione o imposta timer più lungo

**Problema: "No route to host"**
- Raspberry Pi e NAS devono essere sulla stessa rete
- Verifica IP con `ip addr` sul Raspberry Pi
- Verifica IP del NAS nel pannello Synology

### La cartella di rete non si monta (generico)

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
