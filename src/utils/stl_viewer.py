import numpy as np
from stl import mesh
from PyQt6.QtWidgets import QWidget, QVBoxLayout
import pyqtgraph.opengl as gl

class STLViewerWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        # Creiamo il visualizzatore OpenGL
        self.view = gl.GLViewWidget()
        self.layout.addWidget(self.view)
        
        # Aggiungiamo una griglia di base per dare il senso dello spazio
        self.grid = gl.GLGridItem()
        self.grid.scale(10, 10, 1) # Allarga la griglia
        self.view.addItem(self.grid)
        
        # Variabile per tenere traccia del modello caricato
        self.current_mesh_item = None

    def load_stl(self, filepath):
        """Carica un file STL, lo centra e lo renderizza a prova di bomba."""
        try:
            # Rimuove il modello precedente se esiste
            if self.current_mesh_item:
                self.view.removeItem(self.current_mesh_item)
                
            # Legge il file STL
            import numpy as np # Assicurati che sia importato
            from stl import mesh
            stl_mesh = mesh.Mesh.from_file(filepath)
            
            # Estrae vertici e facce
            vertices = stl_mesh.vectors.reshape(-1, 3)
            faces = np.arange(vertices.shape[0]).reshape(-1, 3)
            
            # Centratura Automatica
            min_bounds = vertices.min(axis=0)
            max_bounds = vertices.max(axis=0)
            center = (min_bounds + max_bounds) / 2.0
            
            # Calcola la dimensione
            size = np.linalg.norm(max_bounds - min_bounds)
            
            # Sposta l'oggetto al centro
            vertices = vertices - center
            
            # Crea l'oggetto mesh 3D
            mesh_data = gl.MeshData(vertexes=vertices, faces=faces)
            
            # --- LE 3 CORREZIONI CRITICHE ---
            self.current_mesh_item = gl.GLMeshItem(
                meshdata=mesh_data, 
                smooth=False,                  
                drawEdges=False,                
                color=(0.9, 0.9, 0.9, 1.0),
                shader='shaded',
                glOptions='opaque'
            )
            
            self.view.addItem(self.current_mesh_item)
            
            # Usa il metodo nativo di pyqtgraph per muovere la telecamera, non il dizionario opts
            self.view.setCameraPosition(distance=size * 1.5, elevation=35, azimuth=45)
            self.grid.hide() # Nasconde la griglia

            print(f"✅ Modello 3D caricato! Dimensione: {size:.2f}mm")
            
        except Exception as e:
            print(f"❌ Errore nel caricamento 3D: {e}")