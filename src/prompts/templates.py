from abc import ABC, abstractmethod
import config
import os

class BaseTemplate(ABC):
    """Classe astratta base per tutti i template di prompt."""
    
    @abstractmethod
    def get_phase_1(self) -> str:
        """Restituisce il prompt per l'analisi dell'immagine."""
        pass

    @abstractmethod
    def get_phase_2(self) -> str | None:
        """Restituisce il system prompt per la generazione del codice."""
        pass

    #Metodo concreto per la lettura da file
    def get_from_file(self, filepath: str) -> str:
        with open(filepath, 'r', encoding='utf-8') as file:
            return file.read()


class GraphTemplate(BaseTemplate):

    """Classe base per i grafi (Diretti e Indiretti) che condividono gli stessi parametri."""
    def __init__(self, nodes: int, edges: int, subject: str, is_directed: bool):
        self.nodes = nodes
        self.edges = edges
        self.subject = subject
        self.is_directed = is_directed
        self.__prompt_path = os.path.join(config.PROMPT_DIR, "basic", "DirectGraph") if is_directed else os.path.join(config.PROMPT_DIR,"basic", "UndirectGraph")

        self.__prompt1 = ""
        self.__prompt2 = ""
        

    def get_phase_1(self) -> str:
        type = "directed" if self.is_directed else "undirected"
        node_count = self.nodes
        edge_count = self.edges
        subject = self.subject if self.subject else ""
        base_prompt = self.get_from_file(os.path.join(self.__prompt_path, "phase1.txt"))
        added_prompt = (f"I am attaching a {type} graph used during a {subject} lesson. The graph consists of {node_count} nodes and {edge_count} edges.")
        self.__prompt1 = base_prompt + "\n\n" + added_prompt
        return self.__prompt1


    def get_phase_2(self) -> str:
        self.__prompt2 = self.get_from_file(os.path.join(self.__prompt_path, "phase2.txt"))
        return self.__prompt1+"\n\n"+self.__prompt2

# --- Le 4 Implementazioni Specifiche ---

class DirectGraphTemplate(GraphTemplate):
    def __init__(self, nodes: int, edges: int, subject: str):
        super().__init__(nodes, edges, subject, is_directed=True)

class UndirectGraphTemplate(GraphTemplate):
    def __init__(self, nodes: int, edges: int, subject: str):
        super().__init__(nodes, edges, subject, is_directed=False)

class FlowChartTemplate(BaseTemplate):
    """Template per Flow Chart, prende il numero di strutture e frecce e il soggetto come parametri."""
    def __init__(self, nodes: int = 0, edges: int = 0, subject: str = ""):
        self.nodes = nodes
        self.edges = edges
        self.subject = subject
        self.__prompt_path = os.path.join(config.PROMPT_DIR, "basic", "FlowChart")

        self.__prompt1 = ""
        self.__prompt2 = ""

    def get_phase_1(self) -> str:
        node_count = self.nodes
        edge_count = self.edges
        subject = self.subject if self.subject else ""
        base_prompt = self.get_from_file(os.path.join(self.__prompt_path, "phase1.txt"))
        added_prompt = (f"I am attaching a Flow Chart graph used during a {subject} lesson. The Flow Chart Graph consists of {node_count} nodes and {edge_count} edges.")
        self.__prompt1 = base_prompt + "\n\n" + added_prompt
        return self.__prompt1
    
    def get_phase_2(self) -> str:
        self.__prompt2 = self.get_from_file(os.path.join(self.__prompt_path, "phase2.txt"))
        self.__prompt2 = self.__prompt1+"\n\n"+self.__prompt2 # JUST FOR TESTING
        return self.__prompt1+"\n\n"+self.__prompt2

class SetTheoryTemplate(BaseTemplate):
    def get_phase_1(self) -> str:
        return "TODO" # Da definire
    def get_phase_2(self) -> str:
        return "TODO"
    
# =============================================
# Template per Maschere per Tablet
# =============================================
class ElkBaseTemplate(BaseTemplate):
    """Classe base per i template destinati ai tablet, che usano solo la Fase 1 (JSON)."""
    
    def get_phase_2(self) -> None:
        # Per le pipeline ELK, la fase 2 di Gemini non serve!
        return None




class ELKFlowChartTemplate(ElkBaseTemplate):
    """Template ELK specifico per l'estrazione di diagrammi di flusso."""
    
    def __init__(self):
        self.__prompt_path = os.path.join(config.PROMPT_DIR, "interactive")
        self.__prompt1 = ""

    def get_phase_1(self) -> str:
        base_prompt = self.get_from_file(os.path.join(self.__prompt_path, "FlowChart.txt"))
        self.__prompt1 = base_prompt
        return self.__prompt1
    
class ELKGraphTemplate(ElkBaseTemplate):
    """Template ELK specifico per l'estrazione di grafi generici."""
        
    def __init__(self):
        self.__prompt_path = os.path.join(config.PROMPT_DIR, "interactive")
        self.__prompt1 = ""

    def get_phase_1(self) -> str:
        base_prompt = self.get_from_file(os.path.join(self.__prompt_path, "FlowChart.txt"))
        self.__prompt1 = base_prompt
        return self.__prompt1