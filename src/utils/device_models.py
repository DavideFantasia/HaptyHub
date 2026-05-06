import json
import os
from dataclasses import dataclass, asdict

@dataclass
class Device:
    name: str
    screen_width: float
    screen_height: float
    body_width: float
    body_height: float
    margin_top: float
    margin_bottom: float
    margin_left: float
    margin_right: float

    @staticmethod
    def load_devices(filepath: str):
        if not os.path.exists(filepath):
            return []
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return [Device(**d) for d in data]
        except Exception as e:
            print(f"Errore nel caricamento dispositivi: {e}")
            return []

    @staticmethod
    def save_devices(filepath: str, devices: list):
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump([asdict(d) for d in devices], f, indent=4)