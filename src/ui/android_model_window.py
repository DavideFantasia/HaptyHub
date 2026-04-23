import os
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QTextEdit, QPushButton, QMenuBar, QMenu, 
                             QFileDialog, QFrame, QSizePolicy, QStyle, QStackedWidget,
                             QDialog, QLineEdit, QMessageBox)
from PyQt6.QtGui import QAction, QActionGroup
from PyQt6.QtCore import Qt, pyqtSignal

from src.ui.panels import ELK_FlowChartPanel, ELK_GraphPanel

# Importa la configurazione e gli helper
import config, json, subprocess, time
from src.utils.image_helper import load_and_scale_image
from src.utils.gemini_worker import GeminiWorker
from src.utils.stl_viewer import STLViewerWidget

# --- Widget personalizzato per il drag and drop ---
class ImageDropLabel(QLabel):
    imageDropped = pyqtSignal(str)
    clicked = pyqtSignal()

    def __init__(self, text=""):
        super().__init__(text)
        self.setAcceptDrops(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            url = event.mimeData().urls()[0]
            if url.isLocalFile():
                ext = os.path.splitext(url.toLocalFile())[1].lower()
                if ext in ['.png', '.jpg', '.jpeg', '.bmp']:
                    event.acceptProposedAction()
                    self.setStyleSheet("border: 2px solid #4CAF50; background-color: #e8f5e9;")
                    return
        event.ignore()

    def dragLeaveEvent(self, event):
        self.setStyleSheet("") 

    def dropEvent(self, event):
        self.setStyleSheet("") 
        file_path = event.mimeData().urls()[0].toLocalFile()
        self.imageDropped.emit(file_path)

# --- Finestra Principale Android (Tablet) ---
class AndroidModelWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Generatore Modello 3D (Android / Tablet)")
        self.resize(1000, 700) 

        self.current_image_path = None

        self._init_menu_bar()
        self._init_central_widget()
        self._setup_layout()
        self._apply_styles()

    def _init_menu_bar(self):
        """Ricrea la barra dei menu uguale alla versione Circuito."""
        menu_bar = self.menuBar()

        # ======== Menu 'File' ======== 
        file_menu = menu_bar.addMenu("&File")
        exit_action = QAction("E&sci", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # ======== Menu 'Template' ========
        template_menu = menu_bar.addMenu("&Template")
        template_group = QActionGroup(self)
        template_group.setExclusive(True)
        
        act_flow = QAction("Flow Chart", self)
        act_flow.setCheckable(True)
        act_flow.triggered.connect(lambda: self.switch_template(0))
        template_group.addAction(act_flow)

        act_dir = QAction("Direct Graph", self)
        act_dir.setCheckable(True)
        act_dir.triggered.connect(lambda: self.switch_template(1))
        template_group.addAction(act_dir)
        act_dir.setChecked(True)
        
        act_undir = QAction("Undirect Graph", self)
        act_undir.setCheckable(True)
        act_undir.triggered.connect(lambda: self.switch_template(2))
        template_group.addAction(act_undir)
        '''
        act_set = QAction("Set Theory", self)
        act_set.setCheckable(True)
        act_set.triggered.connect(lambda: self.switch_template(3))
        template_group.addAction(act_set)

        template_menu.addActions([act_flow, act_dir, act_undir, act_set])
        '''
        template_menu.addActions([act_flow, act_dir, act_undir])
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

        act_debug_mode = QAction("Modalità Debug", self)
        act_debug_mode.setCheckable(True)
        act_debug_mode.setChecked(config.DEBUG_MODE) 
        act_debug_mode.triggered.connect(self._toggle_debug_mode) 
        options_menu.addAction(act_debug_mode)

    # --- Metodi di Navigazione ---
    def open_calibration_window(self):
        from src.ui.calibration_window import CalibrationWindow
        self.calibration_window = CalibrationWindow()
        self.calibration_window.show()

    def open_reading_window(self):
        from src.ui.hapticReader_window import HapticReaderWindow
        self.haptic_reader_window = HapticReaderWindow()
        self.haptic_reader_window.show()

    def _init_central_widget(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.main_layout = QHBoxLayout(central_widget)
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        self.main_layout.setSpacing(20)

    def _setup_layout(self):
        # --- COLONNA SINISTRA (Immagine) ---
        self.left_col_layout = QVBoxLayout()
        self.main_layout.addLayout(self.left_col_layout, stretch=1)

        self.img_preview_label = ImageDropLabel("PREVIEW IMG\n\n(Clicca qui o trascina un'immagine)")
        self.img_preview_label.setObjectName("img_preview")
        self.img_preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.img_preview_label.setMinimumSize(400, 300)
        self.img_preview_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        self.img_preview_label.imageDropped.connect(self._process_image_file)
        self.img_preview_label.clicked.connect(self.handle_choose_file)
        self.left_col_layout.addWidget(self.img_preview_label, stretch=1)

        # --- COLONNA DESTRA (Pannelli e Log) ---
        self.right_col_layout = QVBoxLayout()
        self.main_layout.addLayout(self.right_col_layout, stretch=1)

        self.stacked_widget = QStackedWidget()
        
        # NOTA: Per Android, questi pannelli dovrebbero restituire i nuovi "ElkTemplates" 
        # (quelli che hanno get_phase_2 = None) per avviare la pipeline corretta.
        self.panel_flow = ELK_FlowChartPanel()                   # Indice 0
        self.panel_dir = ELK_GraphPanel()                        # Indice 1
        self.panel_undir = ELK_GraphPanel()                      # Indice 2
        #self.panel_set = SetTheoryPanel()                       # Indice 3
        
        self.stacked_widget.addWidget(self.panel_flow)
        self.stacked_widget.addWidget(self.panel_dir)
        self.stacked_widget.addWidget(self.panel_undir)
        #self.stacked_widget.addWidget(self.panel_set)

        self.stacked_widget.setCurrentIndex(0)
        self.right_col_layout.addWidget(self.stacked_widget, stretch=1)

        # 2. IL VISUALIZZATORE 3D (al centro)
        self.viewer_3d = STLViewerWidget()
        self.viewer_3d.setMinimumHeight(300) # Dai un'altezza minima per non schiacciarlo
        self.right_col_layout.addWidget(self.viewer_3d)

        self.console_output = QTextEdit()
        self.console_output.setReadOnly(True) 
        self.console_output.setMaximumHeight(150)
        self.console_output.setStyleSheet("background-color: rgba(var(#f0f0f0),0.5); color: rgb(255,255,255); font-family: monospace;")
        self.console_output.setPlaceholderText("Qui compariranno i log della pipeline ELK.")
        self.right_col_layout.addWidget(self.console_output)

        self.send_btn_layout = QHBoxLayout()
        self.right_col_layout.addLayout(self.send_btn_layout)
        self.send_btn_layout.addStretch()

        self.send_btn = QPushButton(" Esegui Pipeline ELK")
        self.send_btn.setMinimumSize(140, 40)
        icon = self.style().standardIcon(QStyle.StandardPixmap.SP_ArrowRight)
        self.send_btn.setIcon(icon)
        self.send_btn.clicked.connect(self.handle_send_to_gemini)
        self.send_btn_layout.addWidget(self.send_btn)

    def switch_template(self, index):
        self.stacked_widget.setCurrentIndex(index)

    def _apply_styles(self):
        style_sheet = """
            #img_preview {
                border: 2px dashed #999;
                color: #777;
                font-size: 16px;
                font-weight: bold;
                background-color: #f5f5f5;
                margin-bottom: 10px;
            }
            QPushButton {
                font-size: 14px;
                border-radius: 4px;
                border: 1px solid #aaa;
                background-color: #e1e1e1;
                color: #333;
                padding: 5px 15px;
            }
            QPushButton:hover { background-color: #dcdcdc; }
            QPushButton:pressed { background-color: #c1c1c1; }
        """
        self.setStyleSheet(style_sheet)

    # --- File e Interazioni ---
    def handle_choose_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Scegli Immagine", "", "Immagini (*.png *.jpg *.jpeg *.bmp)")
        if file_path:
            self._process_image_file(file_path)

    def _process_image_file(self, file_path):
        self.current_image_path = file_path
        pixmap = load_and_scale_image(file_path, self.img_preview_label.width(), self.img_preview_label.height())
        if pixmap:
            self.img_preview_label.setPixmap(pixmap)
        else:
            self.img_preview_label.setText("Errore nel caricamento dell'immagine")
            self.current_image_path = None

    # --- PIPELINE ELK ---
    def handle_send_to_gemini(self):
        if not self.current_image_path:
            self.console_output.append(">> ERRORE: Seleziona un'immagine prima di inviare.")
            return

        self.console_output.clear()
        self.send_btn.setEnabled(False)
        
        active_panel = self.stacked_widget.currentWidget()
        prompt_obj = active_panel.get_prompt_object()

        # Il worker capirà automaticamente che è una pipeline a 1 fase 
        # perché prompt_obj.get_phase_2() restituirà None
        self.worker = GeminiWorker(self.current_image_path, prompt_obj.get_phase_1(), prompt_obj.get_phase_2())
        self.worker.progress.connect(self.update_ui_progress, type=Qt.ConnectionType.UniqueConnection)
        
        # Colleghiamo il 'finished' al nuovo gestore ELK
        self.worker.finished.connect(self.process_elk_pipeline, type=Qt.ConnectionType.UniqueConnection)
        self.worker.error.connect(self.handle_generation_error, type=Qt.ConnectionType.UniqueConnection)

        self.worker.start()

    def process_elk_pipeline(self, raw_json):
        """Cattura il JSON raw di Gemini e prosegue con ELK (Fase 2 e 3)."""
        try:
            self.update_ui_progress("Avvio motore grafico ELK (Node.js)...")
            
            # 1. Pulisce la risposta di Gemini
            clean_json = raw_json.replace("```json", "").replace("```", "").strip()
            graph_data = json.loads(clean_json)
            
            # 2. Salva il file temporaneo
            input_path = os.path.join(config.TEMP_DIR, "temp_graph.json")
            output_path = os.path.join(config.TEMP_DIR, "output_coordinates.json")
            with open(input_path, "w") as f:
                json.dump(graph_data, f)
            
            # 3. Esegue ELK (Javascript)
            cmd = ["node", "src/utils/run_elk.js", input_path, output_path]
            subprocess.run(cmd, check=True)

            # 4. Converte il risultato in OpenSCAD
            self.update_ui_progress("Conversione coordinate spaziali in modello 3D...")
            from src.utils.json_to_scad import json_to_scad
            
            # Assicurati che la cartella output esista
            os.makedirs(config.OUTPUT_DIR, exist_ok=True)
            scad_output = os.path.join(config.OUTPUT_DIR, "android_model.scad")
            
            json_to_scad(output_path, scad_output)
            
            self.update_ui_progress(f"COMPLETATO! Modello per Tablet salvato in:\n{scad_output}")

            # Compilazione in stl
            cmd = ["openscad", "-o", os.path.join(config.OUTPUT_DIR, "android_model.stl"), scad_output]
            subprocess.run(cmd, check=True)
            self.viewer_3d.load_stl(os.path.join(config.OUTPUT_DIR, "android_model.stl"))

            self.send_btn.setEnabled(True)
            self._cleanup_worker()
            
        except json.JSONDecodeError:
            self.handle_generation_error("Gemini non ha restituito un JSON valido.")
        except subprocess.CalledProcessError:
            self.handle_generation_error("Errore durante l'esecuzione del motore ELK (Node.js). Assicurati che Node sia installato e funzionante.")
        except Exception as e:
            self.handle_generation_error(f"Errore nella generazione ELK: {str(e)}")

    def update_ui_progress(self, message):
        self.console_output.append(f"> {message}")

    def handle_generation_error(self, error_message):
        self.send_btn.setEnabled(True)
        self.console_output.append(f"\n>> ERRORE CRITICO:\n{error_message}")
        self._cleanup_worker()

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

    def _toggle_debug_mode(self, checked):
        config.DEBUG_MODE = checked
        stato = "ATTIVATA (TestClient)" if checked else "DISATTIVATA (Chiamate Reali)"
        self.console_output.append(f"\n>> Modalità Debug: {stato}")

    def _cleanup_worker(self):
        if hasattr(self, 'worker') and self.worker is not None:
            self.worker.deleteLater()
            self.worker = None