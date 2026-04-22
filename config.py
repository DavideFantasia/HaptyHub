import os
from dotenv import load_dotenv

DEBUG_MODE = True #used to turn of the real API calls

#===========================================================================
#   ESEMPIO DI CONFIGURAZIONE
# --------------------------------------------------------------------------
# Path globali (in chiaro)
# Esempio: 
# BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# OUTPUT_DIR = os.path.join(BASE_DIR, "output_models")
# Per convenzione, si scrivono in maiuscolo per indicare che sono costanti.

# Chiavi API (NON METTERE IN CHIARO)
# OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
# if not OPENAI_API_KEY: raise ValueError("OpenAI API Key not found")
#===========================================================================

#====================
#---- Gemini Key ----
#====================
# Carica le variabili d'ambiente dal file .env
load_dotenv()
# Legge la chiave definita nel file .env, se non presente
# va creato
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

#GEMINI_MODEL_ID = "gemini-3.1-pro-preview"
#GEMINI_MODEL_ID = "gemini-2.5-flash"
GEMINI_MODEL_ID = "gemini-3-flash-preview"

#====================
#---- Path Utili ----
#====================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Cartella dove salveremo i file .scad generati
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)
PROMPT_DIR = os.path.join(BASE_DIR, "src", "prompts")
# Cartella degli asset (icone, immagini, ecc.)
ASSET_DIR = os.path.join(BASE_DIR, "assets")
# Cartella temporanea per file intermedi (es. log, cache, ecc.)
TEMP_DIR = os.path.join(BASE_DIR, "temp")
os.makedirs(TEMP_DIR, exist_ok=True)