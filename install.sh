#!/bin/bash

echo "==========================================="
echo " Installazione di HaptyHub "
echo "==========================================="


# ==========================================
# CONTROLLO DIPENDENZE DI SISTEMA
# ==========================================
echo "Controllo delle dipendenze di sistema..."

# Controllo Node.js (necessario per ELK)
if ! command -v node &> /dev/null; then
    echo "Node.js non trovato. Installazione in corso..."
    sudo apt-get update
    sudo apt-get install -y nodejs npm
else
    echo "✔️ Node.js è già installato."
fi

# Controllo OpenSCAD (necessario per la generazione 3D)
if ! command -v openscad &> /dev/null; then
    echo "OpenSCAD non trovato. Installazione in corso..."
    sudo apt-get update
    sudo apt-get install -y openscad
else
    echo "✔️ OpenSCAD è già installato."
fi
# ==========================================

# 1. Creazione dell'ambiente virtuale Python
echo "[1/5] Creazione dell'ambiente virtuale (venv)..."
python3 -m venv venv

# 2. Installazione delle dipendenze
echo "[2/5] Installazione delle librerie Python..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
deactivate

echo "[2.5/5] Installazione delle dipendenze Node.js..."
# Controlliamo se esiste già un package.json (buona pratica)
if [ -f "package.json" ]; then
    echo "  -> package.json trovato. Installazione librerie..."
    npm install
else
    echo "  -> package.json non trovato. Inizializzazione e installazione di elkjs..."
    npm init -y > /dev/null
    npm install elkjs
fi

# 3. Configurazione permessi Hardware (Regole udev)
echo "[3/5] Configurazione dei permessi USB (richiede password amministratore)..."
UDEV_RULE='KERNEL=="ttyUSB*", MODE="0666"\nKERNEL=="ttyACM*", MODE="0666"'
echo -e "$UDEV_RULE" | sudo tee /etc/udev/rules.d/99-nanovna-sensor.rules > /dev/null
sudo udevadm control --reload-rules
sudo udevadm trigger

# 4. Creazione scorciatoia desktop/menu
echo "[4/5] Creazione dell'icona nel menu applicazioni..."
APP_DIR=$(pwd)
DESKTOP_FILE="$HOME/.local/share/applications/HaptyGraph.desktop"
# percorso dell'icona basato sulla cartella attuale
ICON_PATH="$APP_DIR/assets/icon.svg"

cat <<EOF > "$DESKTOP_FILE"
[Desktop Entry]
Name=HaptyGraph
Exec=$APP_DIR/venv/bin/python $APP_DIR/main.py
Icon=$ICON_PATH
Terminal=false
Type=Application
Categories=Utility;Engineering;Application;
EOF

chmod +x "$DESKTOP_FILE"

# Creazione file eseguibile per terminale
cat <<EOF > "HaptyHub.sh"
#!/bin/bash
source venv/bin/activate
python main.py
deactivate
EOF
chmod +x "HaptyHub.sh"

# 5. Creazione file delle Variabili d'Ambiente (.env)
echo "[5/5] Creazione del file di configurazione (.env)..."
if [ ! -f ".env" ]; then
    echo "OPENAI_API_KEY=" > .env
    echo "GEMINI_API_KEY=" >> .env
    echo "  -> File .env creato con successo."
else
    echo "  -> File .env già esistente, chiavi API preservate."
fi

echo "========================================"
echo " Installazione Completata con successo! "
echo " IMPORTANTE: Apri il file .env e inserisci le tue chiavi API prima di avviare il programma."
echo "========================================"
