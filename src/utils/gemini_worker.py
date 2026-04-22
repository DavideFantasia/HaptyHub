
from PyQt6.QtCore import QThread, Qt, pyqtSignal

from src.api_client import GeminiClient
from src.api_client import TestClient # Classe di test senza chiamate API reali

import config, time, os

# --- Worker Thread per l'integrazione API con Gemini ---
class GeminiWorker(QThread):
    # Segnali per comunicare con la UI (Thread principale)
    progress = pyqtSignal(str)   # Per aggiornare lo stato (es. "Fase 1 in corso...")
    finished = pyqtSignal(str)   # Quando ha generato il file .scad
    error = pyqtSignal(str)      # In caso di problemi di rete

    def __init__(self, image_path, prompt_fase_1, prompt_fase_2=None):
        super().__init__()
        self.image_path = image_path
        self.prompt_fase_1 = prompt_fase_1
        self.prompt_fase_2 = prompt_fase_2

        if config.DEBUG_MODE:
            self.client = TestClient() # Usa il client di test
        else:
            self.client = GeminiClient()

    def run(self):
        try:
            # --- FASE 1: Immagine -> Testo (Sempre eseguita) ---
            self.progress.emit("Fase 1: Analisi dell'immagine in corso...")
            risultato_fase_1 = self.client.analyze_image(self.image_path, self.prompt_fase_1)
            
            # --- FASE 2: Testo -> OpenSCAD (Condizionale) ---
            if self.prompt_fase_2:
                self.progress.emit("Fase 2: Generazione del modello 3D (OpenSCAD)...")
                scad_code = self.client.generate_scad(risultato_fase_1, self.prompt_fase_2)
                
                # Salviamo il file in locale (Logica Circuito)
                timestamp = int(time.time())
                filepath = os.path.join(config.OUTPUT_DIR, f"modello_{timestamp}.scad")
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(scad_code)
                    
                # Segnaliamo la fine passando il percorso del file
                self.finished.emit(filepath)
            
            else:
                # Se non c'è il prompt 2, siamo nella logica Android/ELK!
                # Segnaliamo la fine passando direttamente il JSON testuale
                self.progress.emit("Fase 1 completata. JSON estratto.")
                self.finished.emit(risultato_fase_1)
            
        except Exception as e:
            self.error.emit(f"Errore API: {str(e)}")
