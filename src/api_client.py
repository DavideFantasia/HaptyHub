from google import genai
from google.genai import types
import PIL.Image
import config, os

class GeminiClient:
    def __init__(self):
        # Inizializza il client passando la chiave API esplicitamente
        self.client = genai.Client(api_key=config.GEMINI_API_KEY)
        
        self.model_id = config.GEMINI_MODEL_ID

    def analyze_image(self, image_path: str, prompt: str) -> str:
        """Fase 1: Analizza l'immagine e restituisce la descrizione testuale."""
        img = PIL.Image.open(image_path)
        
        response = self.client.models.generate_content(
            model=self.model_id,
            contents=[prompt, img]
        )
        return response.text

    def generate_scad(self, description: str, system_prompt: str) -> str:
        """[DEPRECATED] Fase 2: Prende la descrizione e genera il codice OpenSCAD."""
        
        response = self.client.models.generate_content(
            model=self.model_id,
            contents=description,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=1.0 # Abbassiamo la temperatura per avere codice più prevedibile e meno "creativo"
            )
        )
        
        # Pulisce l'output nel caso in cui Gemini usi la formattazione markdown
        testo_pulito = response.text.replace("```scad", "").replace("```openscad", "").replace("```", "").strip()
        return testo_pulito
    
class TestClient:
    """Classe di test per verificare il funzionamento del client senza chiamare l'API."""

    def __init__(self):
        self.client = None

        # Definisci il percorso del file temporaneo (rispetto a dove esegui lo script)
        self.temp_graph_path = os.path.join(config.TEMP_DIR, "output_coordinates.json")
    
    def analyze_image(self, image_path: str, prompt: str) -> str:
        """
        In modalità test, cerca un file JSON pre-generato. 
        Se lo trova, lo restituisce, altrimenti genera un JSON fittizio.
        """

        # Se il file temp_graph.json esiste, leggilo e restituiscilo
        if os.path.exists(self.temp_graph_path):
            print(f"🛠️ [TEST CLIENT] Trovato {self.temp_graph_path}. Caricamento dati mock...")
            try:
                # Usiamo f.read() e NON json.load() perché l'API vera restituisce 
                # una stringa di testo, non un dizionario Python.
                with open(self.temp_graph_path, 'r', encoding='utf-8') as f:
                    return f.read()
            except Exception as e:
                print(f"❌ Errore nella lettura del file di test: {e}")
                return f'{{"error": "Impossibile leggere il file di test: {e}"}}'
        
        # Fallback se il file non c'è (JSON base fittizio per non far crashare l'app)
        print("🛠️ [TEST CLIENT] File temp_graph.json non trovato. Uso JSON di fallback.")
        fallback_json = """
        {
            "nodes": [{"id": "n1", "label": "Nodo Test"}],
            "edges": []
        }
        """
        return fallback_json.strip()
    
    def generate_scad(self, description: str, system_prompt: str) -> str:
        return "System prompt: " + system_prompt