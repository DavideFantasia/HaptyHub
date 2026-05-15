# HaptyHub
HaptyHub è un'applicazione desktop che utilizza l'Intelligenza Artificiale (LLM $\times$ Computer Vision) per tradurre diagrammi, mappe e grafi bidimensionali (presenti in slide o appunti) in modelli 3D tattili (file `.scad`).<br>
Oltre alla generazione del modello 3D, il software si interfaccia con hardware esterno per **rendere i modelli 3D interattivi**: toccando i nodi del modello stampato, l'applicazione riconosce il tocco e legge ad alta voce la descrizione del nodo tramite sintesi vocale (Text-to-Speech).

L'obiettivo principale è favorire l'accessibilità allo studio per studenti ciechi o ipovedenti (Low Vision), permettendo la stampa 3D rapida di materiale didattico e l'esplorazione aptica interattiva.

---

# Installazione e Setup
Per eseguire il software è necessario avere [Python 3](https://www.python.org/downloads/) installato sul sistema. Il progetto include script di installazione automatica che creano un ambiente virtuale, installano le dipendenze e creano le scorciatoie sul desktop.

## 1.    Clonare il repository
```bash
git clone git@github.com:DavideFantasia/HaptyHub.git
cd HaptyHub
```
In alternativa, è possibile scaricare il progetto in formato `.zip` ed estrarlo.

## 2. Eseguire l'installazione automatica

### Su Windows:
Esegui il file `install.bat` (tramite doppio clic o da terminale). Se Windows mostra un avviso di sicurezza, fai clic col tasto destro ed esegui come amministratore.
L'avvio successivo dell'applicazione potrà avvenire tramite il collegamento creato sul Desktop o lanciando `HaptyHub.bat`.

Fai doppio clic sul file `install.bat` oppure eseguilo da terminale. Lo script configurerà l'ambiente e creerà un collegamento sul Desktop.
- In caso di lamentele da parte di Windows, fare tasto destro sul file ed _eseguire come amministratore_

### Su Linux/macOS:
Apri il terminale ed esegui lo script bash (ti verrà chiesta la password per configurare le regole `udev` necessarie alla lettura della porta USB):

```Bash
chmod +x install.sh
./install.sh
```
L'avvio successivo potrà avvenire ricercando l'applicazione tra i programmi o lanciando `HaptyHub.sh`.

### 3. Configurazione API Key
Il Software utilizza le API di Google Gemini. Dopo l'installazione, verrà generato un file denominato `.env` nella cartella principale.
Puoi inserire la tua chiave in due modi:
1. Avviando il programma e andando nel menu in alto: `Opzioni -> API Key`.
2. Aprendo il file `.env` con un editor di testo e incollando la chiave: `GEMINI_API_KEY=la_tua_chiave`

La propria chiave di Gemini è ottenibile gratuitamente al seguente [link](https://aistudio.google.com/api-keys)

---

# Guida all'uso
Il software è diviso in tre flussi di lavoro principali, accessibili dalla UI:

## Creazione di modelli 3D da foto
Questa funzione traduce un'immagine 2D in codice 3D.

**1.** Avvia l'applicazione (doppio clic sull'icona creata sul Desktop o sull'eseguibile creato nella cartella di lavoro).
**2.** Selezionare la Funzione Desiderata<br>
  **a.** Se si vuole creare un modello 3D: trascina un'immagine (es. Flow Chart, Grafo) nell'area di **PREVIEW IMG** a sinistra, oppure cliccaci sopra per selezionare un file.<br>
  **b.** Seleziona il tipo di diagramma dal **menu Template** in alto (es. _Direct Graph_, _Flow Chart_).<br>
  **c.** Compila i parametri richiesti in base all'operazione, come per esempio `Opzioni->Aggiungi Device/Carica Device` per la generazione di Overlay Tablet<br>
**6.** Se si vuole generare un modello 3D, basterà cliccare sul pulsante Invia in basso a destra. L'IA elaborerà l'immagine e salverà automaticamente il file generato nella cartella `output/`, visualizzando a fine processo il modello 3D nel visualizzatore 3D a lato.

## Calibrazione e Associazione (Grafi Aptici)
Questa funzione serve per "insegnare" al software a riconoscere i tocchi sul modello stampato in 3D, salvando le frequenze di risonanza.

1. Collega la scheda hardware sensore (es. _NanoVNA_) via USB.
2. Vai nel menu **Tattile -> Calibrazione Sensore** o seleziona la funzione omonima nella pagina iniziale.
3. Il software stabilirà una linea di base ambientale (**non toccare il sensore** in questa fase).
4. Segui le istruzioni a schermo: **tocca fisicamente un nodo** sul modello 3D e tieni premuto.
5. Quando il software rileva e stabilizza il picco, rilascia e compila l'ID e la Descrizione del nodo relativo al Picco di cui noti il maggior cambio.
6. Ripeti per tutti i nodi. Al termine, clicca su **Termina ed Esporta** per salvare l'intera mappa tattile in un file `.json`.

## Lettura Interattiva del Grafo Aptico
Questa è la modalità di utilizzo per l'utente finale. Permette l'esplorazione del modello 3D stampato con feedback vocale.

1. Vai nel menu **Tattile -> Lettura Grafo Tattile** o seleziona la funzione omonima nella pagina iniziale.
2. Dal menu della nuova finestra, fai clic su **File -> Importa Grafo (JSON)** e seleziona il file di calibrazione creato precedentemente.
3. Il software calcolerà una _nuova linea_ di base (per adattarsi alle condizioni ambientali attuali).
4. Tocca un nodo qualsiasi sul modello fisico: il software calcolerà in tempo reale l'Errore Quadratico Medio (MSE) delle frequenze, individuerà il nodo corrispondente e lo leggerà ad alta voce usando la sintesi vocale nativa (Windows SAPI5 o Linux espeak/mbrola).

---

# Note di Sviluppo e Architettura
Il progetto è costruito per essere modulare, reattivo ed estensibile.

## Struttura del Progetto
```textHaptyHub/
├── assets/                     # Icone e risorse grafiche dell'applicazione
├── src/                        # Codice sorgente principale
│   ├── api_client.py           # Gestione della comunicazione con l'API di Gemini
│   ├── models/                 # Strutture dati (es. rappresentazione di Grafo e Nodi)
│   ├── prompts/                # Template dei prompt per l'LLM divisi per tipologia
│   │   ├── basic/              # Prompt per modelli 3D base (Flowchart, Grafi, Insiemi)
│   │   └── interactive/        # Prompt per modelli interattivi avanzati
│   ├── ui/                     # Componenti dell'Interfaccia Grafica (PyQt6)
│   │   ├── HaptyHub.py                 # Dashboard principale
│   │   ├── android_model_window.py     # Finestra generazione overlay per Tablet
│   │   ├── circuit_model_window.py     # Finestra generazione base interattiva (NanoVNA)
│   │   ├── basic_haptic_modeler.py     # Finestra generazione schema in rilievo (senza interazione)
│   │   ├── calibration_window.py       # Finestra di calibrazione e associazione sensore
│   │   ├── hapticReader_window.py      # Finestra di lettura con feedback vocale (TTS)
│   │   └── panels.py                   # Collezione di Pannelli UI
│   └── utils/                  # Script di utilità e motori di elaborazione
│       ├── run_elk.js                  # Motore di routing spaziale ELK (Node.js)
│       ├── json_to_scad*.py            # Convertitori delle coordinate spaziali in OpenSCAD
│       ├── gemini_worker.py            # Thread asincrono per chiamate LLM
│       ├── sensor_*.py                 # Logica di comunicazione seriale con NanoVNA
│       ├── tts_worker.py               # Motore Text-to-Speech per il feedback audio
│       ├── stl_viewer.py               # Renderizzatore 3D integrato nella GUI
│       └── ...                         # File secondari di Utilities
├── config.py                     # Parametri globali, path e impostazioni di configurazione
├── main.py                       # Entry point dell'applicazione
├── requirements.txt              # Dipendenze Python necessarie
├── install.sh / install.bat      # Script di installazione automatizzata (Linux/Windows)
└── uninstall.sh / uninstall.bat  # Script di disinstallazione automatizzata (Linux/Windows)
```

## Modalità Debug

Nel file `config.py` è presente la variabile `DEBUG_MODE` (modificabile anche a runtime dal **menu Opzioni -> Modalità Debug**).

- Se **ATTIVATA**, l'app utilizza il `TestClient`. Verranno simulati l'invio e la ricezione di dati senza contattare i server di Google. È fondamentale usarla durante lo sviluppo dell'interfaccia o la creazione dei layout per non consumare la quota API.
- Se **DISATTIVATA**, verranno effettuate chiamate reali a Gemini.

## Multithreading e Hardware
Per evitare "freeze" dell'interfaccia grafica:
- Le chiamate API sono gestite in modo asincrono tramite `GeminiWorker`.
- L'hardware (Seriale) è letto in loop da un `SensorWorker` separato. Le letture grezze sono stabilizzate algoritmicamente per ridurre il rumore e i falsi positivi durante la lettura.
- La sintesi vocale utilizza un `TTSWorker` basato su una struttura a **Queue** thread-safe. Questo previene crash di **pyttsx3**/motori COM e blocchi UI, assicurando un'esperienza fluida anche se l'utente tocca i nodi velocemente.
- La conversione da file `.scad` a file `.stl` per la visualizzazione in App e la successiva stampa è gestita da `STLCompilerWorker`.

## Come aggiungere un nuovo tipo di Schema (Pattern Strategy)
Per aggiungere il supporto a un nuovo tipo di diagramma da processare con l'IA:
- **Crea i Prompt**: Crea una nuova cartella in `src/prompts/`, differenziandolo fra uno interattivo o meno (es. `/basic/NuovoSchema/` o `/interactive/NuovoSchema/`) e aggiungi due file: `phase1.txt` (Vision-to-Text) e `phase2.txt` (Text-to-SCAD), si consiglia di fare riferimento ai prompt già presenti nella medesima cartella come riferimento.
- **Crea la Logica Prompt**: In `src/prompts/templates.py`, crea una classe che eredita da `BaseTemplate`. Implementa i metodi `get_phase_1()` e `get_phase_2()` per iniettare i parametri dell'utente nel testo.
- **Crea il Pannello UI**: In `src/ui/panels.py`, crea una classe che eredita da `BaseTemplatePanel`. Crea qui il form (campi di testo, spinbox) per raccogliere i dati specifici dal frontend.
- **Registra il Template**: In `src/ui/landing_window.py`, aggiungi il nuovo pannello allo `QStackedWidget` nella colonna di destra e aggiungi una nuova azione checkable nel menu in alto ("Template").

## Disinstallazione
Se desideri rimuovere il software e pulire il sistema (inclusi gli ambienti virtuali e le regole USB su Linux):
- **Windows**: Esegui `uninstall.bat`.
- **Linux**: Esegui `./uninstall.sh`.
