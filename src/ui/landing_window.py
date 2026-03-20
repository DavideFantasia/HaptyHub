import sys
import os
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QTextEdit, QPushButton, QMenuBar, QMenu, 
                             QFileDialog, QFrame, QSizePolicy, QStyle)
from PyQt6.QtGui import QAction
from PyQt6.QtCore import Qt, QThread, pyqtSignal

from src.api_client import GeminiClient
import time

# Importa la configurazione e gli helper
import config
from src.utils.image_helper import load_and_scale_image

# --- Worker Thread per l'integrazione API con Gemini ---
class GeminiWorker(QThread):
    # Segnali per comunicare con la UI (Thread principale)
    progress = pyqtSignal(str)   # Per aggiornare lo stato (es. "Fase 1 in corso...")
    finished = pyqtSignal(str)   # Quando ha generato il file .scad
    error = pyqtSignal(str)      # In caso di problemi di rete

    def __init__(self, image_path, prompt_fase_1, prompt_fase_2):
        super().__init__()
        self.image_path = image_path
        self.prompt_fase_1 = prompt_fase_1
        self.prompt_fase_2 = prompt_fase_2
        self.client = GeminiClient()

    def run(self):
        try:
            # --- FASE 1: Immagine -> Testo ---
            self.progress.emit("Fase 1: Analisi dell'immagine in corso...")
            descrizione = self.client.analyze_image(self.image_path, self.prompt_fase_1)
            
            # --- FASE 2: Testo -> OpenSCAD ---
            self.progress.emit("Fase 2: Generazione del modello 3D (OpenSCAD)...")
            scad_code = self.client.generate_scad(descrizione, self.prompt_fase_2)
            
            # Salviamo il file in locale
            timestamp = int(time.time())
            filepath = os.path.join(config.OUTPUT_DIR, f"modello_{timestamp}.scad")
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(scad_code)
                
            # Comunichiamo alla UI che abbiamo finito, passando il percorso del file
            self.finished.emit(filepath)
            
        except Exception as e:
            self.error.emit(f"Errore API: {str(e)}")

class LandingWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("HaptiGraph")
        self.resize(1000, 700) # Una dimensione iniziale decente

        self.prompt_phase_1 = config.PROMPT_PHASE_1
        self.prompt_phase_2 = config.PROMPT_PHASE_2

        # --- Variabili di stato interne ---
        self.current_image_path = None

        # --- Inizializzazione ---
        self._init_menu_bar()
        self._init_central_widget()
        self._setup_layout()
        self._apply_styles()

    def _init_menu_bar(self):
        """Crea la barra dei menu con la voce 'File'."""
        menu_bar = self.menuBar()

        # Menu 'File'
        file_menu = menu_bar.addMenu("&File")

        # Azione segnaposto: Esci
        exit_action = QAction("E&sci", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Aggiungi qui altre azioni segnaposto se necessario
        # file_menu.addAction(QAction("Nuovo Progetto...", self))

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
        
        # --- COLONNA SINISTRA (Immagine) ---
        self.left_col_layout = QVBoxLayout()
        self.main_layout.addLayout(self.left_col_layout, stretch=1) # stretch=1 dà peso uguale alle colonne

        # 1. Box di preview per l'immagine
        self.img_preview_label = QLabel("PREVIEW IMG")
        self.img_preview_label.setObjectName("img_preview") # Per lo styling CSS
        self.img_preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.img_preview_label.setMinimumSize(400, 300)
        # Assicurati che si espanda ma mantenga le proporzioni
        self.img_preview_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.left_col_layout.addWidget(self.img_preview_label, stretch=1)

        # 2. Pulsante sottostante per la scelta dell'immagine
        self.choose_file_btn = QPushButton("choose a file")
        self.choose_file_btn.setMinimumHeight(40)
        self.choose_file_btn.clicked.connect(self.handle_choose_file)
        self.left_col_layout.addWidget(self.choose_file_btn)


        # --- COLONNA DESTRA (Prompt) ---
        self.right_col_layout = QVBoxLayout()
        self.main_layout.addLayout(self.right_col_layout, stretch=1)

        # 1. Box di testo modificabile con del testo già presente
        self.prompt_text_edit = QTextEdit()
        self.prompt_text_edit.setObjectName("prompt_text") # Per lo styling CSS
        self.prompt_text_edit.setPlaceholderText("Inserisci qui la tua descrizione...")
        # Leggi il testo predefinito per il prompt
        self.prompt_text_edit.setPlainText(self.prompt_phase_1)
        self.right_col_layout.addWidget(self.prompt_text_edit, stretch=1)

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
        file_path, _ = QFileDialog.getOpenFileName(self, "Scegli un'immagine per lo schema", 
                                                   "", "Immagini (*.png *.jpg *.jpeg *.bmp)")
        if file_path:
            # Salva il path per l'uso futuro (invio API)
            self.current_image_path = file_path
            
            # Carica e scala l'immagine per la preview
            pixmap = load_and_scale_image(file_path, 
                                          self.img_preview_label.width(), 
                                          self.img_preview_label.height())
            if pixmap:
                # Imposta l'immagine e rimuovi il testo segnaposto
                self.img_preview_label.setPixmap(pixmap)
                self.img_preview_label.setText("") # Rimuovi testo se c'è
            else:
                self.img_preview_label.setText("Errore nel caricamento dell'immagine")
                self.current_image_path = None

    def handle_send_to_gemini(self):
        prompt_text = self.prompt_text_edit.toPlainText()
        image_path = self.current_image_path

        if not image_path:
            self.prompt_text_edit.setPlainText("Errore: Seleziona un'immagine prima di inviare!")
            return

        # Disabilita il pulsante per evitare doppi invii
        self.send_btn.setEnabled(False)
        self.prompt_text_edit.setPlainText("Inizializzazione connessione a Gemini...")

        # Creiamo il worker e lo colleghiamo ai metodi della UI
        self.worker = GeminiWorker(image_path, self.prompt_phase_1, self.prompt_phase_2)
        self.worker.progress.connect(self.update_ui_progress)
        self.worker.finished.connect(self.handle_generation_success)
        self.worker.error.connect(self.handle_generation_error)
        
        # Avvia il processo in background
        self.worker.start()

    # --- Nuovi metodi da aggiungere in LandingWindow ---

    def update_ui_progress(self, message):
        """Aggiorna la casella di testo con lo stato attuale."""
        self.prompt_text_edit.setPlainText(message)

    def handle_generation_success(self, filepath):
        """Chiamato quando il file .scad è stato creato."""
        self.send_btn.setEnabled(True)
        # TODO: Sostiture la casella di testo con il visualizzatore 3D
        success_msg = f"SUCCESSO!\nFile OpenSCAD generato e salvato in:\n{filepath}"
        self.prompt_text_edit.setPlainText(success_msg)

    def handle_generation_error(self, error_message):
        """Chiamato se qualcosa va storto con l'API."""
        self.send_btn.setEnabled(True)
        self.prompt_text_edit.setPlainText(f"Si è verificato un errore:\n\t{error_message}")