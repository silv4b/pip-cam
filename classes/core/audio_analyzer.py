import numpy as np
import sounddevice as sd
from PyQt6.QtCore import QObject, pyqtSignal


class AudioAnalyzer(QObject):
    level_changed = pyqtSignal(float)

    def __init__(self, device_index):
        super().__init__()
        self.device_index = device_index
        self.stream = None
        self.current_level = 0.0

    def start(self):
        if self.device_index == -1:
            return
        try:

            def audio_callback(indata, frames, time, status):
                rms = np.sqrt(np.mean(indata**2))
                self.current_level = float(rms)
                self.level_changed.emit(self.current_level)

            self.stream = sd.InputStream(
                device=self.device_index,
                channels=1,
                samplerate=44100,
                callback=audio_callback,
            )
            self.stream.start()
        except Exception as e:
            print(f"Erro ao iniciar AudioAnalyzer: {e}")

    def stop(self):
        if self.stream:
            try:
                self.stream.stop()
                self.stream.close()
            except:
                pass
            self.stream = None
