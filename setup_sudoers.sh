#!/bin/bash
# Script per configurare sudoers per permettere mount senza password

echo "Configurazione sudoers per Proiettore..."

# Determina l'utente corrente
CURRENT_USER=${SUDO_USER:-$USER}

# Crea il file sudoers
SUDOERS_FILE="/etc/sudoers.d/proiettore"

echo "Creazione regola sudoers per utente: $CURRENT_USER"

# Crea il contenuto del file sudoers
cat > /tmp/proiettore-sudoers <<EOF
# Proiettore - Allow mount/umount without password
$CURRENT_USER ALL=(ALL) NOPASSWD: /bin/mount -t cifs * * -o *
$CURRENT_USER ALL=(ALL) NOPASSWD: /usr/bin/mount -t cifs * * -o *
$CURRENT_USER ALL=(ALL) NOPASSWD: /bin/mount
$CURRENT_USER ALL=(ALL) NOPASSWD: /usr/bin/mount
$CURRENT_USER ALL=(ALL) NOPASSWD: /bin/umount *
$CURRENT_USER ALL=(ALL) NOPASSWD: /usr/bin/umount *
EOF

# Verifica la sintassi
if visudo -c -f /tmp/proiettore-sudoers; then
    echo "Sintassi corretta, installazione..."
    sudo cp /tmp/proiettore-sudoers "$SUDOERS_FILE"
    sudo chmod 0440 "$SUDOERS_FILE"
    echo "✓ Configurazione sudoers completata!"
    echo "✓ L'utente $CURRENT_USER può ora montare/smontare senza password"
else
    echo "✗ Errore nella sintassi del file sudoers!"
    exit 1
fi

# Pulisci
rm -f /tmp/proiettore-sudoers

echo ""
echo "Configurazione completata con successo!"
