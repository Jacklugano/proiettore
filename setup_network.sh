#!/bin/bash
# Interactive script to configure network share

echo "========================================="
echo "  Network Share Configuration"
echo "========================================="
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    if [ -f .env.example ]; then
        cp .env.example .env
    else
        echo "Error: .env.example not found"
        exit 1
    fi
fi

# Get current values
source .env 2>/dev/null || true

echo "Current configuration:"
echo "  Share path: ${NETWORK_SHARE_PATH:-not set}"
echo "  Username: ${NETWORK_SHARE_USER:-not set}"
echo "  Mount point: ${NETWORK_SHARE_MOUNT_POINT:-/mnt/network_videos}"
echo ""

# Prompt for network share path
read -p "Network share path (e.g., //192.168.1.100/videos): " share_path
if [ -z "$share_path" ]; then
    echo "Error: Share path cannot be empty"
    exit 1
fi

# Prompt for username
read -p "Username (leave empty for guest): " username

# Prompt for password
if [ -n "$username" ]; then
    read -sp "Password: " password
    echo ""
else
    password=""
fi

# Prompt for mount point
read -p "Mount point [/mnt/network_videos]: " mount_point
mount_point=${mount_point:-/mnt/network_videos}

# Create mount point
sudo mkdir -p "$mount_point"
sudo chown $USER:$USER "$mount_point"

# Update .env file
echo "Updating .env file..."

# Remove old values
sed -i '/^NETWORK_SHARE_PATH=/d' .env
sed -i '/^NETWORK_SHARE_USER=/d' .env
sed -i '/^NETWORK_SHARE_PASSWORD=/d' .env
sed -i '/^NETWORK_SHARE_MOUNT_POINT=/d' .env

# Add new values
echo "" >> .env
echo "# Network configuration - $(date)" >> .env
echo "NETWORK_SHARE_PATH=$share_path" >> .env
echo "NETWORK_SHARE_USER=$username" >> .env
echo "NETWORK_SHARE_PASSWORD=$password" >> .env
echo "NETWORK_SHARE_MOUNT_POINT=$mount_point" >> .env

echo ""
echo "Configuration saved!"
echo ""

# Test mount
read -p "Test mount now? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Testing mount..."

    # Build mount command
    if [ -n "$username" ]; then
        sudo mount -t cifs "$share_path" "$mount_point" -o username="$username",password="$password",iocharset=utf8
    else
        sudo mount -t cifs "$share_path" "$mount_point" -o guest,iocharset=utf8
    fi

    if [ $? -eq 0 ]; then
        echo "Success! Share mounted at $mount_point"
        ls -la "$mount_point"
        echo ""
        read -p "Unmount now? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            sudo umount "$mount_point"
            echo "Unmounted"
        fi
    else
        echo "Error: Failed to mount share"
        echo "Please check your configuration and network connectivity"
    fi
fi

echo ""
echo "Configuration complete!"
