# Fix per nascondere il terminale durante le transizioni

## Problema
Il terminale diventa visibile durante la transizione di 1.5 secondi tra un video e l'altro.

## Soluzione
Questa versione usa `fbi` (framebuffer image viewer) per mostrare un'immagine nera direttamente sul framebuffer durante le transizioni, coprendo completamente il terminale.

## Installazione pacchetti necessari

Esegui questi comandi sul Raspberry Pi:

```bash
# 1. Installa fbi (framebuffer image viewer)
sudo apt-get update
sudo apt-get install -y fbi

# 2. Installa ImageMagick (per creare l'immagine nera)
sudo apt-get install -y imagemagick

# 3. Crea l'immagine nera (verrà creata automaticamente al primo avvio, ma puoi crearla manualmente)
cd ~/proiettore
convert -size 1920x1080 xc:black black.png

# 4. Riavvia il servizio
sudo systemctl restart proiettore

# 5. Verifica che funzioni
sudo systemctl status proiettore
tail -f ~/proiettore/proiettore.log
```

## Come funziona

1. All'avvio, il programma nasconde permanentemente il cursore del terminale
2. Durante le transizioni tra video, invece di mostrare solo uno schermo nero, viene avviato `fbi` che mostra un'immagine nera sul framebuffer
3. Quando il nuovo video inizia, `fbi` viene terminato e MPV prende il controllo del framebuffer
4. Il terminale rimane sempre nascosto sotto l'immagine nera o il video

## Verifica funzionamento

Nel log dovresti vedere questi messaggi:

```
INFO - Hiding terminal permanently on all TTYs...
INFO - Terminal permanently hidden
DEBUG - Black screen display started (PID: ...)
DEBUG - Black screen display stopped
```

## Troubleshooting

Se il terminale è ancora visibile:

1. Verifica che `fbi` sia installato:
   ```bash
   which fbi
   ```

2. Verifica che l'immagine nera esista:
   ```bash
   ls -lh ~/proiettore/black.png
   ```

3. Testa `fbi` manualmente:
   ```bash
   sudo fbi --noverbose --autozoom -T 1 ~/proiettore/black.png
   # Premi 'q' per uscire
   ```

4. Controlla i log per errori:
   ```bash
   tail -50 ~/proiettore/proiettore.log | grep -i "black\|terminal\|fbi"
   ```
