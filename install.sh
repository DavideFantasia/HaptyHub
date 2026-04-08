#!/bin/bash

echo "==========================================="
echo " Installazione di HaptyGraph - Lettore NVA "
echo "==========================================="

# Creazione dell'ambiente virtuale Python
echo "[1/4] Creazione dell'ambiente virtuale (venv)..."
python3 -m venv venv

# Installazione delle dipendenze
echo "[2/4] Installazione delle librerie Python..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt # Assicurati di avere questo file con scritto 'pyserial' ecc.
deactivate

# Configurazione permessi Hardware (Regole udev)
echo "[3/4] Configurazione dei permessi USB (richiede password amministratore)..."
UDEV_RULE='KERNEL=="ttyUSB*", MODE="0666"\nKERNEL=="ttyACM*", MODE="0666"'
echo -e "$UDEV_RULE" | sudo tee /etc/udev/rules.d/99-nanovna-sensor.rules > /dev/null
sudo udevadm control --reload-rules
sudo udevadm trigger

# Creazione scorciatoia desktop/menu (Opzionale ma molto comodo)
echo "[4/4] Creazione dell'icona nel menu applicazioni..."
APP_DIR=$(pwd)
DESKTOP_FILE="$HOME/.local/share/applications/nanovna-sensor.desktop"

cat <<EOF > "$DESKTOP_FILE"
[Desktop Entry]
Name=HaptyGraph
Exec=$APP_DIR/venv/bin/python $APP_DIR/main.py
Terminal=true
Type=Application
Categories=Utility;Engineering;
EOF

chmod +x "$DESKTOP_FILE"

echo "========================================"
echo " Installazione Completata con successo! "
echo " Puoi lanciare il programma dal menu applicazioni o eseguendo venv/bin/python main.py"
echo "========================================"