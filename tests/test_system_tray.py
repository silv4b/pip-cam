from PyQt6.QtWidgets import QSystemTrayIcon

from classes.ui.system_tray import SystemTrayIcon


class TestSystemTrayIcon:
    def test_tray_creation(self, qtbot):
        """Verifica que o ícone da bandeja é criado com tooltip e menu corretos."""
        tray = SystemTrayIcon("assets/pipcam_icon.ico")

        assert tray.toolTip() == "PiP Cam"
        assert tray.contextMenu() is not None

    def test_restore_action_emits_signal(self, qtbot):
        """Confirma que a ação 'Abrir Setup' emite o sinal restore_requested."""
        tray = SystemTrayIcon("assets/pipcam_icon.ico")

        with qtbot.wait_signal(tray.restore_requested):
            tray.restore_action.trigger()

    def test_quit_action_emits_signal(self, qtbot):
        """Confirma que a ação 'Sair' emite o sinal quit_requested."""
        tray = SystemTrayIcon("assets/pipcam_icon.ico")

        with qtbot.wait_signal(tray.quit_requested):
            tray.quit_action.trigger()

    def test_menu_actions_labels(self, qtbot):
        """Verifica os rótulos das ações do menu de contexto."""
        tray = SystemTrayIcon("assets/pipcam_icon.ico")

        assert tray.restore_action.text() == "Abrir Setup"
        assert tray.quit_action.text() == "Sair"

    def test_single_click_restores(self, qtbot):
        """Um clique simples (Trigger) no ícone deve emitir restore_requested."""
        tray = SystemTrayIcon("assets/pipcam_icon.ico")

        with qtbot.wait_signal(tray.restore_requested):
            tray.activated.emit(QSystemTrayIcon.ActivationReason.Trigger)

    def test_double_click_does_not_restore(self, qtbot):
        """Um duplo clique (DoubleClick) não deve emitir restore_requested."""
        tray = SystemTrayIcon("assets/pipcam_icon.ico")

        received = []
        tray.restore_requested.connect(lambda: received.append(True))
        tray.activated.emit(QSystemTrayIcon.ActivationReason.DoubleClick)
        assert received == []
