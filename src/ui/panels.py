from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QFormLayout, 
                             QSpinBox, QLineEdit, QLabel, QTextEdit)
from src.prompts.templates import DirectGraphTemplate, UndirectGraphTemplate, FlowChartTemplate, SetTheoryTemplate

from src.prompts.templates import ELKFlowChartTemplate, ELKGraphTemplate # Per la pipeline Android/ELK

class BaseTemplatePanel(QWidget):
    """Interfaccia base per i pannelli. Tutti devono poter generare un oggetto Template."""
    def get_prompt_object(self):
        raise NotImplementedError("Devi implementare get_prompt_object()")


class GraphFormPanel(BaseTemplatePanel):
    """Pannello parametrico usato sia per Grafi Diretti che Indiretti."""
    def __init__(self, is_directed: bool):
        super().__init__()
        self.is_directed = is_directed
        
        layout = QFormLayout(self)
        
        self.nodes_input = QSpinBox()
        self.nodes_input.setMaximum(1000)
        
        self.edges_input = QSpinBox()
        self.edges_input.setMaximum(1000)
        
        self.subject_input = QLineEdit()
        self.subject_input.setPlaceholderText("Es. Reti Elettriche, Macchine a Stati...")

        layout.addRow("Numero di Nodi:", self.nodes_input)
        layout.addRow("Numero di Archi:", self.edges_input)
        layout.addRow("Soggetto/Contesto:", self.subject_input)

    def get_prompt_object(self):
        # Raccoglie i dati dalla UI e crea l'oggetto pronto per le API
        nodes = self.nodes_input.value()
        edges = self.edges_input.value()
        subject = self.subject_input.text()
        
        if self.is_directed:
            return DirectGraphTemplate(nodes, edges, subject)
        else:
            return UndirectGraphTemplate(nodes, edges, subject)

class FlowChartPanel(BaseTemplatePanel):
    """Pannello per Flow Chart, al momento senza parametri specifici."""
    def __init__(self):
        super().__init__()
        layout = QFormLayout(self)
        
        self.nodes_input = QSpinBox()
        self.nodes_input.setMaximum(1000)
        
        self.edges_input = QSpinBox()
        self.edges_input.setMaximum(1000)
        
        self.subject_input = QLineEdit()
        self.subject_input.setPlaceholderText("Es. Reti Elettriche, Macchine a Stati...")

        layout.addRow("Numero di Strutture:", self.nodes_input)
        layout.addRow("Numero di Archi:", self.edges_input)
        layout.addRow("Soggetto/Contesto:", self.subject_input)

    def get_prompt_object(self):
        # Raccoglie i dati dalla UI e crea l'oggetto pronto per le API
        nodes = self.nodes_input.value()
        edges = self.edges_input.value()
        subject = self.subject_input.text()
        return FlowChartTemplate(nodes, edges, subject)        
        
class SetTheoryPanel(BaseTemplatePanel):
    """Pannello per Set Theory, al momento senza parametri specifici."""
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        
        label = QLabel("Template selezionato: Set Theory\nI parametri specifici verranno aggiunti in futuro.")
        layout.addWidget(label)
        layout.addStretch() # Spinge tutto in alto

    def get_prompt_object(self):
        return SetTheoryTemplate()
    
# ELK BASED PANEL

class ELK_FlowChartPanel(BaseTemplatePanel):
    """Pannello per Flow Chart per la Pipeline Android, al momento senza parametri specifici."""
    def __init__(self):
        super().__init__()
        layout = QFormLayout(self)

    def get_prompt_object(self):
        # Raccoglie i dati dalla UI e crea l'oggetto pronto per le API
        return ELKFlowChartTemplate()
    
class ELK_GraphPanel(BaseTemplatePanel):
    """Pannello per Grafi per la Pipeline Android, al momento senza parametri specifici."""
    def __init__(self):
        super().__init__()
        layout = QFormLayout(self)

    def get_prompt_object(self):
        # Raccoglie i dati dalla UI e crea l'oggetto pronto per le API
        return ELKGraphTemplate()