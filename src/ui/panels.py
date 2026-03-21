from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QFormLayout, 
                             QSpinBox, QLineEdit, QLabel, QTextEdit)
from src.prompts.templates import DirectGraphPrompt, UndirectGraphPrompt, FlowChartPrompt, SetTheoryPrompt

class BaseTemplatePanel(QWidget):
    """Interfaccia base per i pannelli. Tutti devono poter generare un oggetto Prompt."""
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
            return DirectGraphPrompt(nodes, edges, subject)
        else:
            return UndirectGraphPrompt(nodes, edges, subject)


class TextOnlyPanel(BaseTemplatePanel):
    """Pannello provvisorio per Flow Chart e Set Theory che non hanno ancora parametri."""
    def __init__(self, template_type: str):
        super().__init__()
        self.template_type = template_type
        layout = QVBoxLayout(self)
        
        label = QLabel(f"Template selezionato: {self.template_type}\nI parametri specifici verranno aggiunti in futuro.")
        layout.addWidget(label)
        layout.addStretch() # Spinge tutto in alto

    def get_prompt_object(self):
        if self.template_type == "Flow Chart":
            return FlowChartPrompt()
        return SetTheoryPrompt()