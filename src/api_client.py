from google import genai
from google.genai import types
import PIL.Image
import config

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
        """Fase 2: Prende la descrizione e genera il codice OpenSCAD."""
        
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
    
    def analyze_image(self, image_path: str, prompt: str) -> str:
        return "Test Analyze"
    
    def generate_scad(self, description: str, system_prompt: str) -> str:
        return "Test Generate:\n"+system_prompt