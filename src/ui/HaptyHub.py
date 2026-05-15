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
        self.callback = callback

    # Sovrascriviamo l'evento del mouse per disabilitare la card e passare l'istanza
    def mouseReleaseEvent(self, event):
        # Eseguiamo solo se cliccato col tasto sinistro e se la card è attualmente abilitata
        if event.button() == Qt.MouseButton.LeftButton and self.isEnabled():
            self.setEnabled(False) # Disabilita all'istante per evitare doppi-click veloci
            self.callback(self)    # Passa l'istanza della card alla funzione ricevente

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
            ("Bassorilievo Semplice", "Crea modelli tattili base pronti alla stampa, senza interattività.", os.path.join(config.ASSET_DIR, "basrelief_icon.png"), self.open_basic_model),
            ("Lettura Sensore", "Avvia la lettura interattiva da circuito con feedback vocale.", os.path.join(config.ASSET_DIR, "reader_icon.png"), self.open_reader),
            ("Calibrazione", "Associa i nodi fisici alle impronte del sensore.", os.path.join(config.ASSET_DIR, "calibration_icon.png"), self.open_calibration)
        ]

        # Invece di una griglia, usiamo un layout verticale per contenere le due righe
        cards_v_layout = QVBoxLayout()
        cards_v_layout.setSpacing(20)

        # Creiamo un layout orizzontale per la prima riga (3 card)
        row1_layout = QHBoxLayout()
        row1_layout.setSpacing(20)
        row1_layout.setAlignment(Qt.AlignmentFlag.AlignCenter) # Centra le card nella riga!

        # Creiamo un layout orizzontale per la seconda riga (2 card)
        row2_layout = QHBoxLayout()
        row2_layout.setSpacing(20)
        row2_layout.setAlignment(Qt.AlignmentFlag.AlignCenter) # Centra le card nella riga!

        main_layout.addStretch(1)

        h_layout = QHBoxLayout()
        h_layout.addStretch(1)    # Molla invisibile a SINISTRA
        h_layout.addLayout(cards_v_layout)  # Il nostro nuovo contenitore verticale
        h_layout.addStretch(1)    # Molla invisibile a DESTRA
        
        main_layout.addLayout(h_layout)
        main_layout.addStretch(1)

        # Definizione delle 5 sezioni
        sections = [
            ("Modello 3D (Android)", "Genera modelli tattili ottimizzati per tablet.", os.path.join(config.ASSET_DIR, "android_icon.png"), self.open_android_model),
            ("Modello 3D (Circuito)", "Crea modelli tattili pronti alla stampa.", os.path.join(config.ASSET_DIR, "circuit_icon.png"), self.open_circuit_model),
            ("Bassorilievo Semplice", "Crea modelli tattili base pronti alla stampa, senza interattività.", os.path.join(config.ASSET_DIR, "basrelief_icon.png"), self.open_basic_model),
            ("Lettura Sensore", "Avvia la lettura interattiva da circuito con feedback vocale.", os.path.join(config.ASSET_DIR, "reader_icon.png"), self.open_reader),
            ("Calibrazione", "Associa i nodi fisici alle impronte del sensore.", os.path.join(config.ASSET_DIR, "calibration_icon.png"), self.open_calibration)
        ]

        # Posizionamento: Le prime 3 nella riga 1, le restanti nella riga 2
        for i, (title, desc, icon_path, callback) in enumerate(sections):
            card = NavCard(title, desc, icon_path, callback)
            if i < 3:
                row1_layout.addWidget(card)
            else:
                row2_layout.addWidget(card)
                
        #aggiungiamo le due righe complete al contenitore verticale
        cards_v_layout.addLayout(row1_layout)
        cards_v_layout.addLayout(row2_layout)

        # Stile per le card
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
            /* STILE PER QUANDO LA CARD È DISABILITATA */
            #navCard:disabled {
                background-color: #f0f0f0;
                border: 2px solid #cccccc;
            }
            #navCard:disabled QLabel {
                color: #aaaaaa;
            }
        """)

    # --- Metodi per aprire le finestre ---
    def open_android_model(self, card):
        from src.ui.android_model_window import AndroidModelWindow
        self.android_win = AndroidModelWindow()
        # Quando la finestra muore (viene chiusa), riabilita la card!
        self.android_win.destroyed.connect(lambda x: card.setEnabled(True))
        self.android_win.show()

    def open_circuit_model(self, card):
        from src.ui.circuit_model_window import CircuitModelWindow
        self.circuit_win = CircuitModelWindow()
        self.circuit_win.destroyed.connect(lambda x: card.setEnabled(True))
        self.circuit_win.show()

    def open_basic_model(self, card):
        from src.ui.basic_haptic_modeler import LandingWindow 
        self.basic_win = LandingWindow()
        self.basic_win.destroyed.connect(lambda x: card.setEnabled(True))
        self.basic_win.show()

    def open_reader(self, card):
        from src.ui.hapticReader_window import HapticReaderWindow
        self.read_win = HapticReaderWindow()
        self.read_win.destroyed.connect(lambda x: card.setEnabled(True))
        self.read_win.show()

    def open_calibration(self, card):
        from src.ui.calibration_window import CalibrationWindow
        self.calib_win = CalibrationWindow()
        self.calib_win.destroyed.connect(lambda x: card.setEnabled(True))
        self.calib_win.show()