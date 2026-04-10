# HaptyGraph
HaptyGraph è un'applicazione desktop che utilizza l'Intelligenza Artificiale (LLM e Computer Vision) per tradurre diagrammi, mappe e grafi bidimensionali (presenti in slide o appunti) in modelli 3D tattili (file `.scad`).<br>
Oltre alla generazione del modello 3D, il software si interfaccia con hardware esterno per **rendere i modelli 3D interattivi**: toccando i nodi del modello stampato, l'applicazione riconosce il tocco e legge ad alta voce la descrizione del nodo tramite sintesi vocale (Text-to-Speech).

L'obiettivo principale è favorire l'accessibilità allo studio per studenti ciechi o ipovedenti (Low Vision), permettendo la stampa 3D rapida di materiale didattico e l'esplorazione aptica interattiva.

---

# Installazione e Setup
Per eseguire il software è necessario avere [Python 3](https://www.python.org/downloads/) installato sul sistema. Il progetto include script di installazione automatica che creano un ambiente virtuale, installano le dipendenze e creano le scorciatoie sul desktop.

## 1.    Clonare il repository
```bash
git clone git@github.com:DavideFantasia/HaptyGraph.git
cd HaptyGraph
```

## 2. Eseguire l'installazione automatica

### Su Windows:
Fai doppio clic sul file `install.bat` oppure eseguilo da terminale. Lo script configurerà l'ambiente e creerà un collegamento sul Desktop.

### Su Linux/macOS:
Apri il terminale ed esegui lo script bash (ti verrà chiesta la password per configurare le regole `udev` necessarie alla lettura della porta USB):

```Bash
chmod +x install.sh
./install.sh
```
### 3. Configurazione API Key
Il progetto utilizza le API di Google Gemini. Dopo l'installazione, verrà generato un file denominato `.env` nella cartella principale.
Puoi inserire la tua chiave in due modi:
1. Avviando il programma e andando nel menu in alto: `Opzioni -> API Key`.
2. Aprendo il file `.env` con un editor di testo e incollando la chiave: `GEMINI_API_KEY=la_tua_chiave`

La propria chiave di Gemini è trovabile al seguente [link](https://aistudio.google.com/api-keys)

---

# Guida all'uso
Il software è diviso in tre flussi di lavoro principali, accessibili dalla UI:

## Creazione di file SCAD da foto
Questa funzione traduce un'immagine 2D in codice 3D.

1. Avvia l'applicazione (doppio clic sull'icona creata sul Desktop).
2. Trascina un'immagine (es. Flow Chart, Grafo) nell'area di **PREVIEW IMG** a sinistra, oppure cliccaci sopra per selezionare un file.
3. Seleziona il tipo di diagramma dal menu Template in alto (es. _Direct Graph_, _Flow Chart_).
4. Compila i parametri richiesti nel pannello di destra (Numero di Nodi, Archi, ecc.).
5. Clicca sul pulsante Invia. L'IA elaborerà l'immagine in due fasi e salverà automaticamente il file generato nella cartella `output/`.

## Calibrazione e Associazione (Grafi Aptici)
Questa funzione serve per "insegnare" al software a riconoscere i tocchi sul modello stampato in 3D, salvando le frequenze di risonanza.

1. Collega la scheda hardware sensore (es. _NanoVNA_) via USB.
2. Vai nel menu **Tattile -> Calibrazione Sensore**.
3. Il software stabilirà una linea di base ambientale (**non toccare il sensore** in questa fase).
4. Segui le istruzioni a schermo: **tocca fisicamente un nodo** sul modello 3D e tieni premuto.
5. Quando il software rileva e stabilizza il picco, rilascia e compila l'ID e la Descrizione del nodo.
6. Ripeti per tutti i nodi. Al termine, clicca su **Termina ed Esporta** per salvare l'intera mappa tattile in un file `.json`.

## Lettura Interattiva del Grafo Aptico
Questa è la modalità di utilizzo per l'utente finale. Permette l'esplorazione del modello 3D stampato con feedback vocale.

1. Vai nel menu **Tattile -> Lettura Grafo Tattile**.
2. Dal menu della nuova finestra, fai clic su **File -> Importa Grafo (JSON)** e seleziona il file di calibrazione creato precedentemente.
3. Il software calcolerà una _nuova linea_ di base (per adattarsi alle condizioni ambientali attuali).
4. Tocca un nodo qualsiasi sul modello fisico: il software calcolerà in tempo reale l'Errore Quadratico Medio (MSE) delle frequenze, individuerà il nodo corrispondente e lo leggerà ad alta voce usando la sintesi vocale nativa (Windows SAPI5 o Linux espeak/mbrola).

---

# Note di Sviluppo e Architettura
Il progetto è costruito per essere modulare, reattivo ed estensibile.

## Modalità Debug

Nel file `config.py` è presente la variabile `DEBUG_MODE` (modificabile anche a runtime dal **menu Opzioni -> Modalità Debug**).

- Se **ATTIVATA**, l'app utilizza il `TestClient`. Verranno simulati l'invio e la ricezione di dati senza contattare i server di Google. È fondamentale usarla durante lo sviluppo dell'interfaccia o la creazione dei layout per non consumare la quota API.
- Se **DISATTIVATA**, verranno effettuate chiamate reali a Gemini.

## Multithreading e Hardware
Per evitare "freeze" dell'interfaccia grafica:
- Le chiamate API sono gestite in modo asincrono tramite `GeminiWorker`.
- L'hardware (Seriale) è letto in loop da un `SensorWorker` separato. Le letture grezze sono stabilizzate algoritmicamente per ridurre il rumore e i falsi positivi durante la lettura.
- La sintesi vocale utilizza un `TTSWorker` basato su una struttura a **Queue** thread-safe. Questo previene crash di **pyttsx3**/motori COM e blocchi UI, assicurando un'esperienza fluida anche se l'utente tocca i nodi velocemente.

## Come aggiungere un nuovo tipo di Schema (Pattern Strategy)
Per aggiungere il supporto a un nuovo tipo di diagramma da processare con l'IA:
- **Crea i Prompt**: Crea una nuova cartella in `src/prompts/` (es. `NuovoSchema/`) e aggiungi due file: `phase1.txt` (Vision-to-Text) e `phase2.txt` (Text-to-SCAD).
- **Crea la Logica Prompt**: In `src/prompts/templates.py`, crea una classe che eredita da `BaseTemplate`. Implementa i metodi `get_phase_1()` e `get_phase_2()` per iniettare i parametri dell'utente nel testo.
- **Crea il Pannello UI**: In `src/ui/panels.py`, crea una classe che eredita da `BaseTemplatePanel`. Crea qui il form (campi di testo, spinbox) per raccogliere i dati specifici dal frontend.
- **Registra il Template**: In `src/ui/landing_window.py`, aggiungi il nuovo pannello allo `QStackedWidget` nella colonna di destra e aggiungi una nuova azione checkable nel menu in alto ("Template").

## Disinstallazione
Se desideri rimuovere il software e pulire il sistema (inclusi gli ambienti virtuali e le regole USB su Linux):
- **Windows**: Esegui `uninstall.bat`.
- **Linux**: Esegui `./uninstall.sh`.
