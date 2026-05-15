from PyQt6.QtCore import QThread, pyqtSignal
import os, json, subprocess, importlib

import config

class STLCompilerWorker(QThread):
    progress = pyqtSignal(str)
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, graph_data, generator_module, output_prefix):
        """
        :param graph_data: Il dizionario JSON con i dati dal LLM
        :param generator_module: Il percorso del modulo Python da usare (es. 'src.utils.json_to_scad')
        :param output_prefix: Il nome di base per i file generati (es. 'android_model' o 'circuit_model')
        """
        super().__init__()
        self.graph_data = graph_data
        self.generator_module = generator_module
        self.output_prefix = output_prefix

    def run(self):
        try:
            # 1. Salva i dati per ELK
            os.makedirs(config.TEMP_DIR, exist_ok=True)
            input_path = os.path.join(config.TEMP_DIR, "input_coordinates.json")
            with open(input_path, "w") as f:
                json.dump(self.graph_data, f)

            # 2. Lancia ELK (Node.js)
            self.progress.emit("Avvio motore grafico ELK (Node.js)...")
            cmd_elk = ["node", "src/utils/run_elk.js"]
            subprocess.run(cmd_elk, text=True, check=True)

            # 3. Converti in SCAD (Importazione Dinamica!)
            self.progress.emit("Conversione coordinate in modello 3D (.scad)...")
            os.makedirs(config.OUTPUT_DIR, exist_ok=True)
            scad_output = os.path.join(config.OUTPUT_DIR, f"{self.output_prefix}.scad")
            
            # Qui la magia: carica lo script giusto in base a chi ha chiamato il Worker
            scad_generator = importlib.import_module(self.generator_module)
            scad_generator.generate_scad(os.path.join(config.TEMP_DIR, "output_coordinates.json"), scad_output)
            
            # 4. Compilazione pesantissima in STL
            self.progress.emit("Compilazione in corso (OpenSCAD).\nQuesta operazione è molto pesante, attendere prego...")
            stl_output = os.path.join(config.OUTPUT_DIR, f"{self.output_prefix}.stl")
            cmd_scad = ["openscad", "-o", stl_output, scad_output]
            subprocess.run(cmd_scad, check=True)

            # Ha finito con successo!
            self.finished.emit(stl_output)

        except Exception as e:
            self.error.emit(str(e))