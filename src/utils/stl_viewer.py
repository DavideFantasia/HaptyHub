import numpy as np
from stl import mesh
from PyQt6.QtWidgets import QWidget, QVBoxLayout
import pyqtgraph.opengl as gl
import pyqtgraph.opengl.shaders as shaders
from PyQt6.QtCore import Qt


def _reset_gl_shader_cache():
    """
    Resetta la cache degli shader di pyqtgraph dopo la distruzione del contesto OpenGL.
    """
    # Reset su GLLinePlotItem (causa del crash: griglia e linee)
    try:
        from pyqtgraph.opengl.items.GLLinePlotItem import GLLinePlotItem
        if hasattr(GLLinePlotItem, '_shaderProgram'):
            GLLinePlotItem._shaderProgram = None
    except Exception as e:
        print(f"Avviso reset GLLinePlotItem: {e}")

    # Reset su GLMeshItem (mesh STL)
    try:
        from pyqtgraph.opengl.items.GLMeshItem import GLMeshItem
        if hasattr(GLMeshItem, '_shaderProgram'):
            GLMeshItem._shaderProgram = None
    except Exception as e:
        print(f"Avviso reset GLMeshItem: {e}")

    # Reset generico su tutti i moduli gl items che potrebbero avere shader cachati
    try:
        import pyqtgraph.opengl.items as gl_items
        import pkgutil, importlib, inspect
        import pyqtgraph.opengl.items as items_pkg

        for importer, modname, ispkg in pkgutil.iter_modules(items_pkg.__path__):
            try:
                mod = importlib.import_module(f"pyqtgraph.opengl.items.{modname}")
                for name, obj in inspect.getmembers(mod, inspect.isclass):
                    if hasattr(obj, '_shaderProgram'):
                        obj._shaderProgram = None
            except Exception:
                pass
    except Exception as e:
        print(f"Avviso reset generico: {e}")


class STLViewerWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)

        self.view = gl.GLViewWidget()
        self._layout.addWidget(self.view)

        self.current_mesh_item = None
        self.grid = None
        self._grid_initialized = False

    def showEvent(self, event):
        super().showEvent(event)
        if not self._grid_initialized:
            self._create_grid()
            self._grid_initialized = True

    def _create_grid(self):
        if self.grid is not None:
            try:
                self.view.removeItem(self.grid)
            except Exception:
                pass
            self.grid = None

        self.grid = gl.GLGridItem()
        self.grid.scale(10, 10, 1)
        self.view.addItem(self.grid)

    def cleanup(self):
        """Rilascia le risorse OpenGL e resetta la cache degli shader."""
        print("Svuotamento risorse GPU...")
        try:
            items = list(self.view.items)
            for item in items:
                self.view.removeItem(item)
            self.view.update()
        except Exception as e:
            print(f"Errore durante cleanup OpenGL: {e}")
        finally:
            self.current_mesh_item = None
            self.grid = None
            self._grid_initialized = False
            # Fondamentale: resetta la cache DOPO aver rimosso gli item
            _reset_gl_shader_cache()

    def load_stl(self, filepath):
        try:
            if self.current_mesh_item is not None:
                self.view.removeItem(self.current_mesh_item)
                self.current_mesh_item = None

            stl_mesh = mesh.Mesh.from_file(filepath)
            vertices = stl_mesh.vectors.reshape(-1, 3)
            faces = np.arange(vertices.shape[0]).reshape(-1, 3)

            min_bounds = vertices.min(axis=0)
            max_bounds = vertices.max(axis=0)
            center = (min_bounds + max_bounds) / 2.0
            size = np.linalg.norm(max_bounds - min_bounds)
            vertices = vertices - center

            mesh_data = gl.MeshData(vertexes=vertices, faces=faces)
            self.current_mesh_item = gl.GLMeshItem(
                meshdata=mesh_data,
                smooth=False,
                drawEdges=False,
                color=(0.9, 0.9, 0.9, 1.0),
                shader='shaded',
                glOptions='opaque'
            )

            self.view.addItem(self.current_mesh_item)
            self.view.setCameraPosition(distance=size * 1.5, elevation=35, azimuth=45)

        except Exception as e:
            print(f"❌ Errore nel caricamento 3D: {e}")