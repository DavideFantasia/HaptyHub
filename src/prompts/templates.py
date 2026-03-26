from abc import ABC, abstractmethod
import config
import os

class BasePrompt(ABC):
    """Classe astratta base per tutti i template di prompt."""
    
    @abstractmethod
    def get_phase_1(self) -> str:
        """Restituisce il prompt per l'analisi dell'immagine."""
        pass

    @abstractmethod
    def get_phase_2(self) -> str:
        """Restituisce il system prompt per la generazione del codice."""
        pass

    @abstractmethod
    def get_from_file(self, filepath: str) -> str:
        """Metodo per caricare un prompt da file, se necessario."""
        pass


class GraphPrompt(BasePrompt):

    """Classe base per i grafi (Diretti e Indiretti) che condividono gli stessi parametri."""
    def __init__(self, nodes: int, edges: int, subject: str, is_directed: bool):
        self.nodes = nodes
        self.edges = edges
        self.subject = subject
        self.is_directed = is_directed
        self.__prompt_path = os.path.join(config.PROMPT_DIR, "DirectGraph") if is_directed else os.path.join(config.PROMPT_DIR, "UndirectGraph")

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
    
    def get_from_file(self, filepath: str) -> str:
        with open(filepath, 'r') as file:
            return file.read()


# --- Le 4 Implementazioni Specifiche ---

class DirectGraphPrompt(GraphPrompt):
    def __init__(self, nodes: int, edges: int, subject: str):
        super().__init__(nodes, edges, subject, is_directed=True)

class UndirectGraphPrompt(GraphPrompt):
    def __init__(self, nodes: int, edges: int, subject: str):
        super().__init__(nodes, edges, subject, is_directed=False)

class FlowChartPrompt(BasePrompt):
    def get_phase_1(self) -> str:
        return "TODO" # Da definire
    def get_phase_2(self) -> str:
        return "TODO"

class SetTheoryPrompt(BasePrompt):
    def get_phase_1(self) -> str:
        return "TODO" # Da definire
    def get_phase_2(self) -> str:
        return "TODO"