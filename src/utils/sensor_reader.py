from abc import ABC, abstractmethod

import serial
import serial.tools.list_ports

# =============================================================================
# Esempio di utilizzo
# =============================================================================
#sensore = NVAReader()
#
#if sensore.connect():
#    print("Connesso alla scheda NVA!")
#    
#    # Simula una lettura continua
#    try:
#        for _ in range(5):
#            dati = sensore.read_data()
#            print(f"Dati ricevuti: {dati}")
#    finally:
#        # Assicuriamoci di chiudere sempre la porta quando finiamo
#        sensore.disconnect()
#        print("Disconnesso.")
#else:
#    print("Impossibile connettersi. Controlla il cavo e la porta.")
# =============================================================================

class BaseSensorReader(ABC):
    """
    Classe astratta che definisce l'interfaccia standard per leggere 
    i dati dal sensore.
    """

    @abstractmethod
    def connect(self) -> bool:
        """Stabilisce la connessione con l'hardware."""
        pass

    @abstractmethod
    def disconnect(self):
        """Chiude la connessione con l'hardware."""
        pass

    @abstractmethod
    def read_data(self) -> list:
        """
        Legge i dati dall'hardware.
        Ritorna una lista di valori (es. float) o una lista vuota in caso di errore.
        """
        pass

#=============================================================================
# Implementazione concreta per la lettura dei dati da una NanoVNA via seriale
#=============================================================================

class NVAReader(BaseSensorReader):
    def __init__(self, port: str='standard', baudrate: int = 115200, timeout: float = 1.0):
        self.port = self.__port_discovery() if port == 'standard' else port
        
        self.baudrate = baudrate
        self.timeout = timeout
        self.serial_conn = None

    def connect(self) -> bool:
        if not self.port:
            return False

        try:
            self.serial_conn = serial.Serial(self.port, self.baudrate, timeout=1.0)
            return self.serial_conn.is_open
        except serial.SerialException as e:
            if "Permission denied" in str(e):
                print("\n" + "!"*40)
                print("ERRORE DI PERMESSI SU LINUX")
                print(f"L'utente non può accedere a {self.port}.")
                print("Esegui questo comando per risolvere:")
                print(f"sudo chmod 666 {self.port}")
                print("!"*40 + "\n")
            else:
                print(f"Errore: {e}")
            return False

    def disconnect(self):
        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.close()

    def _send_command(self, command: str):
        if self.serial_conn and self.serial_conn.is_open:
            # 1. Puliamo il buffer in ingresso per evitare di leggere risposte vecchie
            self.serial_conn.reset_input_buffer() 
            
            # 2. Usiamo SOLO \r (standard NanoVNA)
            self.serial_conn.write(f"{command}\r".encode('utf-8'))
            
            # 3. Diamo alla scheda un attimo di respiro per calcolare e rispondere
            import time
            time.sleep(0.2)

    def read_data(self) -> list:
        if not self.serial_conn or not self.serial_conn.is_open:
            print("Errore: Seriale non connessa.")
            return []

        self._send_command("data 0")
        
        dati_letti = []
        try:
            lines = self.serial_conn.readlines()
            
            for line in lines:
                clean_line = line.decode('utf-8', errors='ignore').strip()
                
                # Ignora righe vuote o spurie
                if clean_line and "data 0" not in clean_line and "ch>" not in clean_line:
                    # I dati della NanoVNA sono due numeri separati da spazio: "Re Im"
                    parti = clean_line.split()
                    
                    if len(parti) >= 2:
                        try:
                            # Convertiamo le stringhe in numeri decimali (float)
                            reale = float(parti[0])
                            immaginario = float(parti[1])
                            # Salviamo la coppia come una tupla (Re, Im)
                            dati_letti.append((reale, immaginario))
                        except ValueError:
                            # Se la riga contiene testo non convertibile, la saltiamo
                            pass
                            
        except Exception as e:
            print(f"Errore durante la lettura: {e}")
            
        return dati_letti

    def __port_discovery(self)-> str:
        """Metodo di supporto per auto-scoprire la porta seriale della NVA (opzionale)."""
        print("Ricerca automatica della scheda in corso...")
        ports = serial.tools.list_ports.comports()
        
        for p in ports:
            # Opzione A: Riconoscimento tramite VID/PID (Sostituisci questi valori con i tuoi!)
            # Molti NanoVNA usano VID 0x0483 (STMicroelectronics) e PID 0x5740
            # Altri usano chip CH340 (VID 0x1A86, PID 0x7523)
            if p.vid == 0x0483 and p.pid == 0x5740:
                print(f"Scheda trovata in automatico su: {p.device}")
                return p.device

            # Opzione B: Riconoscimento tramite la descrizione testuale
            # Cerca parole chiave tipiche nella descrizione del dispositivo USB
            desc_lower = p.description.lower()
            if "stm32" in desc_lower or "ch340" in desc_lower or "serial" in desc_lower:
                print(f"Trovato dispositivo compatibile: {p.description} su {p.device}")
                return p.device

        print("Auto-discovery fallito. Nessuna scheda compatibile rilevata.")
        return None