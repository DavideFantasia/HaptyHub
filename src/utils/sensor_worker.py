from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QMessageBox, QFileDialog)
from PyQt6.QtGui import QAction
from PyQt6.QtCore import QTimer, Qt, QThread, pyqtSignal
import pyqtgraph as pg
import time

from src.utils.sensor_reader import NVAReader
from src.models.graph_models import HapticGraph

class SensorWorker(QThread):
    # Segnali per comunicare con l'interfaccia grafica
    data_ready = pyqtSignal(list)
    error_occurred = pyqtSignal(str)

    def __init__(self, sensor):
        super().__init__()
        self.sensor = sensor
        self.sensor.connect()
        self.is_running = True
        self.is_paused = False

    def run(self):
        """Questo ciclo gira in background e non blocca mai l'interfaccia."""
        while self.is_running:
            if not self.is_paused:
                try:
                    # Legge i dati. Se la scheda ci mette 200ms, solo questo thread si ferma.
                    dati = self.sensor.read_data()
                    
                    # Se abbiamo ricevuto qualcosa, invia i dati alla finestra principale
                    if dati:
                        self.data_ready.emit(dati)
                    
                    # Un microscopico respiro per non occupare il 100% della CPU
                    time.sleep(0.01) 
                    
                except Exception as e:
                    self.error_occurred.emit(str(e))
                    break

    def stop(self):
        """Ferma il ciclo in modo pulito alla chiusura del programma."""
        self.is_running = False
        self.wait() # Attende che il ciclo while finisca l'ultima iterazione
        self.sensor.disconnect() # Assicuriamoci di chiudere la connessione al sensore