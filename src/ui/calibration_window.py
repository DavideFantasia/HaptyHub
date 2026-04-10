from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QLabel, QLineEdit, QFormLayout, QMessageBox)
from PyQt6.QtCore import QTimer, Qt
import pyqtgraph as pg

import math
import numpy as np

from src.models.graph_models import Node #classe per la rappresentazione dei nodi
from src.models.graph_models import HapticGraph #classe per la rappresentazione del grafo

from src.utils.sensor_reader import NVAReader #classe per la lettura dei dati dalla scheda
from src.utils.sensor_worker import SensorWorker #classe per la gestione del thread di lettura dei dati dal sensore

class CalibrationWindow(QMainWindow):
    # Definizione degli Stati
    STATE_BASELINE = 0
    STATE_WAIT_TOUCH = 1
    STATE_RECORDING_PEAK = 2
    STATE_FORM_ENTRY = 3


    def __init__(self, sensor= NVAReader()):
        super().__init__()
        self.setWindowTitle("Procedura Associazione Nodi")
        
        self.resize(1000, 600)
        
        self.sensor = sensor
        self.haptic_graph = HapticGraph()
        
        # Variabili per la Macchina a Stati e Signal Processing
        self.current_state = self.STATE_BASELINE
        self.baseline_data = None
        self.baseline_frames = [] # Buffer per calcolare la media iniziale
        self.threshold = 0.1 # SOGLIA: Modifica questo valore in base al rumore del tuo sensore
        
        self.touch_buffer = []      # Raccoglie i picchi durante il tocco
        self.final_fingerprint = [] # La "impronta digitale" finale da salvare nel nodo

        self._setup_ui()

        self.worker = SensorWorker(self.sensor)
        self.worker.data_ready.connect(self.process_sensor_data)
        self.worker.start()

    def _setup_ui(self):
        self.main_widget = QWidget()
        self.setCentralWidget(self.main_widget)
        self.layout = QHBoxLayout(self.main_widget)

        # --- SINISTRA: Grafico Real-Time (PyQtGraph) ---
        self.plot_widget = pg.PlotWidget(title="Dati Sensore (Magnitudo Lin)")
        self.plot_widget.setYRange(0, 1) # Assumiamo magnitudo tra 0 e 1
        self.plot_widget.showGrid(x=True, y=True, alpha=0.3)
        self.plot_curve = self.plot_widget.plot(pen=pg.mkPen('y', width=2)) # Linea gialla
        
        # Linea orizzontale rossa per mostrare la soglia (invisibile all'inizio)
        self.thresh_line = pg.InfiniteLine(angle=0, pen=pg.mkPen('r', style=Qt.PenStyle.DashLine))
        self.plot_widget.addItem(self.thresh_line)
        self.thresh_line.setVisible(False)

        self.layout.addWidget(self.plot_widget, stretch=2)

        # --- DESTRA: Procedura Guidata (Wizard) ---
        self.wizard_layout = QVBoxLayout()
        
        self.lbl_stato = QLabel("STATO: Calibrazione Iniziale")
        self.lbl_stato.setStyleSheet("color: orange; font-weight: bold;")
        self.wizard_layout.addWidget(self.lbl_stato)

        self.lbl_istruzioni = QLabel("Non toccare il sensore...\nAcquisizione linea di base in corso.")
        self.lbl_istruzioni.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_istruzioni.setStyleSheet("font-size: 16px; font-weight: bold; margin: 20px 0;")
        self.wizard_layout.addWidget(self.lbl_istruzioni)

        # Form per i dati del nodo
        self.form_layout = QFormLayout()
        self.entry_node_id = QLineEdit()
        self.entry_desc = QLineEdit()
        self.entry_node_id.setEnabled(False)
        self.entry_desc.setEnabled(False)
        self.form_layout.addRow("ID Nodo:", self.entry_node_id)
        self.form_layout.addRow("Descrizione:", self.entry_desc)
        self.wizard_layout.addLayout(self.form_layout)

        self.btn_salva = QPushButton("Salva Nodo e Continua")
        self.btn_salva.setEnabled(False)
        self.btn_salva.clicked.connect(self.salva_nodo_corrente)
        self.wizard_layout.addWidget(self.btn_salva)
        
        self.wizard_layout.addStretch() # Spinge tutto verso l'alto
        self.layout.addLayout(self.wizard_layout, stretch=1)

        self.btn_termina = QPushButton("Termina ed Esporta")
        #self.btn_termina.setEnabled(False)
        self.btn_termina.clicked.connect(self.termina_e_salva)
        self.wizard_layout.addWidget(self.btn_termina)

    def termina_e_salva(self):
        from PyQt6.QtWidgets import QFileDialog, QMessageBox
        
        if len(self.haptic_graph.nodes) == 0:
            QMessageBox.warning(self, "Attenzione", "Nessun nodo calibrato da salvare.")
            return
        
        # Mette in pausa il thread
        if hasattr(self, 'worker'):
            self.worker.is_paused = True

        filepath, _ = QFileDialog.getSaveFileName(
            self, "Salva Grafo Haptico", "grafo_sensore.json", "JSON Files (*.json)"
        )
        
        if filepath:
            self.haptic_graph.to_json(filepath)
            QMessageBox.information(self, "Successo", f"Grafo salvato in:\n{filepath}")
            self.close() 
        else:
            # L'utente ha annullato, togliamo la pausa
            if hasattr(self, 'worker'):
                self.worker.is_paused = False

    def process_sensor_data(self,dati_raw):
        """Metodo chiamato dal QTimer ogni 100ms. È il 'cervello' della macchina a stati."""
        # Se siamo in fase di inserimento dati, non aggiorniamo il grafico per "congelarlo" sul picco
        if self.current_state == self.STATE_FORM_ENTRY:
            return

        mags = np.array([math.sqrt(re**2 + im**2) for re, im in dati_raw])
        
        # Controllo di sicurezza
        if len(mags) != 101: 
            return
            
        # 2. MACCHINA A STATI
        if self.current_state == self.STATE_BASELINE:
            self._handle_state_baseline(mags)
            self.plot_curve.setData(mags)

        elif self.current_state in [self.STATE_WAIT_TOUCH, self.STATE_RECORDING_PEAK]:
            diff = np.abs(mags - self.baseline_data)
            max_diff = np.max(diff)
            
            self.plot_curve.setData(mags) 

            if self.current_state == self.STATE_WAIT_TOUCH:
                if max_diff > self.threshold:
                    self.touch_buffer = [mags]
                    self._cambia_stato(self.STATE_RECORDING_PEAK)
            
            elif self.current_state == self.STATE_RECORDING_PEAK:
                if max_diff > self.threshold:
                    self.touch_buffer.append(mags)
                else:
                    if len(self.touch_buffer) > 0:
                        curva_media = np.mean(self.touch_buffer, axis=0)
                        self.final_fingerprint = curva_media.tolist()
                    
                    self._cambia_stato(self.STATE_FORM_ENTRY)
                    
    def _handle_state_baseline(self, mags):
        """Raccoglie i primi frame per stabilire lo 'zero' del sensore."""
        
        self.baseline_frames.append(mags)
        if len(self.baseline_frames) >= 10: # Dopo ~2 secondi (10 frame x 200ms)
            # Calcola la media lungo l'asse 0 (media di ogni singolo punto della scansione)
            self.baseline_data = np.mean(self.baseline_frames, axis=0)
            
            # Imposta la linea rossa della soglia sul grafico per aiuto visivo
            self.thresh_line.setPos(self.threshold)
            self.thresh_line.setVisible(True)
            self.plot_widget.setYRange(0, self.threshold * 5) # Adatta lo zoom
            
            self._cambia_stato(self.STATE_WAIT_TOUCH)

    def _cambia_stato(self, nuovo_stato):
        """Gestisce le transizioni visive della UI in base allo stato."""
        self.current_state = nuovo_stato

        if nuovo_stato == self.STATE_WAIT_TOUCH:
            self.lbl_stato.setText("STATO: Attesa Tocco")
            self.lbl_stato.setStyleSheet("color: green; font-weight: bold;")
            self.lbl_istruzioni.setText(f"Tocca il NODO {len(self.haptic_graph.nodes) + 1}\ne tieni premuto.")
            self.entry_node_id.setEnabled(False)
            self.entry_desc.setEnabled(False)
            self.btn_salva.setEnabled(False)

        elif nuovo_stato == self.STATE_RECORDING_PEAK:
            self.lbl_stato.setText("STATO: Acquisizione in corso...")
            self.lbl_stato.setStyleSheet("color: red; font-weight: bold;")
            self.lbl_istruzioni.setText("Picco Rilevato!\nRilascia il nodo ora.")

        elif nuovo_stato == self.STATE_FORM_ENTRY:
            self.lbl_stato.setText("STATO: Compilazione Dati")
            self.lbl_stato.setStyleSheet("color: blue; font-weight: bold;")
            self.lbl_istruzioni.setText("Impronta digitale (Fingerprint) acquisita con successo!\nCompila i dati e salva.")
            
            # Abilita il form
            self.entry_node_id.setEnabled(True)
            self.entry_desc.setEnabled(True)
            self.btn_salva.setEnabled(True)
            
            # Pre-compila l'ID in automatico
            self.entry_node_id.setText(f"Nodo_{len(self.haptic_graph.nodes) + 1}")
            self.entry_desc.setFocus() # Mette il cursore sulla descrizione

    def salva_nodo_corrente(self):
        """Triggerato dal click su 'Salva Nodo e Continua'."""
        node_id = self.entry_node_id.text().strip()
        desc = self.entry_desc.text().strip()

        if not node_id or not desc:
            QMessageBox.warning(self, "Attenzione", "Compila entrambi i campi prima di salvare.")
            return

        # Crea l'oggetto Node e lo salva in memoria

        nuovo_nodo = Node(
            id=node_id, 
            description=desc, 
            fingerprint=self.final_fingerprint
        )
        self.haptic_graph.add_node(nuovo_nodo)
        
        print(f"Salvato: {nuovo_nodo.id} - Fingerprint di {len(nuovo_nodo.fingerprint)} punti acquisito.")

        # Pulisci il form e riavvia il ciclo!
        self.entry_node_id.clear()
        self.entry_desc.clear()
        self._cambia_stato(self.STATE_WAIT_TOUCH)

    def closeEvent(self, event):
        """Chiude il thread in modo sicuro."""
        if hasattr(self, 'worker') and self.worker.isRunning():
            self.worker.stop()
            
        self.deleteLater()
        event.accept()