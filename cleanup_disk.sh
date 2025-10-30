#!/bin/bash
# Script per pulire spazio disco sul Raspberry Pi

echo "=== Pulizia Spazio Disco ==="
echo ""

# 1. Verifica spazio attuale
echo "1. Spazio disco attuale:"
df -h
echo ""

# 2. Pulisci cache APT
echo "2. Pulizia cache APT..."
sudo apt-get clean
echo "✓ Cache APT pulita"
echo ""

# 3. Pulisci vecchi log
echo "3. Pulizia log vecchi..."
sudo journalctl --vacuum-time=7d
echo "✓ Log vecchi eliminati"
echo ""

# 4. Pulisci file temporanei
echo "4. Pulizia file temporanei..."
sudo rm -rf /tmp/*
sudo rm -rf /var/tmp/*
echo "✓ File temporanei eliminati"
echo ""

# 5. Pulisci cache video (se esiste)
if [ -d "/home/ggeronzi/proiettore/video_cache" ]; then
    echo "5. Pulizia cache video..."
    CACHE_SIZE=$(du -sh /home/ggeronzi/proiettore/video_cache | cut -f1)
    echo "   Dimensione cache: $CACHE_SIZE"
    rm -rf /home/ggeronzi/proiettore/video_cache/*
    echo "✓ Cache video pulita"
else
    echo "5. Cache video non trovata (OK)"
fi
echo ""

# 6. Pulisci oggetti git loose
if [ -d ".git/objects" ]; then
    echo "6. Ottimizzazione repository git..."
    git gc --prune=now --aggressive
    echo "✓ Repository git ottimizzato"
else
    echo "6. Directory .git non trovata (eseguire nella directory del progetto)"
fi
echo ""

# 7. Verifica spazio finale
echo "=== Spazio finale ==="
df -h
echo ""
echo "✅ Pulizia completata!"
