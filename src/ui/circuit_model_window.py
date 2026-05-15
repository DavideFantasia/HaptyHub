import os
import json
import subprocess
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QTextEdit, QPushButton, QMenuBar, QMenu, 
                             QFileDialog, QFrame, QSizePolicy, QStyle, QStackedWidget,
                             QDialog, QLineEdit, QMessageBox)
from PyQt6.QtGui import QAction, QActionGroup
from PyQt6.QtCore import Qt, pyqtSignal

import config
from src.utils.image_helper import load_and_scale_image
from src.utils.gemini_worker import GeminiWorker
from src.utils.stl_viewer import STLViewerWidget
from src.ui.panels import ELK_FlowChartPanel, ELK_GraphPanel

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

# --- Finestra Principale Circuito (NanoVNA) ---
class CircuitModelWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Generatore Modello 3D (Circuito / NanoVNA)")
        self.resize(1000, 700)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        
        self.current_image_path = None
        
        self._init_menu_bar()
        self._init_central_widget()
        self._setup_layout()
        self._apply_styles()

    def _init_menu_bar(self):
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu("&File")
        exit_action = QAction("E&sci", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

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

        template_menu.addActions([act_flow, act_dir, act_undir])

        options_menu = menu_bar.addMenu("&Opzioni")
        act_api_key = QAction("API Key", self)
        act_api_key.triggered.connect(self._apri_impostazioni_api)
        options_menu.addAction(act_api_key)

        act_debug_mode = QAction("Modalità Debug", self)
        act_debug_mode.setCheckable(True)
        act_debug_mode.setChecked(config.DEBUG_MODE)
        act_debug_mode.triggered.connect(self._toggle_debug_mode)
        options_menu.addAction(act_debug_mode)

    def _init_central_widget(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.main_layout = QHBoxLayout(central_widget)
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        self.main_layout.setSpacing(20)

    def _setup_layout(self):
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

        self.right_col_layout = QVBoxLayout()
        self.main_layout.addLayout(self.right_col_layout, stretch=1)

        self.stacked_widget = QStackedWidget()
        self.panel_flow = ELK_FlowChartPanel()
        self.panel_dir = ELK_GraphPanel()
        self.panel_undir = ELK_GraphPanel()
        
        self.stacked_widget.addWidget(self.panel_flow)
        self.stacked_widget.addWidget(self.panel_dir)
        self.stacked_widget.addWidget(self.panel_undir)
        self.stacked_widget.setCurrentIndex(1)
        self.right_col_layout.addWidget(self.stacked_widget, stretch=1)

        self.viewer_3d = STLViewerWidget()
        self.viewer_3d.setMinimumHeight(300)
        self.right_col_layout.addWidget(self.viewer_3d)

        self.console_output = QTextEdit()
        self.console_output.setReadOnly(True)
        self.console_output.setMaximumHeight(150)
        self.console_output.setStyleSheet("background-color: rgba(var(#f0f0f0),0.5); color: rgb(255,255,255); font-family: monospace;")
        self.console_output.setPlaceholderText("Qui compariranno i log della pipeline Circuito ELK.")
        self.right_col_layout.addWidget(self.console_output)

        self.send_btn_layout = QHBoxLayout()
        self.right_col_layout.addLayout(self.send_btn_layout)
        self.send_btn_layout.addStretch()

        self.send_btn = QPushButton(" Esegui Pipeline Circuito")
        self.send_btn.setMinimumSize(160, 40)
        icon = self.style().standardIcon(QStyle.StandardPixmap.SP_ArrowRight)
        self.send_btn.setIcon(icon)
        self.send_btn.clicked.connect(self.handle_send_to_gemini)
        self.send_btn_layout.addWidget(self.send_btn)

    def switch_template(self, index):
        self.stacked_widget.setCurrentIndex(index)

    def _apply_styles(self):
        style_sheet = """
            #img_preview { border: 2px dashed #999; color: #777; font-size: 16px; font-weight: bold; background-color: #f5f5f5; margin-bottom: 10px; }
            QPushButton { font-size: 14px; border-radius: 4px; border: 1px solid #aaa; background-color: #e1e1e1; color: #333; padding: 5px 15px; }
            QPushButton:hover { background-color: #dcdcdc; }
            QPushButton:pressed { background-color: #c1c1c1; }
        """
        self.setStyleSheet(style_sheet)

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

    def handle_send_to_gemini(self):
        if not self.current_image_path:
            self.console_output.append(">> ERRORE: Seleziona un'immagine prima di inviare.")
            return

        self.console_output.clear()
        self.send_btn.setEnabled(False)
        
        active_panel = self.stacked_widget.currentWidget()
        prompt_obj = active_panel.get_prompt_object()

        self.worker = GeminiWorker(self.current_image_path, prompt_obj.get_phase_1(), prompt_obj.get_phase_2())
        self.worker.progress.connect(self.update_ui_progress, type=Qt.ConnectionType.UniqueConnection)
        self.worker.finished.connect(self.process_elk_pipeline, type=Qt.ConnectionType.UniqueConnection)
        self.worker.error.connect(self.handle_generation_error, type=Qt.ConnectionType.UniqueConnection)
        self.worker.start()

    def process_elk_pipeline(self, raw_json):
        try:
            self.update_ui_progress("Dati ricevuti da Gemini. Preparazione modello Circuito...")
            clean_json = raw_json.replace("```json", "").replace("```", "").strip()
            graph_data = json.loads(clean_json)

            # (ATTENZIONE: Assicurati di importare CompilerWorker in cima al file!)
            from src.utils.stl_compiler import STLCompilerWorker # Adatta il nome del file se diverso

            # Istanzia il worker passandogli il generatore NanoVNA e il prefisso "circuit_model"
            self.STLcompiler_worker = STLCompilerWorker(
                graph_data=graph_data, 
                generator_module="src.utils.json_to_scad_NanoVNA", 
                output_prefix="circuit_model"
            )
            self.STLcompiler_worker.progress.connect(self.update_ui_progress)
            self.STLcompiler_worker.finished.connect(self.on_STLcompilation_finished)
            self.STLcompiler_worker.error.connect(self.handle_generation_error)
            self.STLcompiler_worker.start()
            
        except json.JSONDecodeError:
            self.handle_generation_error("Gemini non ha restituito un JSON valido.")
        except Exception as e:
            self.handle_generation_error(f"Errore nella generazione: {str(e)}")

    # -- Aggiungi questo metodo ricevitore --
    def on_STLcompilation_finished(self, stl_path):
        """Funzione chiamata quando STLCompilerWorker ha finito di generare l'STL."""
        self.update_ui_progress(f"COMPLETATO! Modello Circuito salvato in:\n{stl_path}")
        self.viewer_3d.load_stl(stl_path)
        
        self.send_btn.setEnabled(True)
        self._cleanup_worker()

    def update_ui_progress(self, message):
        self.console_output.append(f"> {message}")

    def handle_generation_error(self, error_message):
        self.send_btn.setEnabled(True)
        self.console_output.append(f"\n>> ERRORE CRITICO:\n{error_message}")
        self._cleanup_worker()

    def _apri_impostazioni_api(self):
        # ... (Stesso codice dell'impostazione API della versione Android)
        dialog = QDialog(self)
        dialog.setWindowTitle("Impostazione API Key")
        dialog.resize(450, 180)
        dialog.setModal(True)
        layout = QVBoxLayout(dialog)
        testo_html = "<div align='center'>Incolla la tua chiave di Gemini:<br><a href='https://aistudio.google.com/app/api-keys'>https://aistudio.google.com/app/api-keys</a></div>"
        lbl_info = QLabel(testo_html)
        lbl_info.setOpenExternalLinks(True)
        lbl_info.setTextFormat(Qt.TextFormat.RichText)
        lbl_info.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)
        layout.addWidget(lbl_info)
        entry_chiave = QLineEdit()
        entry_chiave.setPlaceholderText("Inserisci API Key...")
        layout.addWidget(entry_chiave)
        
        env_path = os.path.join(os.getcwd(), ".env")
        if os.path.exists(env_path):
            with open(env_path, "r") as f:
                for linea in f:
                    if linea.startswith("GEMINI_API_KEY="):
                        entry_chiave.setText(linea.strip().split("=", 1)[1])
        
        btn_salva = QPushButton("Salva")
        layout.addWidget(btn_salva)
        def salva_chiave():
            nuova_chiave = entry_chiave.text().strip()
            linee = []
            if os.path.exists(env_path):
                with open(env_path, "r") as f: linee = f.readlines()
            agg = False
            for i, linea in enumerate(linee):
                if linea.startswith("GEMINI_API_KEY="):
                    linee[i] = f"GEMINI_API_KEY={nuova_chiave}\n"
                    agg = True
                    break
            if not agg: linee.append(f"GEMINI_API_KEY={nuova_chiave}\n")
            with open(env_path, "w") as f: f.writelines(linee)
            QMessageBox.information(dialog, "Successo", "API Key salvata!")
            dialog.accept()
        btn_salva.clicked.connect(salva_chiave)
        dialog.exec()

    def _toggle_debug_mode(self, checked):
        config.DEBUG_MODE = checked
        stato = "ATTIVATA (TestClient)" if checked else "DISATTIVATA (Chiamate Reali)"
        self.console_output.append(f"\n>> Modalità Debug: {stato}")

    def _cleanup_worker(self):
        if hasattr(self, 'worker') and self.worker is not None:
            try:
                self.worker.quit()
                self.worker.deleteLater()
                self.worker = None
            except Exception as e:
                pass
                
        # Pulizia STLCompilerWorker
        if hasattr(self, 'STLcompiler_worker') and self.STLcompiler_worker is not None:
            try:
                self.STLcompiler_worker.quit()
                self.STLcompiler_worker.deleteLater()
                self.STLcompiler_worker = None
            except Exception as e:
                pass

    def closeEvent(self, event):
        print("Chiusura finestra: avvio procedura di scaricamento GPU...")
        # 1. Chiama il cleanup del visualizzatore
        if hasattr(self, 'viewer_3d'):
            self.viewer_3d.cleanup()
        
        # 2. Imposta l'attributo per la distruzione immediata (se non lo hai già nell'init)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        
        # 3. Accetta l'evento
        event.accept()