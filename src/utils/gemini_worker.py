
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
            # logica di exponential backoff per gestire eventuali errori di rete o limiti API
            max_retries = 3
            base_delay = 2.0 # Secondi di attesa base
        
            for attempt in range(max_retries):
                try:
                    if attempt == 0:
                        self.progress.emit("Fase 1: Analisi dell'immagine in corso...")
                    else:
                        self.progress.emit(f"Fase 1: Nuovo tentativo in corso... ({attempt + 1}/{max_retries})")
                    # --- FASE 1: Immagine -> Testo (Sempre eseguita) ---
                    risultato_fase_1 = self.phase_1_only()

                    # --- FASE 2: Testo -> OpenSCAD (Condizionale) ---
                    if self.prompt_fase_2:
                        self.progress.emit("Fase 2: Generazione del codice OpenSCAD in corso...")    
                        # Segnaliamo la fine passando il percorso del file
                        filepath = self.phase_2_only(risultato_fase_1)
                        self.finished.emit(filepath)
                    
                    else:
                        # Se non c'è il prompt 2, siamo nella logica Android/ELK!
                        # Segnaliamo la fine passando direttamente il JSON testuale
                        self.progress.emit("Fase 1 completata. JSON estratto.")
                        self.finished.emit(risultato_fase_1)
                    return
                
                except Exception as e:
                    error_msg = str(e)
                    
                    # Controlliamo se è un errore 503 (Server Overload)
                    if "503" in error_msg or "UNAVAILABLE" in error_msg:
                        if attempt < max_retries - 1:
                            # Calcoliamo il ritardo esponenziale: 2s -> 4s -> 8s
                            delay = base_delay * (2 ** attempt) 
                            
                            self.progress.emit(f"Server Google temporaneamente occupati (503). Attendo {delay} secondi e riprovo...")
                            time.sleep(delay) # Mettiamo in pausa questo Thread (la GUI non si blocca!)
                        else:
                            # Abbiamo finito i tentativi
                            self.error.emit("I server di Google sono attualmente troppo carichi. Riprova tra qualche minuto.")
                            return
                    else:
                        # Se è un errore diverso (es. API Key errata o niente Internet), falliamo subito
                        self.error.emit(f"Errore API: {error_msg}")
            
        except Exception as e:
            self.error.emit(f"Errore API: {str(e)}")

    def phase_1_only(self):
        """Metodo alternativo per eseguire solo la Fase 1 (analisi immagine) e restituire il testo."""\
        # chiamata reale a Gemini per analizzare l'immagine e restituire il testo (JSON o descrizione)
        if config.DEBUG_MODE == False:
            return self.client.analyze_image(self.image_path, self.prompt_fase_1)
        else:
            # returniamo una risposta prefatta di Gemini per testare la logica senza chiamate API reali
            # usando il json temp/GeminiOutput_Debug.json
            with open(os.path.join(config.TEMP_DIR, "GeminiOutput_Debug.json"), "r", encoding="utf-8") as f:
                return f.read()
    def phase_2_only(self, risultato_fase_1):
        self.progress.emit("Fase 2: Generazione del modello 3D (OpenSCAD)...")
        scad_code = self.client.generate_scad(risultato_fase_1, self.prompt_fase_2)
                
        # Salviamo il file in locale (Logica Circuito)
        timestamp = int(time.time())
        filepath = os.path.join(config.OUTPUT_DIR, f"modello_{timestamp}.scad")
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(scad_code)
        return filepath
                