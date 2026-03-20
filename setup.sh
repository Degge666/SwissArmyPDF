#!/bin/bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

source .venv/bin/activate

# Prüfen, ob ALLE Module (fitz, PyQt6 UND PIL) installiert sind
python3 -c "import fitz, PyQt6, PIL" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "Dependencies missing. Attempting to install..."

    if ! ping -c 1 -W 2 8.8.8.8 > /dxev/null 2>&1; then
        echo "ERROR: No internet connection. Cannot install dependencies."
        exit 1
    fi

    pip install --upgrade pip
    # Hier wurde Pillow hinzugefügt
    pip install pymupdf PyQt6 Pillow
else
    echo "Dependencies already satisfied."
fi

echo "Launching SwissArmyPDF..."
python3 main.py