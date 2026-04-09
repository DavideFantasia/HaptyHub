from dataclasses import dataclass, asdict
import json, os

@dataclass
class Node:
    id: str
    description: str
    fingerprint: list   # Intera frequenza di 101 valori
    # x: float = 0.0    # (Futuro) Coordinate spaziali
    # y: float = 0.0    # (Futuro) Coordinate spaziali

class HapticGraph:
    def __init__(self):
        self.nodes = []
        self.baseline_data = [] # Dati del sensore a riposo

    def add_node(self, node: Node):
        self.nodes.append(node)

    def to_json(self, filepath: str):
        with open(filepath, 'w') as f:
            json.dump([asdict(n) for n in self.nodes], f, indent=4)

    @classmethod
    def from_json(cls, filepath: str):
        """Metodo per caricare un grafo salvato in precedenza."""
        graph = cls()
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                data = json.load(f)
                for item in data:
                    # Inizializza l'oggetto Node scartando eventuali campi extra futuri
                    node = Node(**item)
                    graph.add_node(node)
        return graph