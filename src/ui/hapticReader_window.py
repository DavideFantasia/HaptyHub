import numpy as np

from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QMessageBox, QFileDialog)
from PyQt6.QtGui import QAction
from PyQt6.QtCore import Qt
import pyqtgraph as pg

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
        self.graph = None 
        
        # Variabili di stato
        self.baseline_frames = []
        self.baseline_data = None
        self.is_baseline_ready = False

        # --- GESTIONE TEXT TO SPEECH ---
        self.tts_worker = TTSWorker()
        self.tts_worker.start()
        self.ultimo_nodo_letto = None 
        
        # --- DEBOUNCING ---
        self.no_touch_frames = 0 # Contatore per evitare "rimbalzi" quando togli il dito
        self._setup_ui()
        self._init_menu_bar()

        self.worker = SensorWorker(self.sensor)
        self.worker.data_ready.connect(self.process_sensor_data)
        self.worker.start()

    def _init_menu_bar(self):
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
        self.plot_curve = self.plot_widget.plot(pen=pg.mkPen('c', width=2))
        
        # Aggiungiamo anche la baseline al grafico (tratteggiata) per debug visivo
        self.plot_baseline = self.plot_widget.plot(pen=pg.mkPen('y', style=Qt.PenStyle.DashLine))
        
        self.layout.addWidget(self.plot_widget, stretch=2)

        # --- DESTRA: Feedback ---
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
        if hasattr(self, 'worker'):
            self.worker.is_paused = True

        filepath, _ = QFileDialog.getOpenFileName(
            self, "Importa Grafo Haptico", "", "JSON Files (*.json)"
        )

        if filepath:
            try:
                self.graph = HapticGraph.from_json(filepath)
                if len(self.graph.nodes) > 0:
                    self.baseline_frames = []
                    self.is_baseline_ready = False
                    self.lbl_stato.setText(f"Grafo caricato ({len(self.graph.nodes)} nodi).\nAcquisizione linea di base...")
                    self.lbl_stato.setStyleSheet("font-size: 20px; font-weight: bold; color: orange;")
                else:
                    QMessageBox.warning(self, "Attenzione", "Il file JSON è vuoto.")
            except Exception as e:
                QMessageBox.critical(self, "Errore", f"Impossibile leggere il file:\n{e}")
        
        if hasattr(self, 'worker'):
            self.worker.is_paused = False

    def process_sensor_data(self, dati_raw):
        k = 50
        mags = np.array([k*((1-re**2-im**2)/(1-re)**2+im**2) for re, im in dati_raw])
        
        if len(mags) != 101: 
            return
            
        # NORMALIZZAZIONE MATEMATICA
        pavimento_attuale = np.min(mags)
        mags_ancorati = mags - pavimento_attuale
        mags = mags_ancorati

        self.plot_curve.setData(mags)

        if not self.graph or len(self.graph.nodes) == 0:
            return

        # --- 1. Calcolo Baseline Statica ---
        if not self.is_baseline_ready:
            self.baseline_frames.append(mags)
            if len(self.baseline_frames) >= 15: # Usiamo 15 frame (circa 1.5s) per maggiore stabilità
                self.baseline_data = np.mean(self.baseline_frames, axis=0)
                self.plot_baseline.setData(self.baseline_data) # Mostriamo la baseline
                self.is_baseline_ready = True
                
                # Niente più threshold calcolato. Usiamo la variazione relativa percentuale.
                self.lbl_stato.setText("PRONTO.\nTocca un nodo.")
                self.lbl_stato.setStyleSheet("font-size: 20px; font-weight: bold; color: green;")
            return

        # =======================================================
        # 2. PREDICTION: WINDOWING & RELATIVE DIFFERENCE
        # =======================================================
        
        WINDOW_SIZE = 2 
        MIN_RELATIVE_CHANGE = 0.20 # Aumentato al 20% per ignorare shift lievi
        
        best_node = None
        max_rel_diff = 0.0

        for nodo in self.graph.nodes:
            # Controllo di sicurezza: verifichiamo che il json sia formattato correttamente
            if "peak_index" not in nodo.fingerprint:
                continue
                
            idx = nodo.fingerprint["peak_index"]
            
            start = max(0, idx - WINDOW_SIZE)
            end = min(len(mags), idx + WINDOW_SIZE + 1)
            
            live_window = mags[start:end]
            base_window = self.baseline_data[start:end]
            
            local_floor = np.min(base_window)
            
            # "Sgonfiamo" la finestra rimuovendo il piedistallo
            # Usiamo np.maximum(..., 0.001) per evitare aree nulle o negative causate dal rumore
            base_window_ancorata = np.maximum(base_window - local_floor, 0.001)
            live_window_ancorata = np.maximum(live_window - local_floor, 0.001)
            
            # Area della sola "gobba" a riposo
            base_area = np.sum(base_window_ancorata)
            
            if base_area > 0.01:
                diff_area = np.sum(np.abs(live_window_ancorata - base_window_ancorata))
                rel_diff = diff_area / base_area
            else:
                rel_diff = 0
                
            if rel_diff > max_rel_diff:
                max_rel_diff = rel_diff
                best_node = nodo

        # =======================================================
        # 3. AGGIORNAMENTO UI & TTS
        # =======================================================
        
        if max_rel_diff > MIN_RELATIVE_CHANGE and best_node is not None:
            self.no_touch_frames = 0 # Resetta il contatore
            
            self.lbl_nodo_rilevato.setText(best_node.id)
            self.lbl_nodo_rilevato.setStyleSheet("font-size: 32px; font-weight: bold; color: #2196F3;")
            self.lbl_descrizione.setText(f"{best_node.description}\n(Confidenza: {max_rel_diff*100:.0f}%)")

            if best_node.id != self.ultimo_nodo_letto:
                self.ultimo_nodo_letto = best_node.id
                self.tts_worker.parla(best_node.description)
                
        else:
            # Attendiamo 3 frame senza tocco prima di dichiarare la fine (Debouncing)
            self.no_touch_frames += 1
            
            if self.no_touch_frames >= 3:
                self.lbl_nodo_rilevato.setText("Nessun tocco")
                self.lbl_nodo_rilevato.setStyleSheet("font-size: 32px; font-weight: bold; color: #555;")
                self.lbl_descrizione.setText("")
                self.ultimo_nodo_letto = None

    def closeEvent(self, event):
        if hasattr(self, 'worker') and self.worker.isRunning():
            self.worker.stop()
            
        if hasattr(self, 'tts_worker') and self.tts_worker.isRunning():
            self.tts_worker.stop()

        self.deleteLater()
        event.accept()