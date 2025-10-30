# Fix per nascondere il terminale durante le transizioni

## Problema
Il terminale diventa visibile durante la transizione di 1.5 secondi tra un video e l'altro.

## Soluzione
Questa versione scrive **direttamente nel framebuffer** `/dev/fb0` con pixel neri. Questo è **ISTANTANEO** - nessun ritardo da avvio di processi esterni.

## Installazione - NON servono pacchetti aggiuntivi!

Esegui questi comandi sul Raspberry Pi:

```bash
cd ~/proiettore

# 1. Fai il pull delle modifiche
git pull origin claude/fix-terminal-visibility-011CUe1uBx6vPuH8cijKZNmW

# 2. Riavvia il servizio
sudo systemctl restart proiettore

# 3. Verifica che funzioni
sudo systemctl status proiettore
tail -f ~/proiettore/proiettore.log
```

## Come funziona

1. **All'avvio**: Il programma nasconde permanentemente il cursore del terminale su tutti i TTY
2. **Durante transizioni**: Il framebuffer `/dev/fb0` viene riempito istantaneamente con pixel neri (8.3MB di zeri)
3. **Quando inizia il video**: MPV sovrascrive i pixel neri con il video
4. **Risultato**: Zero ritardi, zero processi esterni, nero istantaneo

## Vantaggi rispetto a `fbi`

- ✅ **ISTANTANEO**: Nessun tempo di avvio processo
- ✅ **Nessuna dipendenza**: Non servono pacchetti esterni
- ✅ **Più affidabile**: Scrittura diretta nel framebuffer
- ✅ **Zero overhead**: Nessun processo in background

## Verifica funzionamento

Nel log dovresti vedere questi messaggi:

```
INFO - Hiding terminal permanently on all TTYs...
INFO - Terminal permanently hidden
DEBUG - Black screen activated (instant framebuffer fill)
DEBUG - Framebuffer /dev/fb0 filled with black (instant)
DEBUG - Black screen cleared (framebuffer ready for video)
```

## Troubleshooting

Se il terminale è ancora visibile per un istante:

1. Verifica i permessi del framebuffer:
   ```bash
   ls -l /dev/fb0
   sudo chmod 666 /dev/fb0  # Se necessario
   ```

2. Verifica che il framebuffer esista:
   ```bash
   ls -l /dev/fb*
   ```

3. Controlla i log per errori:
   ```bash
   tail -100 ~/proiettore/proiettore.log | grep -i "framebuffer\|terminal\|black"
   ```

4. Testa la scrittura manuale nel framebuffer:
   ```bash
   # Riempi schermo di nero (1920x1080x4 = 8.3MB)
   sudo dd if=/dev/zero of=/dev/fb0 bs=8294400 count=1
   ```
