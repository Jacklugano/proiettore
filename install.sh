#!/bin/bash
# Proiettore Installation Script for Raspberry Pi 5

set -e

echo "========================================="
echo "  Proiettore - Video Player Installer"
echo "========================================="
echo ""

# Check if running on Raspberry Pi
if [ ! -f /proc/device-tree/model ] || ! grep -q "Raspberry Pi" /proc/device-tree/model; then
    echo "Warning: This script is designed for Raspberry Pi"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Update system
echo "Updating system packages..."
sudo apt-get update

# Install required packages
echo "Installing dependencies..."
sudo apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    mpv \
    cifs-utils \
    git

# Create virtual environment
echo "Creating Python virtual environment..."
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install Python requirements
echo "Installing Python packages..."
pip install --upgrade pip
pip install -r requirements.txt

# Create .env file if not exists
if [ ! -f .env ]; then
    echo "Creating .env configuration file..."
    cp .env.example .env
    echo ""
    echo "IMPORTANT: Edit the .env file to configure your network share:"
    echo "  nano .env"
    echo ""
fi

# Create mount point
echo "Creating mount point directory..."
sudo mkdir -p /mnt/network_videos
sudo chown $USER:$USER /mnt/network_videos

# Configure sudoers for passwordless mount
echo "Configuring sudoers for mount/umount..."
if [ -f "./setup_sudoers.sh" ]; then
    sudo ./setup_sudoers.sh
else
    echo "Warning: setup_sudoers.sh not found. You may need to configure sudoers manually."
fi

# Install systemd service
echo "Installing systemd service..."
cat > /tmp/proiettore.service <<EOF
[Unit]
Description=Proiettore Video Player
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$(pwd)
Environment="PATH=$(pwd)/venv/bin"
ExecStart=$(pwd)/venv/bin/python app.py
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

sudo mv /tmp/proiettore.service /etc/systemd/system/
sudo systemctl daemon-reload

echo ""
echo "========================================="
echo "  Installation Complete!"
echo "========================================="
echo ""
echo "Next steps:"
echo "1. Edit the configuration file:"
echo "   nano .env"
echo ""
echo "2. Configure your network share path, username, and password"
echo ""
echo "3. Start the service:"
echo "   sudo systemctl start proiettore"
echo ""
echo "4. Enable auto-start on boot:"
echo "   sudo systemctl enable proiettore"
echo ""
echo "5. Access the web interface:"
echo "   http://$(hostname -I | awk '{print $1}'):5000"
echo ""
echo "To view logs:"
echo "   sudo journalctl -u proiettore -f"
echo ""
