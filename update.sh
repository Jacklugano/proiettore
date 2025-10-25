#!/bin/bash
# Proiettore Update Script
# Aggiorna automaticamente Proiettore all'ultima versione

set -e

echo "========================================="
echo "  Proiettore - Aggiornamento Sistema"
echo "========================================="
echo ""

# Colori per output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Verifica se siamo nella directory corretta
if [ ! -f "app.py" ]; then
    echo -e "${RED}Errore: Esegui questo script dalla directory di Proiettore${NC}"
    exit 1
fi

echo -e "${YELLOW}[1/6]${NC} Controllo aggiornamenti disponibili..."
git fetch origin

# Verifica se ci sono aggiornamenti
LOCAL=$(git rev-parse @)
REMOTE=$(git rev-parse @{u})

if [ "$LOCAL" = "$REMOTE" ]; then
    echo -e "${GREEN}✓ Proiettore è già aggiornato!${NC}"
    echo ""
    read -p "Vuoi controllare comunque le dipendenze? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 0
    fi
    SKIP_GIT=true
else
    echo -e "${GREEN}✓ Aggiornamenti disponibili!${NC}"
    echo ""
    echo "Modifiche disponibili:"
    git log HEAD..@{u} --oneline --decorate
    echo ""
    SKIP_GIT=false
fi

# Chiedi conferma
if [ "$SKIP_GIT" = false ]; then
    read -p "Procedere con l'aggiornamento? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Aggiornamento annullato."
        exit 0
    fi
fi

echo ""
echo -e "${YELLOW}[2/6]${NC} Backup configurazione..."

# Backup del database se esiste
if [ -f "proiettore.db" ]; then
    cp proiettore.db proiettore.db.backup.$(date +%Y%m%d_%H%M%S)
    echo -e "${GREEN}✓ Database salvato${NC}"
fi

# Backup .env se esiste
if [ -f ".env" ]; then
    cp .env .env.backup.$(date +%Y%m%d_%H%M%S)
    echo -e "${GREEN}✓ File .env salvato${NC}"
fi

echo ""
echo -e "${YELLOW}[3/6]${NC} Arresto servizio..."

# Ferma il servizio se è in esecuzione
if systemctl is-active --quiet proiettore; then
    sudo systemctl stop proiettore
    echo -e "${GREEN}✓ Servizio arrestato${NC}"
else
    echo -e "${YELLOW}⚠ Servizio non in esecuzione${NC}"
fi

echo ""
echo -e "${YELLOW}[4/6]${NC} Download aggiornamenti..."

# Fai il pull se necessario
if [ "$SKIP_GIT" = false ]; then
    git pull origin $(git rev-parse --abbrev-ref HEAD)
    echo -e "${GREEN}✓ Codice aggiornato${NC}"
else
    echo -e "${YELLOW}⚠ Skip git pull${NC}"
fi

echo ""
echo -e "${YELLOW}[5/6]${NC} Aggiornamento dipendenze..."

# Attiva virtual environment se esiste
if [ -d "venv" ]; then
    source venv/bin/activate
    echo -e "${GREEN}✓ Virtual environment attivato${NC}"
else
    echo -e "${YELLOW}⚠ Virtual environment non trovato, lo creo...${NC}"
    python3 -m venv venv
    source venv/bin/activate
fi

# Aggiorna pip
pip install --upgrade pip --quiet

# Installa/aggiorna dipendenze
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt --upgrade --quiet
    echo -e "${GREEN}✓ Dipendenze aggiornate${NC}"
fi

echo ""
echo -e "${YELLOW}[6/6]${NC} Riavvio servizio..."

# Riavvia il servizio
sudo systemctl start proiettore

# Attendi un momento per il servizio
sleep 2

# Verifica lo stato
if systemctl is-active --quiet proiettore; then
    echo -e "${GREEN}✓ Servizio riavviato con successo${NC}"
else
    echo -e "${RED}✗ Errore nel riavvio del servizio${NC}"
    echo ""
    echo "Controlla i log con:"
    echo "  sudo journalctl -u proiettore -n 50"
    exit 1
fi

echo ""
echo "========================================="
echo -e "${GREEN}  Aggiornamento completato!${NC}"
echo "========================================="
echo ""
echo "Informazioni:"
echo "  • Versione: $(git describe --tags --always)"
echo "  • Branch: $(git rev-parse --abbrev-ref HEAD)"
echo "  • Ultimo commit: $(git log -1 --pretty=format:'%h - %s')"
echo ""
echo "Comandi utili:"
echo "  • Stato servizio: sudo systemctl status proiettore"
echo "  • Log in tempo reale: sudo journalctl -u proiettore -f"
echo "  • Interfaccia web: http://$(hostname -I | awk '{print $1}'):5000"
echo ""
echo -e "${GREEN}Backup salvati:${NC}"
ls -lht *.backup.* 2>/dev/null | head -5 || echo "  Nessun backup creato"
echo ""
