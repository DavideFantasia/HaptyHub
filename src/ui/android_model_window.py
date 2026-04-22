import os
import json
import subprocess
from PyQt6.QtWidgets import QMainWindow, QVBoxLayout, QWidget, QPushButton, QLabel, QFileDialog, QTextEdit
from PyQt6.QtCore import Qt

from src.utils.gemini_worker import GeminiWorker # Riutilizziamo il worker asincrono

class AndroidModelWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Generatore Modello 3D (Android/Tablet)")
        self.resize(1000, 700)
        
        self.image_path = None

        # UI Layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        self.lbl_info = QLabel("Trascina un'immagine o seleziona un file per iniziare la pipeline ELK")
        self.lbl_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.lbl_info)

        self.btn_select = QPushButton("Seleziona Immagine")
        self.btn_select.clicked.connect(self.select_image)
        layout.addWidget(self.btn_select)

        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        self.log_area.setPlaceholderText("Log della pipeline...")
        layout.addWidget(self.log_area)

        self.btn_generate = QPushButton("Genera Modello con ELK")
        self.btn_generate.setEnabled(False)
        self.btn_generate.clicked.connect(self.start_pipeline)
        layout.addWidget(self.btn_generate)

    def select_image(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Apri Immagine", "", "Images (*.png *.jpg *.jpeg)")
        if file_path:
            self.image_path = file_path
            self.lbl_info.setText(f"Immagine caricata: {os.path.basename(file_path)}")
            self.btn_generate.setEnabled(True)

    def start_pipeline(self):
        self.log_area.append(">>> Fase 1: Invio immagine a Gemini (Estrazione Grafo JSON)...")
        
        # Prompt specifico per ELK (estratto dai tuoi file sperimentali)
        prompt_elk = """Analizza l'immagine e restituisci SOLO un file JSON con questa struttura:
        {"nodes": [{"id": "n1", "label": "Nome"}], "edges": [{"source": "n1", "target": "n2"}]}
        Non aggiungere testo prima o dopo il JSON."""

        self.worker = GeminiWorker(self.image_path, prompt_elk)
        self.worker.finished.connect(self.process_gemini_response)
        self.worker.start()

    def process_gemini_response(self, response):
        try:
            # Pulizia della risposta (rimozione di eventuali ```json ... ```)
            clean_json = response.replace("```json", "").replace("```", "").strip()
            graph_data = json.loads(clean_json)
            
            # Salvataggio temporaneo per ELK
            input_path = "temp_graph.json"
            with open(input_path, "w") as f:
                json.dump(graph_data, f)
            
            self.log_area.append(">>> Fase 2: Esecuzione ELK Layout (Node.js)...")
            self.run_elk_layout(input_path)
            
        except Exception as e:
            self.log_area.append(f"ERRORE FASE 1: {str(e)}")

    def run_elk_layout(self, input_path):
        output_path = "output_coords.json"
        try:
            # Chiamata a Node.js (run_elk.js)
            # Assicurati che 'node' sia nel PATH e run_elk.js sia in src/utils/
            cmd = ["node", "src/utils/run_elk.js", input_path, output_path]
            subprocess.run(cmd, check=True)
            
            self.log_area.append(">>> Fase 3: Conversione in OpenSCAD...")
            self.generate_scad(output_path)
            
        except Exception as e:
            self.log_area.append(f"ERRORE FASE 2: {str(e)}")

    def generate_scad(self, coords_path):
        try:
            # Qui importiamo la logica di json_to_scad.py
            from src.utils.json_to_scad import convert_to_scad
            
            scad_output = "output/android_model.scad"
            convert_to_scad(coords_path, scad_output)
            
            self.log_area.append(f"COMPLETATO! Modello salvato in: {scad_output}")
            os.system(f"openscad {scad_output} &") # Anteprima automatica se installato
            
        except Exception as e:
            self.log_area.append(f"ERRORE FASE 3: {str(e)}")