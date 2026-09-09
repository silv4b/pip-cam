import numpy as np
import sounddevice as sd
from PyQt6.QtCore import QObject, pyqtSignal


class AudioAnalyzer(QObject):
    """
    Classe responsável por capturar o áudio do microfone e calcular os níveis de volume (RMS)
    para o modo "Sinalizador de Áudio" (Discord Mode).
    """

    level_changed = pyqtSignal(float)

    def __init__(self, device_index):
        """
        Inicializa o analisador de áudio.

        Args:
            device_index (int): Índice do dispositivo de gravação (microfone).
        """
        super().__init__()
        self.device_index = device_index
        self.stream = None
        self.current_level = 0.0
        self.sensitivity = 1.0

        # Buffer circular para suavizar a leitura de áudio
        self.rms_history = []
        self.history_size = 5

    # ==========================================
    # Sessão de Configuração
    # ==========================================

    def set_sensitivity(self, value):
        """
        Ajusta o multiplicador de ganho do áudio.

        Args:
            value (float): Valor da sensibilidade (ex: 2.0 para amplificar em 2x).
        """
        self.sensitivity = value

    # ==========================================
    # Sessão de Controle de Fluxo (Stream)
    # ==========================================

    def start(self):
        """
        Inicia a thread de captura de áudio não-bloqueante via sounddevice.
        A cada leitura (callback), calcula a raiz quadrada média (RMS) e emite um sinal.
        """
        if self.device_index == -1:
            return
        try:

            def audio_callback(indata, frames, time, status):
                """
                Função de callback chamada automaticamente pelo sounddevice sempre que
                um novo pacote de áudio está disponível.
                """
                if status:
                    print(status)

                if indata.size == 0:
                    return

                # Cálculo do Root Mean Square (nível de energia do som)
                rms = np.sqrt(np.mean(indata**2))

                # Adiciona o novo valor ao histórico para suavização (Média Móvel)
                self.rms_history.append(float(rms))
                if len(self.rms_history) > self.history_size:
                    self.rms_history.pop(0)

                smoothed_rms = np.mean(self.rms_history)

                # Aplica sensibilidade e limita o valor a 1.0 (100%)
                amplified = smoothed_rms * self.sensitivity
                self.current_level = min(amplified, 1.0)

                # Emite o nível de áudio calculado para a UI
                self.level_changed.emit(self.current_level)

            self.stream = sd.InputStream(
                device=self.device_index,
                dtype="float32",
                callback=audio_callback,
            )
            self.stream.start()
        except Exception as e:  # noqa: BLE001
            print(f"Erro ao iniciar AudioAnalyzer: {e}")

    def stop(self):
        """
        Interrompe a escuta do microfone e libera os recursos do dispositivo.
        """
        if self.stream:
            try:
                self.stream.stop()
                self.stream.close()
            except Exception:  # noqa: BLE001, S110
                pass
            self.stream = None
