import keyboard
from classes.shortcut_signals import ShortcutSignals


class HotkeyManager:
    """Centraliza a gestão de atalhos globais do teclado."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(HotkeyManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self.signals = ShortcutSignals()
        self._initialized = True

    def setup_global_hotkeys(self):
        """Configura os atalhos globais (Alt+Key)."""
        try:
            # Limpa atalhos anteriores para evitar duplicidade em restarts
            keyboard.unhook_all()

            keyboard.add_hotkey("alt+=", lambda: self.signals.resize_signal.emit(20))
            keyboard.add_hotkey("alt+plus", lambda: self.signals.resize_signal.emit(20))
            keyboard.add_hotkey("alt+-", lambda: self.signals.resize_signal.emit(-20))
            keyboard.add_hotkey("alt+s", lambda: self.signals.toggle_signal.emit())
            keyboard.add_hotkey(
                "alt+a", lambda: self.signals.toggle_avatar_signal.emit()
            )
            keyboard.add_hotkey("alt+m", lambda: self.signals.toggle_mic_signal.emit())
            keyboard.add_hotkey(
                "alt+c", lambda: self.signals.toggle_camera_signal.emit()
            )

            print("Atalhos globais inicializados com sucesso.")
        except Exception as e:
            print(f"Erro ao configurar atalhos globais: {e}")

    def cleanup(self):
        """Remove todos os ganchos de teclado."""
        try:
            keyboard.unhook_all()
        except:
            pass
