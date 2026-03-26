import cv2
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtCore import Qt

def load_and_scale_image(image_path: str, max_width: int, max_height: int) -> QPixmap:
    """
    Carica un'immagine, la ridimensiona mantenendo le proporzioni
    e la converte in un QPixmap Qt.
    """
    try:
        # Carica l'immagine (può essere utile OpenCV per futuri pre-processing)
        img_cv = cv2.imread(image_path)
        if img_cv is None:
            return None

        # Ottieni le dimensioni originali
        h, w, ch = img_cv.shape
        bytes_per_line = ch * w

        # Converti da BGR (OpenCV) a RGB
        img_rgb = cv2.cvtColor(img_cv, cv2.COLOR_BGR2RGB)

        # Crea un QImage
        q_img = QImage(img_rgb.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)

        # Converti in QPixmap
        pixmap = QPixmap.fromImage(q_img)

        # Ridimensiona mantenendo le proporzioni
        scaled_pixmap = pixmap.scaled(max_width, max_height, 
                                     Qt.AspectRatioMode.KeepAspectRatio, 
                                     Qt.TransformationMode.SmoothTransformation)
        return scaled_pixmap
    except Exception as e:
        print(f"Errore nel caricamento dell'immagine: {e}")
        return None