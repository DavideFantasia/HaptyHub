import os
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QTextEdit, QPushButton, QMenuBar, QMenu, 
                             QFileDialog, QFrame, QSizePolicy, QStyle, QStackedWidget,
                             QDialog, QLineEdit, QMessageBox)
from PyQt6.QtGui import QAction, QActionGroup
from PyQt6.QtCore import Qt, pyqtSignal

from src.ui.panels import GraphFormPanel, FlowChartPanel, SetTheoryPanel

# Importa la configurazione e gli helper
import config
from src.utils.image_helper import load_and_scale_image
from src.utils.gemini_worker import GeminiWorker

# --- Widget personalizzato per il drag and drop dell'immagine ---
# Sottoclasse della label di preview per gestire il drag and drop dei file immagine direttamente sulla preview stessa
class ImageDropLabel(QLabel):
    # Segnali personalizzati
    imageDropped = pyqtSignal(str)
    clicked = pyqtSignal()  # Nuovo segnale per il click

    def __init__(self, text=""):
        super().__init__(text)
        # Abilita esplicitamente il drag and drop su questo widget
        self.setAcceptDrops(True)
        # Cambia il cursore nella classica "manina" per indicare che è cliccabile
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def mousePressEvent(self, event):
        """Gestisce il click del mouse sul widget."""
        # Se viene premuto il tasto sinistro, emetti il segnale
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)

    def dragEnterEvent(self, event):
        """Controlla cosa sta entrando nell'area del widget."""
        if event.mimeData().hasUrls():
            url = event.mimeData().urls()[0]
            if url.isLocalFile():
                file_path = url.toLocalFile()
                ext = os.path.splitext(file_path)[1].lower()
                # Accetta solo se è un'immagine supportata
                if ext in ['.png', '.jpg', '.jpeg', '.bmp']:
                    event.acceptProposedAction()
                    # Cambiamo un po' lo stile per dare feedback visivo
                    self.setStyleSheet("border: 2px solid #4CAF50; background-color: #e8f5e9;")
                    return
        event.ignore()

    def dragLeaveEvent(self, event):
        """Ripristina lo stile se l'utente esce dall'area senza droppare."""
        self.setStyleSheet("") # Ripristina lo stile CSS predefinito assegnato dalla finestra

    def dropEvent(self, event):
        """Gestisce il rilascio effettivo del file."""
        self.setStyleSheet("") # Ripristina lo stile
        url = event.mimeData().urls()[0]
        file_path = url.toLocalFile()
        # Emette il segnale con il percorso, che verrà catturato dalla finestra principale
        self.imageDropped.emit(file_path)

class LandingWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("HaptiGraph")
        self.resize(1000, 700) # Una dimensione iniziale decente

        # --- Variabili di stato interne ---
        self.current_image_path = None

        # --- Inizializzazione ---
        self._init_menu_bar()
        self._init_central_widget()
        self._setup_layout()
        self._apply_styles()

    def _init_menu_bar(self):
        """Crea la barra dei menu con la voce 'File', 'Template' e 'Opzioni'."""
        menu_bar = self.menuBar()

        # ======== Menu 'File' ======== 
        file_menu = menu_bar.addMenu("&File")

        # Azione segnaposto: Esci
        exit_action = QAction("E&sci", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        # altre azioni segnaposto se necessario
        # es... file_menu.addAction(QAction("Nuovo Progetto...", self))

        # ======== Menu 'Template' ========
        template_menu = menu_bar.addMenu("&Template")
        
        # Gruppo esclusivo affinché solo un'opzione possa essere spuntata alla volta
        template_group = QActionGroup(self)
        template_group.setExclusive(True)
        
        # Azioni Checkable e le aggiungiamo al gruppo
        act_flow = QAction("Flow Chart", self)
        act_flow.setCheckable(True)
        act_flow.triggered.connect(lambda: self.switch_template(0))
        template_group.addAction(act_flow)
        
        act_dir = QAction("Direct Graph", self)
        act_dir.setCheckable(True)
        act_dir.triggered.connect(lambda: self.switch_template(1))
        template_group.addAction(act_dir)
        # Impostiamo Direct Graph come già spuntato all'avvio (essendo l'indice 1 di default)
        act_dir.setChecked(True)
        
        act_undir = QAction("Undirect Graph", self)
        act_undir.setCheckable(True)
        act_undir.triggered.connect(lambda: self.switch_template(2))
        template_group.addAction(act_undir)
        
        act_set = QAction("Set Theory", self)
        act_set.setCheckable(True)
        act_set.triggered.connect(lambda: self.switch_template(3))
        template_group.addAction(act_set)

        # Aggiungiamo le azioni al menu visivo
        template_menu.addActions([act_flow, act_dir, act_undir, act_set])

        # ======== Menu 'Tattile' ========
        tactile_menu = menu_bar.addMenu("&Tattile")
        act_calibrate = QAction("Calibrazione Sensore", self)
        act_calibrate.triggered.connect(self.open_calibration_window)
        tactile_menu.addAction(act_calibrate)

        act_read = QAction("Lettura Grafo Tattile", self)
        act_read.triggered.connect(self.open_reading_window)
        tactile_menu.addAction(act_read)

        # ======== Menu 'Opzioni' ========
        options_menu = menu_bar.addMenu("&Opzioni")
        
        act_api_key = QAction("API Key", self)
        act_api_key.triggered.connect(self._apri_impostazioni_api)
        options_menu.addAction(act_api_key)

        # ---- Modalità Debug -----
        act_debug_mode = QAction("Modalità Debug", self)
        act_debug_mode.setCheckable(True)
        # Imposta la spunta iniziale leggendo il valore di default in config.py
        act_debug_mode.setChecked(config.DEBUG_MODE) 
        # Collega il click alla funzione che cambierà lo stato
        act_debug_mode.triggered.connect(self._toggle_debug_mode) 
        options_menu.addAction(act_debug_mode)
        
    def open_calibration_window(self):
        """Apre la finestra di calibrazione del sensore."""
        from src.ui.calibration_window import CalibrationWindow
        # Passiamo l'istanza del lettore del sensore alla finestra di calibrazione
        self.calibration_window = CalibrationWindow()
        self.calibration_window.show()

    def open_reading_window(self):
        """Apre la finestra di lettura del grafo tattile."""
        from src.ui.hapticReader_window import HapticReaderWindow
        # Passiamo l'istanza del lettore del sensore alla finestra di lettura
        self.haptic_reader_window = HapticReaderWindow()
        self.haptic_reader_window.show()

    def _init_central_widget(self):
        """Inizializza il widget centrale e il layout principale."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.main_layout = QHBoxLayout(central_widget)
        # Aggiungi un po' di padding generale
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        self.main_layout.setSpacing(20)

    def _setup_layout(self):
        """Costruisce le colonne sinistra (immagine) e destra (prompt) come nello schizzo."""
        
        """Costruisce le colonne sinistra (immagine) e destra (prompt) come nello schizzo."""
        
        # --- COLONNA SINISTRA (Immagine) ---
        self.left_col_layout = QVBoxLayout()
        self.main_layout.addLayout(self.left_col_layout, stretch=1)

        # --- Box di preview per l'immagine ---
        # Aggiornato il testo per spiegare entrambe le interazioni
        self.img_preview_label = ImageDropLabel("PREVIEW IMG\n\n(Clicca qui o trascina un'immagine)")
        self.img_preview_label.setObjectName("img_preview")
        self.img_preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.img_preview_label.setMinimumSize(400, 300)
        self.img_preview_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        # Colleghiamo sia il drop che il click ai rispettivi metodi
        self.img_preview_label.imageDropped.connect(self._process_image_file)
        self.img_preview_label.clicked.connect(self.handle_choose_file)
        
        self.left_col_layout.addWidget(self.img_preview_label, stretch=1)


        # --- COLONNA DESTRA (Prompt Dinamico) ---
        self.right_col_layout = QVBoxLayout()
        self.main_layout.addLayout(self.right_col_layout, stretch=1)

        # Usiamo QStackedWidget per i layout scambiabili
        self.stacked_widget = QStackedWidget()
        
        # Creiamo i 4 pannelli (l'ordine di inserimento definisce l'indice: 0, 1, 2, 3)
        self.panel_flow = FlowChartPanel()                      # Indice 0
        self.panel_dir = GraphFormPanel(is_directed=True)       # Indice 1
        self.panel_undir = GraphFormPanel(is_directed=False)    # Indice 2
        self.panel_set = SetTheoryPanel()                       # Indice 3
        
        self.stacked_widget.addWidget(self.panel_flow)
        self.stacked_widget.addWidget(self.panel_dir)
        self.stacked_widget.addWidget(self.panel_undir)
        self.stacked_widget.addWidget(self.panel_set)

        #Direct Graph come default (Indice 1)
        self.stacked_widget.setCurrentIndex(1)
        
        self.right_col_layout.addWidget(self.stacked_widget, stretch=1)

        # --- Console di output/log in sola lettura ---
        self.console_output = QTextEdit()
        self.console_output.setReadOnly(True)  # L'utente non può scriverci dentro
        self.console_output.setMaximumHeight(100) # massimo spazio occupato
        self.console_output.setStyleSheet("background-color: rgba(var(#f0f0f0),0.5); color: rgb(255,255,255); font-family: monospace;")
        self.console_output.setPlaceholderText("Qui compariranno i log di sistema e i risultati.")
        
        self.right_col_layout.addWidget(self.console_output)

        # 2. Pulsante sottostante di invio in basso a destra con icona
        # Usiamo un layout orizzontale per posizionarlo a destra
        self.send_btn_layout = QHBoxLayout()
        self.right_col_layout.addLayout(self.send_btn_layout)

        # Aggiungi uno spaziatore a sinistra per spingere il pulsante a destra
        self.send_btn_layout.addStretch()

        # Pulsante di invio con icona standard di sistema
        self.send_btn = QPushButton()
        self.send_btn.setToolTip("Invia a Gemini")
        self.send_btn.setMinimumSize(60, 40)
        # Usiamo un'icona standard di sistema per "Invia" (o simile, come "Applica")
        # Puoi sostituirla con un'icona personalizzata in seguito
        #icon = self.style().standardIcon(QStyle.StandardPixmap.SP_DialogApplyButton)
        # Un'icona più specifica se disponibile a tema: 
        icon = self.style().standardIcon(QStyle.StandardPixmap.SP_ArrowRight)
        self.send_btn.setIcon(icon)
        self.send_btn.setIconSize(self.send_btn.sizeHint().expandedTo(self.send_btn.minimumSize()))
        self.send_btn.clicked.connect(self.handle_send_to_gemini)
        self.send_btn_layout.addWidget(self.send_btn)
    
    def switch_template(self, index):
        """Cambia il pannello visibile in base alla scelta del menu."""
        self.stacked_widget.setCurrentIndex(index)

    def _apply_styles(self):
        """Applica un foglio di stile CSS per definire l'aspetto dei placeholder."""
        # Un semplice stile per rendere i segnaposto visibili e simili allo schizzo
        style_sheet = """
            #img_preview {
                border: 2px dashed #999;
                color: #777;
                font-size: 16px;
                font-weight: bold;
                background-color: #f5f5f5;
                margin-bottom: 10px;
            }
            #prompt_text {
                border: 1px solid #ccc;
                font-family: 'Consolas', 'Monaco', monospace; /* Stile "codice" per prompt */
                font-size: 14px;
                background-color: #fafafa;
                padding: 10px;
            }
            QPushButton {
                font-size: 14px;
                border-radius: 4px;
                border: 1px solid #aaa;
                background-color: #e1e1e1;
                color: #333;
                padding: 5px 15px;
            }
            QPushButton:hover {
                background-color: #dcdcdc;
            }
            QPushButton:pressed {
                background-color: #c1c1c1;
            }
        """
        self.setStyleSheet(style_sheet)

    # --- Gestori degli Eventi (Slots) ---

    def handle_choose_file(self):
        """Apre un dialogo per scegliere un file immagine e lo visualizza."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Scegli un'immagine per lo schema", "", "Immagini (*.png *.jpg *.jpeg *.bmp)"
        )
        if file_path:
            self._process_image_file(file_path)

    def _process_image_file(self, file_path):
        """Elabora il file immagine (da pulsante o da drop) e lo mostra nella UI."""
        self.current_image_path = file_path
        
        # Carica e scala l'immagine per la preview
        pixmap = load_and_scale_image(
            file_path, 
            self.img_preview_label.width(), 
            self.img_preview_label.height()
        )
        
        if pixmap:
            self.img_preview_label.setPixmap(pixmap)
            # Rimuoviamo il testo "PREVIEW IMG..." o mostriamo un errore invisibile
        else:
            self.img_preview_label.setText("Errore nel caricamento dell'immagine")
            self.current_image_path = None

    def handle_send_to_gemini(self):
        image_path = self.current_image_path
        if not image_path:
            self.console_output.append(">> ERRORE: Nessuna immagine selezionata. Scegli un file prima di inviare.")
            return
        if not config.GEMINI_API_KEY and not config.DEBUG_MODE:
            self.console_output.append(">> ERRORE: API Key di Gemini non configurata. Inseriscila nelle Opzioni.")
            return

        self.console_output.clear()
        # Disabilita il pulsante per evitare doppi invii
        self.send_btn.setEnabled(False)
        
        # Chiediamo al pannello attualmente visibile
        # di restituirci l'oggetto Prompt con tutti i dati già compilati
        active_panel = self.stacked_widget.currentWidget()
        prompt_obj = active_panel.get_prompt_object()

        # Creiamo il worker e lo colleghiamo ai metodi della UI
        self.worker = GeminiWorker(image_path, prompt_obj.get_phase_1(), prompt_obj.get_phase_2())

        self.worker.progress.connect(self.update_ui_progress, type=Qt.ConnectionType.UniqueConnection)
        self.worker.finished.connect(self.handle_generation_success, type=Qt.ConnectionType.UniqueConnection)
        self.worker.error.connect(self.handle_generation_error, type=Qt.ConnectionType.UniqueConnection)

        # Avvia il processo in background
        self.worker.start()

    def _apri_impostazioni_api(self):
        """Apre un QDialog modale per inserire o modificare l'API Key di Gemini."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Impostazione API Key")
        dialog.resize(450, 180)
        dialog.setModal(True) # Blocca la finestra sottostante finché non si chiude

        layout = QVBoxLayout(dialog)

        # --- Testo descrittivo con Link cliccabile (grazie al formato RichText) ---
        testo_html = (
            "<div align='center'>"
            "Incolla la tua chiave di Gemini, se non ne sei in possesso,<br>"
            "puoi prenderla da qui:<br>"
            "<a href='https://aistudio.google.com/app/api-keys'>https://aistudio.google.com/app/api-keys</a>"
            "</div>"
        )
        lbl_info = QLabel(testo_html)
        lbl_info.setOpenExternalLinks(True) # Permette il click diretto sul link
        lbl_info.setTextFormat(Qt.TextFormat.RichText)
        lbl_info.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)
        layout.addWidget(lbl_info)

        # --- Campo di input per la chiave ---
        entry_chiave = QLineEdit()
        entry_chiave.setPlaceholderText("Inserisci la tua API Key...")
        # Usa EchoMode se in futuro vuoi nasconderla stile password (entry_chiave.setEchoMode(QLineEdit.EchoMode.Password))
        layout.addWidget(entry_chiave)

        # --- Lettura pre-caricamento dal file .env ---
        env_path = os.path.join(os.getcwd(), ".env")
        if os.path.exists(env_path):
            with open(env_path, "r") as f:
                for linea in f:
                    if linea.startswith("GEMINI_API_KEY="):
                        chiave_attuale = linea.strip().split("=", 1)[1]
                        entry_chiave.setText(chiave_attuale)

        # --- Pulsante Salva e sua logica ---
        btn_salva = QPushButton("Salva")
        btn_salva.setMinimumHeight(35)
        layout.addWidget(btn_salva)

        def salva_chiave():
            nuova_chiave = entry_chiave.text().strip()
            linee = []
            
            # Legge il file esistente per non sovrascrivere OPENAI_API_KEY
            if os.path.exists(env_path):
                with open(env_path, "r") as f:
                    linee = f.readlines()
            
            chiave_aggiornata = False
            for i, linea in enumerate(linee):
                if linea.startswith("GEMINI_API_KEY="):
                    linee[i] = f"GEMINI_API_KEY={nuova_chiave}\n"
                    chiave_aggiornata = True
                    break
            
            if not chiave_aggiornata:
                linee.append(f"GEMINI_API_KEY={nuova_chiave}\n")
                
            with open(env_path, "w") as f:
                f.writelines(linee)
                
            QMessageBox.information(dialog, "Successo", "API Key salvata correttamente nel file .env!")
            dialog.accept() # Chiude il QDialog con successo

        btn_salva.clicked.connect(salva_chiave)

        # Mostra il dialogo
        dialog.exec()

    def update_ui_progress(self, message):
        """Aggiorna la console di output con lo stato attuale."""
        # Usiamo append() invece di setPlainText() per mantenere lo storico dei messaggi
        self.console_output.append(f"> {message}")

    def handle_generation_success(self, filepath):
        """Chiamato quando il file .scad è stato creato con successo."""
        self.send_btn.setEnabled(True)
        
        success_msg = (
            "\n\n"+
            ">> ELABORAZIONE COMPLETATA!\n\t"
            f"File OpenSCAD generato in:\n{filepath}\n"
        )
        self.console_output.append(success_msg)
        self._cleanup_worker()

    def handle_generation_error(self, error_message):
        """Chiamato se qualcosa va storto con l'API o il processo."""
        self.send_btn.setEnabled(True)
        
        error_msg = (
            "\n" + ">> ERRORE CRITICO:\n"
            f"{error_message}\n"
            "Verifica la connessione o la chiave API."
        )
        self.console_output.append(error_msg)
        self._cleanup_worker()

    def _toggle_debug_mode(self, checked):
        """Attiva o disattiva la modalità di debug a runtime."""
        config.DEBUG_MODE = checked
        
        # Diamo un feedback visivo all'utente nella console
        stato = "ATTIVATA (Verrà usato il TestClient)" if checked else "DISATTIVATA (Verranno fatte chiamate API reali)"
        self.console_output.append(f"\n>> Modalità Debug: {stato}")

    def _cleanup_worker(self):
        """Forza la distruzione del thread sganciandolo dalla memoria."""
        if hasattr(self, 'worker') and self.worker is not None:
            self.worker.deleteLater()
            self.worker = None  #taglia il riferimento e forza il __del__