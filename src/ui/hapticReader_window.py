import math
import numpy as np

from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QMessageBox, QFileDialog)
from PyQt6.QtGui import QAction
from PyQt6.QtCore import QTimer, Qt, QThread, pyqtSignal
import pyqtgraph as pg
import time

from src.utils.sensor_reader import NVAReader
from src.models.graph_models import HapticGraph
from src.utils.sensor_worker import SensorWorker
from src.utils.tts_worker import TTSWorker

class HapticReaderWindow(QMainWindow):
    def __init__(self, sensor= NVAReader()):
        super().__init__()
        self.setWindowTitle("Lettura Grafo Haptico Live")
        self.resize(1000, 600)
        
        self.sensor = sensor
        self.graph = None # Qui caricheremo il file JSON
        
        # Variabili di stato per la lettura
        self.baseline_frames = []
        self.baseline_data = None
        self.threshold = 0.1 # Mantieni la stessa soglia usata in calibrazione
        self.is_baseline_ready = False

        # --- GESTIONE TEXT TO SPEECH ---
        self.tts_worker = TTSWorker()
        self.tts_worker.start()
        self.ultimo_nodo_letto = None # per evitare stuttering

        self._setup_ui()
        self._init_menu_bar()

        # Crea e avvia il Worker in background
        self.worker = SensorWorker(self.sensor)
        # Collega il "campanello" del worker alla funzione di aggiornamento
        self.worker.data_ready.connect(self.process_sensor_data)
        self.worker.start()

    def _init_menu_bar(self):
        """Crea la barra dei menu per l'importazione del file JSON."""
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu("&File")
        
        act_importa = QAction("Importa Grafo (JSON)", self)
        act_importa.triggered.connect(self.importa_json)
        file_menu.addAction(act_importa)

    def _setup_ui(self):
        self.main_widget = QWidget()
        self.setCentralWidget(self.main_widget)
        self.layout = QHBoxLayout(self.main_widget)

        # --- SINISTRA: Grafico Real-Time ---
        self.plot_widget = pg.PlotWidget(title="Dati Sensore LIVE")
        self.plot_widget.setYRange(0, 80)
        self.plot_widget.setXRange(0, 100)
        self.plot_widget.showGrid(x=True, y=True, alpha=0.3)
        self.plot_curve = self.plot_widget.plot(pen=pg.mkPen('c', width=2)) # Ciano per la lettura
        self.layout.addWidget(self.plot_widget, stretch=2)

        # --- DESTRA: Feedback Visivo/Testuale ---
        self.info_layout = QVBoxLayout()
        
        self.lbl_stato = QLabel("Importa un file JSON per iniziare.")
        self.lbl_stato.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_stato.setStyleSheet("font-size: 20px; font-weight: bold; color: orange;")
        self.info_layout.addWidget(self.lbl_stato)

        self.lbl_nodo_rilevato = QLabel("In attesa...")
        self.lbl_nodo_rilevato.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_nodo_rilevato.setStyleSheet("font-size: 32px; font-weight: bold; color: #555;")
        self.info_layout.addWidget(self.lbl_nodo_rilevato)

        self.lbl_descrizione = QLabel("")
        self.lbl_descrizione.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_descrizione.setStyleSheet("font-size: 18px;")
        self.info_layout.addWidget(self.lbl_descrizione)

        self.info_layout.addStretch()
        self.layout.addLayout(self.info_layout, stretch=1)

    def importa_json(self):
        """Apre il File Dialog per caricare il grafo."""
        from PyQt6.QtWidgets import QFileDialog, QMessageBox
        from src.models.graph_models import HapticGraph

        # 1. Metti in pausa il thread per non aggiornare la UI mentre navighi le cartelle
        if hasattr(self, 'worker'):
            self.worker.is_paused = True

        filepath, _ = QFileDialog.getOpenFileName(
            self, "Importa Grafo Haptico", "", "JSON Files (*.json)"
        )

        if filepath:
            try:
                # Carichiamo il grafo
                self.graph = HapticGraph.from_json(filepath)
                
                if len(self.graph.nodes) > 0:
                    # Ricalcoliamo la linea di base per le condizioni attuali
                    self.baseline_frames = []
                    self.is_baseline_ready = False
                    self.lbl_stato.setText(f"Grafo caricato ({len(self.graph.nodes)} nodi).\nAcquisizione linea di base...")
                    self.lbl_stato.setStyleSheet("font-size: 20px; font-weight: bold; color: orange;")
                else:
                    QMessageBox.warning(self, "Attenzione", "Il file JSON è vuoto.")
            except Exception as e:
                QMessageBox.critical(self, "Errore", f"Impossibile leggere il file:\n{e}")
        
        # 2. Togli la pausa al thread! (Sia che abbia caricato, sia che abbia premuto Annulla)
        if hasattr(self, 'worker'):
            self.worker.is_paused = False

    def process_sensor_data(self, dati_raw):
        """Ciclo di aggiornamento dati e logica di Machine Learning."""
        """Metodo richiamato automaticamente ogni volta che il Worker emette 'data_ready'."""
        # Non serve più fare 'dati_raw = self.sensor.read_data()' perché ci arrivano come parametro
        k = 50
        mags = np.array([k*((1-re**2-im**2)/(1-re)**2+im**2) for re, im in dati_raw])
        
        # Controllo di sicurezza
        if len(mags) != 101: 
            return
            
        self.plot_curve.setData(mags)

        if not self.graph or len(self.graph.nodes) == 0:
            return

        # --- 1. Calcolo Baseline ---
        if not self.is_baseline_ready:
            self.baseline_frames.append(mags)
            if len(self.baseline_frames) >= 5:
                self.baseline_data = np.mean(self.baseline_frames, axis=0)
                self.is_baseline_ready = True
                self.__update_threshold() # Aggiorna la soglia in base al rumore di fondo
                self.lbl_stato.setText("PRONTO.\nTocca un nodo.")
                self.lbl_stato.setStyleSheet("font-size: 20px; font-weight: bold; color: green;")
            
            return

        # --- 2. Rilevamento Tocco ---
        diff = np.abs(mags - self.baseline_data)
        
        # 2.1. Troviamo dove si trova il picco più alto in QUESTO istante
        live_peak_index = int(np.argmax(diff))
        live_peak_mag = diff[live_peak_index]

        # 2.2. Controlliamo se supera la soglia minima di tocco
        if live_peak_mag > self.threshold:
            
            best_node = None
            min_distance = float('inf')
            
            # Finestra di tolleranza (es. +/- 3 punti nell'array da 101)
            # Se la NanoVNA scansiona 900MHz su 101 punti, 1 punto sono circa 9MHz.
            TOLERANCE = 0 

            for nodo in self.graph.nodes:
                saved_index = nodo.fingerprint["index"]
                
                # Calcoliamo la distanza "orizzontale" (sull'asse X delle frequenze)
                distanza = abs(live_peak_index - saved_index)
                
                # Se il picco rientra nella finestra di questo nodo
                # e ed è il più vicino in assoluto
                if distanza <= TOLERANCE and distanza < min_distance:
                    min_distance = distanza
                    best_node = nodo

            # Aggiorna l'interfaccia con il vincitore
            if best_node:
                self.lbl_nodo_rilevato.setText(best_node.id)
                self.lbl_nodo_rilevato.setStyleSheet("font-size: 32px; font-weight: bold; color: #2196F3;")
                self.lbl_descrizione.setText(best_node.description)

                # --- LOGICA TEXT-TO-SPEECH ---
                # Parla solo se il nodo è diverso da quello che stiamo già tenendo premuto
                if best_node.id != self.ultimo_nodo_letto:
                    self.ultimo_nodo_letto = best_node.id
                    self.tts_worker.parla(best_node.description)
        else:
            # Sotto la soglia, il dito è stato rimosso
            self.lbl_nodo_rilevato.setText("Nessun tocco")
            self.lbl_nodo_rilevato.setStyleSheet("font-size: 32px; font-weight: bold; color: #555;")
            self.lbl_descrizione.setText("")

            # --- LOGICA TEXT-TO-SPEECH ---
            # Resettiamo la memoria quando alziamo il dito.
            # Così, se ritocchiamo lo STESSO nodo, lo rileggerà.
            self.ultimo_nodo_letto = None

    def __update_threshold(self):
        """Aggiorna la soglia di rilevamento tocco."""
        max_rumore_fondo = 0.0
        
        for frame in self.baseline_frames:
            # Calcoliamo la differenza assoluta di questo frame dalla media
            diff = np.abs(np.array(frame) - self.baseline_data)
            picco_rumore = np.max(diff)
            
            if picco_rumore > max_rumore_fondo:
                max_rumore_fondo = picco_rumore
        
        moltiplicatore_sicurezza = 15.5 # Più è alto, più devi premere forte il dito
        
        self.threshold = max(max_rumore_fondo * moltiplicatore_sicurezza, 0.05)

    def closeEvent(self, event):
        """Gestione pulita della chiusura della finestra e del thread."""
        # Ferma il thread in modo sicuro
        if hasattr(self, 'worker') and self.worker.isRunning():
            self.worker.stop()
            
        # Ferma la voce
        if hasattr(self, 'tts_worker') and self.tts_worker.isRunning():
            self.tts_worker.stop()

        self.deleteLater()
        event.accept()