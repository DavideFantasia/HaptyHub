#!/bin/bash

echo "==========================================="
echo " Disinstallazione di HaptyGraph "
echo "==========================================="

# 1. Rimozione dell'Ambiente Virtuale
echo "[1/3] Rimozione dell'ambiente virtuale (venv)..."
if [ -d "venv" ]; then
    rm -rf venv
    echo "  -> Cartella venv rimossa."
else
    echo "  -> Cartella venv non trovata, salto."
fi

echo "[1.5/3] Rimozione modulo ELK"
if [ -d "node_modules" ]; then
	npm unistall elkjs
	rm -r -f node_modules
	rm *.json
	echo " -> Modulo Rimosso"
else
	echo " -> Cartella non Rimossa"
fi

# 2. Rimozione delle Regole udev
echo "[2/3] Rimozione delle regole hardware (richiede password amministratore)..."
if [ -f "/etc/udev/rules.d/99-nanovna-sensor.rules" ]; then
    sudo rm /etc/udev/rules.d/99-nanovna-sensor.rules
    sudo udevadm control --reload-rules
    sudo udevadm trigger
    echo "  -> Regole udev rimosse dal sistema."
else
    echo "  -> Regole udev non trovate, salto."
fi

# 3. Rimozione della Scorciatoia (Icona)
echo "[3/3] Rimozione dell'icona dal menu applicazioni..."
DESKTOP_FILE="$HOME/.local/share/applications/HaptyGraph.desktop"
if [ -f "$DESKTOP_FILE" ]; then
    rm "$DESKTOP_FILE"
    echo "  -> Icona rimossa con successo."
else
    echo "  -> Icona non trovata, salto."
fi

echo "==========================================="
echo " Pulizia Completata con successo! "
echo " Ora puoi eliminare in sicurezza l'intera cartella del progetto."
echo "==========================================="
