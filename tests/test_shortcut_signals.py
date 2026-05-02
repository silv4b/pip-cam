import pytest
from classes.shortcut_signals import ShortcutSignals


class TestShortcutSignals:
    def test_signals_exist(self, qtbot):
        """Verifica que todos os 8 sinais esperados estão definidos na classe ShortcutSignals."""
        signals = ShortcutSignals()
        assert hasattr(signals, "resize_signal")
        assert hasattr(signals, "toggle_signal")
        assert hasattr(signals, "toggle_avatar_signal")
        assert hasattr(signals, "toggle_mic_signal")
        assert hasattr(signals, "toggle_camera_signal")
        assert hasattr(signals, "toggle_format_signal")
        assert hasattr(signals, "toggle_border_mode_signal")
        assert hasattr(signals, "toggle_border_visibility_signal")

    def test_resize_signal_emits_int(self, qtbot):
        """Confirma que o resize_signal emite corretamente um valor inteiro positivo (aumentar tamanho)."""
        signals = ShortcutSignals()
        with qtbot.wait_signal(signals.resize_signal) as blocker:
            signals.resize_signal.emit(20)
        assert blocker.args == [20]

    def test_resize_signal_negative(self, qtbot):
        """Confirma que o resize_signal emite corretamente um valor inteiro negativo (diminuir tamanho)."""
        signals = ShortcutSignals()
        with qtbot.wait_signal(signals.resize_signal) as blocker:
            signals.resize_signal.emit(-20)
        assert blocker.args == [-20]

    def test_toggle_signal(self, qtbot):
        """Testa que o toggle_signal (visibilidade da janela) é emitido sem argumentos."""
        signals = ShortcutSignals()
        with qtbot.wait_signal(signals.toggle_signal):
            signals.toggle_signal.emit()

    def test_toggle_avatar_signal(self, qtbot):
        """Testa que o toggle_avatar_signal (ligar/desligar avatar) é emitido corretamente."""
        signals = ShortcutSignals()
        with qtbot.wait_signal(signals.toggle_avatar_signal):
            signals.toggle_avatar_signal.emit()

    def test_toggle_mic_signal(self, qtbot):
        """Testa que o toggle_mic_signal (ligar/desligar microfone) é emitido corretamente."""
        signals = ShortcutSignals()
        with qtbot.wait_signal(signals.toggle_mic_signal):
            signals.toggle_mic_signal.emit()

    def test_toggle_camera_signal(self, qtbot):
        """Testa que o toggle_camera_signal (alternar câmera) é emitido corretamente."""
        signals = ShortcutSignals()
        with qtbot.wait_signal(signals.toggle_camera_signal):
            signals.toggle_camera_signal.emit()

    def test_toggle_format_signal(self, qtbot):
        """Testa que o toggle_format_signal (alternar formato da máscara) é emitido corretamente."""
        signals = ShortcutSignals()
        with qtbot.wait_signal(signals.toggle_format_signal):
            signals.toggle_format_signal.emit()

    def test_toggle_border_mode_signal(self, qtbot):
        """Testa que o toggle_border_mode_signal (modo Discord/áudio) é emitido corretamente."""
        signals = ShortcutSignals()
        with qtbot.wait_signal(signals.toggle_border_mode_signal):
            signals.toggle_border_mode_signal.emit()

    def test_toggle_border_visibility_signal(self, qtbot):
        """Testa que o toggle_border_visibility_signal (mostrar/ocultar borda) é emitido corretamente."""
        signals = ShortcutSignals()
        with qtbot.wait_signal(signals.toggle_border_visibility_signal):
            signals.toggle_border_visibility_signal.emit()

    def test_multiple_emissions(self, qtbot):
        """Verifica que múltiplas emissões do resize_signal são recebidas na ordem correta pelo listener."""
        signals = ShortcutSignals()
        received = []
        signals.resize_signal.connect(received.append)

        signals.resize_signal.emit(10)
        signals.resize_signal.emit(20)
        signals.resize_signal.emit(-5)

        assert received == [10, 20, -5]
