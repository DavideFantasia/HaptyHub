import queue
from PyQt6.QtCore import QThread

class TTSWorker(QThread):
    def __init__(self):
        super().__init__()
        # Usiamo una coda thread-safe per passare i messaggi
        self.q = queue.Queue()
        self.is_running = True

    def parla(self, testo):
        """Metodo chiamato dalla UI per aggiungere testo da leggere."""
        # TRUCCO UX: Svuota la coda prima di aggiungere una nuova parola.
        # Così, se l'utente "striscia" il dito su 5 nodi velocemente, 
        # il sistema leggerà solo l'ultimo nodo senza accumulare ritardo!

        while not self.q.empty():
            try:
                self.q.get_nowait()
            except queue.Empty:
                break
                
        # Inserisce il nuovo testo nella coda
        self.q.put(testo)

    def run(self):
        """Ciclo infinito in background dedicato SOLO a pyttsx3."""

        # --- IMPOSTAZIONE DIRETTA DELLA VOCE (Linux / Windows) ---
        import platform
        if platform.system() == 'Windows':
            # (Su Windows lasciamo la ricerca intatta come prima)
            import pythoncom
            import win32com.client

            # Inizializza l'ambiente COM per questo specifico Thread
            pythoncom.CoInitialize()
            
            # Aggancia direttamente la voce nativa di Windows
            speaker = win32com.client.Dispatch("SAPI.SpVoice")
            
            # trova la voce italiana se non è quella di default
            for voice in speaker.GetVoices():
                if "it" in voice.GetDescription().lower() or "italian" in voice.GetDescription().lower():
                    speaker.Voice = voice
                    break

            while self.is_running:
                try:
                    testo = self.q.get(timeout=0.5)
                    # .Speak è naturalmente sincrono su Windows e non si incastra
                    speaker.Speak(testo) 
                except queue.Empty:
                    pass
            
            # Pulizia finale alla chiusura del thread
            pythoncom.CoUninitialize()
        
        else:
            import pyttsx3
            engine = pyttsx3.init()
            # Usiamo la voce nativa italiana di espeak.
            # 'it' è maschile standard.
            # 'it+f4' è femminile (f1, f2, f3, f4 sono varianti femminili)
            # 'it+m4' è maschile alternativa.
            engine.setProperty('voice', 'it+f4')
            engine.setProperty('rate', 125)
        
            while self.is_running:
                try:
                    # 2. Aspetta un messaggio nella coda per 0.5 secondi.
                    # Il timeout è fondamentale per permettere al ciclo while 
                    # di verificare "self.is_running" e potersi chiudere.
                    testo = self.q.get(timeout=0.5)
                    
                    # 3. Legge il testo
                    engine.say(testo)
                    engine.runAndWait()
                    
                except queue.Empty:
                    # La coda è vuota, riparte il ciclo while in silenzio
                    pass

    def stop(self):
        """Ferma il thread in modo pulito."""
        self.is_running = False
        self.wait()