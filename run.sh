#!/bin/bash
# Simple run script for development/testing

# Activate virtual environment if exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Check if .env exists
if [ ! -f .env ]; then
    echo "Warning: .env file not found"
    echo "Copy .env.example to .env and configure it"
    echo ""
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Run the application
echo "Starting Proiettore..."
echo "Access the web interface at: http://$(hostname -I | awk '{print $1}'):5000"
echo ""
echo "Press Ctrl+C to stop"
echo ""

python3 app.py
