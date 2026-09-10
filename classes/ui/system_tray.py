from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QMenu, QSystemTrayIcon


class SystemTrayIcon(QSystemTrayIcon):
    """
    Ícone da bandeja do sistema que mantém o aplicativo acessível mesmo quando
    o Launcher está oculto. Oferece ações para restaurar o Setup ou encerrar
    a aplicação por completo.
    """

    # Sinais emitidos pelas ações do menu de contexto
    restore_requested = pyqtSignal()
    quit_requested = pyqtSignal()

    def __init__(self, icon_path, parent=None):
        """
        Inicializa o ícone da bandeja com o menu de contexto.

        Args:
            icon_path (str): Caminho para o arquivo de ícone a ser exibido.
            parent (QObject, optional): Objeto pai do ícone.
        """
        super().__init__(QIcon(icon_path), parent)
        self.setToolTip("PiP Cam")

        # ==========================================
        # Sessão de Menu de Contexto
        # ==========================================
        menu = QMenu()
        self.restore_action = menu.addAction("Abrir Setup")
        self.quit_action = menu.addAction("Sair")

        if self.restore_action is not None:
            self.restore_action.triggered.connect(self.restore_requested.emit)
        if self.quit_action is not None:
            self.quit_action.triggered.connect(self.quit_requested.emit)

        self.setContextMenu(menu)

        # Um clique simples no ícone também restaura o Setup
        self.activated.connect(self._on_activated)

    def _on_activated(self, reason):
        """
        Restaura o Setup quando o usuário clica uma vez (trigger) no ícone.

        Args:
            reason (QSystemTrayIcon.ActivationReason): Motivo da ativação do ícone.
        """
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.restore_requested.emit()
