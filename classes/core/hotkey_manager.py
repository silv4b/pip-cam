import keyboard
from classes.shortcut_signals import ShortcutSignals


class HotkeyManager:
    """
    Centraliza a gestão de atalhos globais do teclado utilizando o padrão Singleton.
    Escuta por teclas em background (mesmo com a janela minimizada) e emite
    sinais Qt correspondentes para a interface gráfica.
    """

    _instance = None

    def __new__(cls):
        """
        Garante a criação de apenas uma instância da classe (Singleton).
        """
        if cls._instance is None:
            cls._instance = super(HotkeyManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """
        Inicializa o gerenciador de atalhos e os sinais de comunicação.
        Impede a reinicialização caso já tenha sido instanciado.
        """
        if self._initialized:
            return
        self.signals = ShortcutSignals()
        self._initialized = True

    # ==========================================
    # Sessão de Configuração de Atalhos
    # ==========================================

    def setup_global_hotkeys(self):
        """
        Configura os atalhos globais do teclado (combinações com Alt).
        Vincula cada atalho a um sinal específico que será processado pelos Widgets.
        """
        try:
            # Limpa atalhos anteriores para evitar duplicidade em restarts
            keyboard.unhook_all()

            # Atalhos de Redimensionamento
            keyboard.add_hotkey("alt+=", lambda: self.signals.resize_signal.emit(20))
            keyboard.add_hotkey("alt+plus", lambda: self.signals.resize_signal.emit(20))
            keyboard.add_hotkey("alt+-", lambda: self.signals.resize_signal.emit(-20))
            
            # Atalho de Visibilidade da Janela
            keyboard.add_hotkey("alt+s", lambda: self.signals.toggle_signal.emit())
            
            # Atalhos de Alternância (Toggles) de Componentes
            keyboard.add_hotkey(
                "alt+a", lambda: self.signals.toggle_avatar_signal.emit()
            )
            keyboard.add_hotkey("alt+m", lambda: self.signals.toggle_mic_signal.emit())
            keyboard.add_hotkey(
                "alt+c", lambda: self.signals.toggle_camera_signal.emit()
            )
            keyboard.add_hotkey(
                "alt+f", lambda: self.signals.toggle_format_signal.emit()
            )
            keyboard.add_hotkey(
                "alt+d", lambda: self.signals.toggle_border_mode_signal.emit()
            )
            keyboard.add_hotkey(
                "alt+b", lambda: self.signals.toggle_border_visibility_signal.emit()
            )

            print("Atalhos globais inicializados com sucesso.")
        except Exception as e:
            print(f"Erro ao configurar atalhos globais: {e}")

    # ==========================================
    # Sessão de Limpeza e Encerramento
    # ==========================================

    def cleanup(self):
        """
        Remove todos os ganchos (hooks) de teclado associados.
        Deve ser chamado ao encerrar a aplicação para liberar recursos do sistema.
        """
        try:
            keyboard.unhook_all()
        except:
            pass
