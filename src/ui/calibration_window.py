from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QLabel, QLineEdit, QFormLayout, QMessageBox)
from PyQt6.QtCore import Qt
import pyqtgraph as pg

import numpy as np
from scipy.signal import find_peaks

from src.models.graph_models import Node
from src.models.graph_models import HapticGraph
from src.utils.sensor_reader import NVAReader
from src.utils.sensor_worker import SensorWorker

class CalibrationWindow(QMainWindow):
    # Definizione degli Stati Semplificata (Solo 2 stati reali)
    STATE_ACQUIRING = 0
    STATE_FORM_ENTRY = 1

    def __init__(self, sensor= NVAReader()):
        super().__init__()
        self.setWindowTitle("Associazione Nodi")
        self.resize(1000, 600)
        
        self.sensor = sensor
        self.haptic_graph = HapticGraph()
        
        self.current_state = self.STATE_ACQUIRING
        self.baseline_frames = [] 
        self.baseline_data = None
        
        self.nodi_rilevati = []
        self.nodo_corrente_index = 0

        self._setup_ui()

        self.worker = SensorWorker(self.sensor)
        self.worker.data_ready.connect(self.process_sensor_data)
        self.worker.start()

    def _setup_ui(self):
        self.main_widget = QWidget()
        self.setCentralWidget(self.main_widget)
        self.layout = QHBoxLayout(self.main_widget)

        # --- Grafico Real-Time ---
        self.plot_widget = pg.PlotWidget(title="Dati Sensore (Live vs Baseline)")
        self.plot_widget.setYRange(0, 80)
        self.plot_widget.setXRange(0, 100)
        self.plot_widget.showGrid(x=True, y=True, alpha=0.3)
        
        # Curva LIVE (Gialla, in continuo movimento)
        self.plot_curve_live = self.plot_widget.plot(pen=pg.mkPen('y', width=2))
        
        # Curva BASELINE (Ciano, appare quando SciPy trova i nodi)
        self.plot_curve_baseline = self.plot_widget.plot(pen=pg.mkPen('c', width=2, style=Qt.PenStyle.DashLine))

        self.layout.addWidget(self.plot_widget, stretch=2)

        # --- Procedura Guidata ---
        self.wizard_layout = QVBoxLayout()
        
        self.lbl_stato = QLabel("STATO: Acquisizione Linea di Base")
        self.lbl_stato.setStyleSheet("color: orange; font-weight: bold; font-size: 18px;")
        self.wizard_layout.addWidget(self.lbl_stato)

        self.lbl_istruzioni = QLabel("Non toccare il sensore...\nScansione del circuito in corso.")
        self.lbl_istruzioni.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_istruzioni.setStyleSheet("font-size: 16px; margin: 20px 0;")
        self.wizard_layout.addWidget(self.lbl_istruzioni)

        # Form per i dati
        self.form_layout = QFormLayout()
        self.entry_node_id = QLineEdit()
        self.entry_desc = QLineEdit()
        self.entry_node_id.setEnabled(False)
        self.entry_desc.setEnabled(False)
        self.form_layout.addRow("ID Nodo:", self.entry_node_id)
        self.form_layout.addRow("Descrizione Vocale:", self.entry_desc)
        self.wizard_layout.addLayout(self.form_layout)

        # Bottone Verde "Salva"
        self.btn_salva = QPushButton("Associa Nodo")
        self.btn_salva.setEnabled(False)
        self.btn_salva.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 8px;")
        self.btn_salva.clicked.connect(self.salva_nodo_corrente)
        self.wizard_layout.addWidget(self.btn_salva)
        
        self.wizard_layout.addStretch() 
        self.layout.addLayout(self.wizard_layout, stretch=1)

        self.btn_termina = QPushButton("Termina ed Esporta JSON")
        self.btn_termina.clicked.connect(self.termina_e_salva)
        self.wizard_layout.addWidget(self.btn_termina)

    def process_sensor_data(self, dati_raw):
        """Metodo chiamato a ripetizione per streammare l'onda."""
        k = 50
        mags = np.array([k*((1-re**2-im**2)/(1-re)**2+im**2) for re, im in dati_raw])
        
        if len(mags) != 101: 
            return
            
        # ==========================================
        # NORMALIZZAZIONE MATEMATICA
        # ==========================================
        pavimento_attuale = np.min(mags)
        mags_ancorati = mags - pavimento_attuale
        mags = mags_ancorati
        # ==========================================

        # CONTINUIAMO AD AGGIORNARE IL GRAFICO SEMPRE E COMUNQUE!
        self.plot_curve_live.setData(mags)

        # Logica di Acquisizione Iniziale
        if self.current_state == self.STATE_ACQUIRING:
            self.baseline_frames.append(mags)
            
            if len(self.baseline_frames) >= 15: # 1.5 secondi di ascolto
                self.baseline_data = np.mean(self.baseline_frames, axis=0)
                
                # Fissiamo la linea ciano tratteggiata per far vedere la baseline "congelata"
                self.plot_curve_baseline.setData(self.baseline_data)
                
                # Cerchiamo i picchi sulla media congelata
                self.esegui_scipy_discovery()
                

    def esegui_scipy_discovery(self):
        """Usa SciPy per trovare i nodi fisici e prepara l'interfaccia utente."""
        
        picchi_trovati, _ = find_peaks(self.baseline_data, prominence=0.5, distance=3)
        self.nodi_rilevati = picchi_trovati.tolist()
        
        # Disegnamo i pallini rossi sui picchi trovati
        if hasattr(self, 'scatter_peaks'):
            self.plot_widget.removeItem(self.scatter_peaks)
            
        valori_picchi = [self.baseline_data[i] for i in self.nodi_rilevati]
        
        # Creiamo lo ScatterPlot e lo rendiamo interattivo
        self.scatter_peaks = pg.ScatterPlotItem(
            x=self.nodi_rilevati, 
            y=valori_picchi, 
            pen=None, 
            symbol='o', 
            brush='r', 
            size=14,  # Leggermente più grandi per essere facili da cliccare
            hoverable=True, # Diventano luminosi quando ci passi sopra col mouse
            hoverSymbol='o',
            hoverSize=18,
            hoverPen=pg.mkPen('w', width=2),
            hoverBrush='g'
        )
        
        # Colleghiamo l'evento click alla nostra funzione
        self.scatter_peaks.sigClicked.connect(self.on_scatter_clicked)
        
        self.plot_widget.addItem(self.scatter_peaks)
        
        if len(self.nodi_rilevati) > 0:
            self.current_state = self.STATE_FORM_ENTRY
            
            # Teniamo traccia di quali nodi abbiamo già salvato
            self.nodi_salvati = set() 
            self.nodo_selezionato_index = None # Indice X del nodo attualmente cliccato
            
            self.lbl_stato.setText("STATO: Mappatura Libera")
            self.lbl_stato.setStyleSheet("color: #2196F3; font-weight: bold; font-size: 18px;")
            self.lbl_istruzioni.setText(f"Trovati {len(self.nodi_rilevati)} nodi!\n\nClicca su un pallino rosso nel grafico\nper associargli un nome.")
            
        else:
            QMessageBox.warning(self, "Attenzione", "Nessun nodo rilevato.")
            self.baseline_frames = []

    def on_scatter_clicked(self, plot, points):
        """Gestisce il click su uno dei pallini rossi."""
        # points è una lista dei punti cliccati (di solito 1)
        if len(points) == 0:
            return
            
        punto = points[0]
        indice_x = int(punto.pos().x())
        
        # Controlliamo se questo nodo è già stato salvato
        if indice_x in self.nodi_salvati:
            QMessageBox.information(self, "Info", "Hai già associato questo nodo!")
            return
            
        # Aggiorniamo la UI per questo specifico nodo
        self.nodo_selezionato_index = indice_x
        
        self.lbl_istruzioni.setText(f"Stai configurando il Nodo a Frequenza: {indice_x}")
        self.lbl_istruzioni.setStyleSheet("font-size: 16px; margin: 20px 0; color: #E91E63; font-weight: bold;")
        
        self.entry_node_id.setEnabled(True)
        self.entry_desc.setEnabled(True)
        self.btn_salva.setEnabled(True)
        
        # Suggerimento automatico dell'ID
        numero_nodo = len(self.nodi_salvati) + 1
        self.entry_node_id.setText(f"Nodo_{numero_nodo}")
        self.entry_desc.clear()
        self.entry_desc.setFocus()
        
        # Opzionale: Cambiamo il colore del pallino cliccato per dare feedback visivo
        # (Richiede un po' di manipolazione dei brush di PyQtGraph, ma l'hoverable fa già un buon lavoro)

    def prepara_form_nodo(self):
        """Aggiorna i testi e abilita i bottoni per compilare il nodo N."""
        self.lbl_stato.setText("STATO: Associazione Vocale")
        self.lbl_stato.setStyleSheet("color: #2196F3; font-weight: bold; font-size: 18px;")
        
        indice = self.nodi_rilevati[self.nodo_corrente_index]
        totale = len(self.nodi_rilevati)
        
        self.lbl_istruzioni.setText(f"Trovati {totale} nodi!\n\nStai configurando il NODO {self.nodo_corrente_index + 1} di {totale}\n(Punto di Risonanza: {indice})")
        
        self.entry_node_id.setEnabled(True)
        self.entry_desc.setEnabled(True)
        self.btn_salva.setEnabled(True)
        self.btn_ignora.setEnabled(True)
        
        self.entry_node_id.setText(f"Nodo_{self.nodo_corrente_index + 1}")
        self.entry_desc.clear()
        self.entry_desc.setFocus()

    def salva_nodo_corrente(self):
        if self.nodo_selezionato_index is None:
            return
            
        node_id = self.entry_node_id.text().strip()
        desc = self.entry_desc.text().strip()

        if not node_id or not desc:
            QMessageBox.warning(self, "Attenzione", "Compila entrambi i campi prima di salvare.")
            return

        # Creiamo il nodo con l'indice del pallino cliccato
        window_data = { "peak_index": self.nodo_selezionato_index }
        nuovo_nodo = Node(id=node_id, description=desc, fingerprint=window_data)
        self.haptic_graph.add_node(nuovo_nodo)
        
        # Segniamo il nodo come completato
        self.nodi_salvati.add(self.nodo_selezionato_index)
        print(f"Salvato {node_id} all'indice {self.nodo_selezionato_index}")
        
        # Resettiamo la UI in attesa del prossimo click
        self.nodo_selezionato_index = None
        self.entry_node_id.clear()
        self.entry_node_id.setEnabled(False)
        self.entry_desc.clear()
        self.entry_desc.setEnabled(False)
        self.btn_salva.setEnabled(False)
        
        # Controlliamo se abbiamo finito
        nodi_rimanenti = len(self.nodi_rilevati) - len(self.nodi_salvati)
        
        if nodi_rimanenti > 0:
            self.lbl_istruzioni.setText(f"Nodo associato con successo!\nClicca su un altro pallino rosso.\n(Ne restano {nodi_rimanenti})")
            self.lbl_istruzioni.setStyleSheet("font-size: 16px; margin: 20px 0; color: black;")
        else:
            self.lbl_stato.setText("STATO: Mappatura Completata")
            self.lbl_stato.setStyleSheet("color: green; font-weight: bold; font-size: 18px;")
            self.lbl_istruzioni.setText("Tutti i nodi sono stati associati!\nClicca su 'Termina ed Esporta JSON'.")
    
    def ignora_nodo_corrente(self):
        """Salta l'indice attuale senza inserirlo nel grafo."""
        print(f"Ignorato picco fantasma all'indice {self.nodi_rilevati[self.nodo_corrente_index]}")
        
        # Andiamo direttamente avanti senza salvare nulla
        self._passa_al_prossimo_nodo()

    def _passa_al_prossimo_nodo(self):
        """Funzione helper per far avanzare la procedura o concluderla."""
        self.nodo_corrente_index += 1
        
        if self.nodo_corrente_index < len(self.nodi_rilevati):
            self.prepara_form_nodo()
        else:
            self.lbl_stato.setText("STATO: Procedura Completata")
            self.lbl_stato.setStyleSheet("color: green; font-weight: bold; font-size: 18px;")
            self.lbl_istruzioni.setText("Tutti i nodi rilevati sono stati analizzati!\nEsporta il file JSON per usarlo.")
            
            self.entry_node_id.clear()
            self.entry_node_id.setEnabled(False)
            self.entry_desc.clear()
            self.entry_desc.setEnabled(False)
            
            self.btn_salva.setEnabled(False)
            self.btn_ignora.setEnabled(False)

    def termina_e_salva(self):
        from PyQt6.QtWidgets import QFileDialog, QMessageBox
        
        if len(self.haptic_graph.nodes) == 0:
            QMessageBox.warning(self, "Attenzione", "Nessun nodo mappato da salvare.")
            return
        
        if hasattr(self, 'worker'):
            self.worker.is_paused = True

        filepath, _ = QFileDialog.getSaveFileName(self, "Salva Mappa Nodi", "mappa_sensore.json", "JSON Files (*.json)")
        
        if filepath:
            self.haptic_graph.to_json(filepath)
            QMessageBox.information(self, "Successo", f"File JSON salvato correttamente.")
            self.close() 
        else:
            if hasattr(self, 'worker'):
                self.worker.is_paused = False

    def closeEvent(self, event):
        if hasattr(self, 'worker') and self.worker.isRunning():
            self.worker.stop()
        self.deleteLater()
        event.accept()