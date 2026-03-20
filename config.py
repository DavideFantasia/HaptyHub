import os
from dotenv import load_dotenv

load_dotenv()

# Path globali (in chiaro)
# Esempio: 
# BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# OUTPUT_DIR = os.path.join(BASE_DIR, "output_models")

# Chiavi API (NON METTERE IN CHIARO)
# OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
# if not OPENAI_API_KEY: raise ValueError("OpenAI API Key not found")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY: raise ValueError("GEMINI API Key not found")