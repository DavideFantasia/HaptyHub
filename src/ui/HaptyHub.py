from PyQt6.QtWidgets import (QMainWindow, QWidget, QGridLayout, 
                             QPushButton, QVBoxLayout, QHBoxLayout, QLabel, QFrame)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QFont, QIcon

import os, config

class NavCard(QFrame):
    """Widget personalizzato che rappresenta una 'Card' di navigazione."""
    def __init__(self, title, description, icon_path, callback):
        super().__init__()
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setObjectName("navCard")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedSize(240, 180)
        
        # Layout della card
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)

        # Icona
        icon_label = QLabel()
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        if icon_path:
            # Creiamo l'oggetto QIcon
            icon = QIcon(icon_path)
            # Trasformiamo l'icona in un Pixmap della dimensione desiderata
            pixmap = icon.pixmap(QSize(64, 64))
            icon_label.setPixmap(pixmap)
        layout.addWidget(icon_label)

        # Titolo
        title_label = QLabel(title)
        title_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        # Descrizione
        desc_label = QLabel(description)
        desc_label.setWordWrap(True)
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc_label.setStyleSheet("color: #666;")
        layout.addWidget(desc_label)

        # Rendere la card cliccabile
        self.mouseReleaseEvent = lambda e: callback()

class HaptyHub(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("HaptyHub")
        self.resize(900, 600)

        # Widget centrale e layout a griglia
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        header = QLabel("Benvenuto in HaptyHub")
        header.setFont(QFont("Arial", 22, QFont.Weight.Bold))
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(header)

        grid = QGridLayout()
        grid.setSpacing(20)

        main_layout.addStretch(1)

        h_layout = QHBoxLayout()
        h_layout.addStretch(1)    # Molla invisibile a SINISTRA
        h_layout.addLayout(grid)  # La nostra griglia compatta al centro
        h_layout.addStretch(1)    # Molla invisibile a DESTRA
        
        main_layout.addLayout(h_layout)

        main_layout.addStretch(1)

        # Definizione delle 4 sezioni
        sections = [
            ("Modello 3D (Android)", "Genera modelli tattili ottimizzati per tablet.", os.path.join(config.ASSET_DIR, "android_icon.png"), self.open_android_model),
            ("Modello 3D (Circuito)", "Crea modelli tattili pronti alla stampa.", os.path.join(config.ASSET_DIR, "circuit_icon.png"), self.open_circuit_model),
            ("Lettura Sensore", "Avvia la lettura interattiva da circuito con feedback vocale.", os.path.join(config.ASSET_DIR, "reader_icon.png"), self.open_reader),
            ("Calibrazione", "Associa i nodi fisici alle impronte del sensore.", os.path.join(config.ASSET_DIR, "calibration_icon.png"), self.open_calibration)
        ]

        # Posizionamento nella griglia 2x2
        for i, (title, desc, icon_path,callback) in enumerate(sections):
            card = NavCard(title, desc, icon_path, callback)
            grid.addWidget(card, i // 2, i % 2, alignment=Qt.AlignmentFlag.AlignCenter)

        # Applicazione di uno stile moderno tramite QSS
        self.setStyleSheet("""
            #navCard {
                background-color: #ffffff;
                border: 2px solid #e0e0e0;
                border-radius: 15px;
            }
            #navCard:hover {
                background-color: #f8f9fa;
                border: 2px solid #3498db;
            }
        """)

    # --- Metodi per aprire le finestre ---
    def open_android_model(self):
        print("Apertura finestra Android...")
        # self.android_win = AndroidModelWindow(...)
        # self.android_win.show()

    def open_circuit_model(self):
        from src.ui.basic_haptic_modeler import LandingWindow # La rinomineremo poi
        self.circuit_win = LandingWindow()
        self.circuit_win.show()

    def open_reader(self):
        from src.ui.hapticReader_window import HapticReaderWindow
        self.read_win = HapticReaderWindow()
        self.read_win.show()

    def open_calibration(self):
        from src.ui.calibration_window import CalibrationWindow
        self.calib_win = CalibrationWindow()
        self.calib_win.show()