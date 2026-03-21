# HaptyGraph

HaptyGraph è un'applicazione desktop che utilizza l'Intelligenza Artificiale (LLM e Computer Vision) per tradurre diagrammi, mappe e grafi bidimensionali (presenti in slide o appunti) in modelli 3D tattili (file `.scad`). 
L'obiettivo principale è favorire l'accessibilità allo studio per studenti ciechi o ipovedenti (Low Vision), permettendo la stampa 3D rapida di materiale didattico.

## Architettura e Flusso di Lavoro

L'applicazione è sviluppata in **Python 3** con interfaccia grafica **PyQt6**. 
La generazione del modello 3D avviene tramite le API di Google Gemini (`google-genai`) in due fasi distinte e sequenziali, per massimizzare la precisione spaziale:

1.  **Fase 1 (Vision to Text):** L'immagine caricata e i parametri scelti dall'utente vengono inviati al modello Vision. Il modello restituisce una descrizione testuale altamente strutturata, deterministica e geometricamente accurata del grafo (nodi, archi, coordinate spaziali).
2.  **Fase 2 (Text to Code):** La descrizione testuale della Fase 1 viene passata nuovamente all'LLM (con un system prompt diverso) che agisce come esperto programmatore per generare esclusivamente codice **OpenSCAD** valido.

> **Nota di sviluppo:** Le chiamate API sono gestite in modo asincrono tramite un `QThread` (`GeminiWorker`) per evitare il blocco dell'interfaccia grafica durante l'attesa delle risposte.

## Struttura del Progetto

Il progetto segue un approccio modulare per facilitare l'aggiunta di nuovi tipi di diagrammi:

```text
HaptyGraph/
├── .env                    # (Da creare) Contiene GEMINI_API_KEY
├── config.py               # Variabili globali, path e toggle DEBUG_MODE
├── main.py                 # Entry-point dell'applicazione
├── requirements.txt        # Dipendenze del progetto
├── output/                 # Cartella autogenerata per i file .scad finali
└── src/
    ├── api_client.py       # Gestione delle chiamate a Gemini (Client reale e TestClient)
    ├── prompts/            # Logica e testi per i prompt inviati all'IA
    │   ├── templates.py    # Classi base e implementazioni dei vari template
    │   ├── DirectGraph/    # File .txt con i prompt (Fase 1 e 2) per grafi diretti
    │   └── UndirectGraph/  # File .txt con i prompt (Fase 1 e 2) per grafi indiretti
    ├── ui/                 # Componenti dell'interfaccia utente (PyQt6)
    │   ├── landing_window.py # Finestra principale e gestione eventi
    │   └── panels.py       # Pannelli dinamici (Form) per i parametri specifici
    └── utils/
        └── image_helper.py # Utility OpenCV/PyQt per caricamento e scaling immagini
```

## Installazione e Setup
Per eseguire il software è necessario Python 3 installato sul sistema. Si consiglia vivamente l'uso di un ambiente virtuale.

```Bash
git clone git@github.com:DavideFantasia/HaptyGraph.git
cd HaptyGraph
```
### Configurazione Ambiente Virtuale
#### Su Linux/macOS:

```Bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```
*(Solo per Linux)*: Per evitare problemi di caricamento cursori con PyQt6, assicurati di avere installata la libreria di sistema:
`sudo apt install libxcb-cursor0`

#### Su Windows:

```Bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```
### Configurazione API Key (.env)
Il progetto utilizza le API di Google Gemini. Crea un file denominato `.env` nella root del progetto e inserisci la tua chiave:

```Snippet di codice
GEMINI_API_KEY=la_tua_chiave_api_qui
```
## Sviluppo e Debug
Nel file `config.py` è presente la variabile `DEBUG_MODE`.

- Se impostata su `True`, l'app utilizzerà il `TestClient` (che simula le risposte dell'API in locale con del testo fantoccio). È fondamentale usarlo durante lo sviluppo della UI per non sprecare token API.

- Impostare su `False` per le generazioni reali.

##  Come aggiungere un nuovo tipo di Schema (Template)
L'app utilizza il pattern *Strategy*. Per aggiungere il supporto a un nuovo tipo di schema (es. *Flow Chart*):

1.  **Crea i Prompt**: Crea una nuova cartella in `src/prompts/` (es. `FlowChart/`) e aggiungi due file: `phase1.txt` e `phase2.txt`, contenenti i prompt testuali effettivi per la prima fase di analisi dell'immagine e per la seconda fase di costruzione del modello 3D.

2.  **Crea la Logica Prompt**: In `src/prompts/templates.py`, crea una classe che eredita da `BasePrompt` che implementi la logica di caricamento dei nuovi file txt o la parametrizzazione di questa, ove necessario.

3.  **Crea il Pannello UI**: In `src/ui/panels.py`, crea un nuovo Form (es. `FlowChartPanel`) per raccogliere gli input specifici dall'utente (es. numero di blocchi decisionali).

4.  **Registra il Template**: In `landing_window.py`, aggiungi il nuovo pannello allo `stacked_widget` e crea una nuova voce nel menu "Template".
