import sys
from PyQt6.QtWidgets import QApplication
from src.ui.landing_window import LandingWindow

def main():
    # Crea l'applicazione Qt
    app = QApplication(sys.argv)
    
    # Crea e mostra la finestra di landing
    window = LandingWindow()
    window.show()
    
    # Esegui il ciclo degli eventi dell'app
    sys.exit(app.exec())

if __name__ == '__main__':
    main()