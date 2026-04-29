import sys
from PyQt6.QtWidgets import QApplication, QSplashScreen
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QPixmap

from utils.functions import init_app_environment


def load_heavy_modules():
    """
    Carrega módulos pesados de forma atrasada para melhorar o tempo de inicialização da splash screen.
    """
    # Importação atrasada de módulos que exigem maior processamento ou I/O
    from classes.views.launcher import Launcher
    from classes.core.config_manager import ConfigManager

    return Launcher, ConfigManager


class AppStarter:
    """
    Classe responsável por inicializar a aplicação, exibir a splash screen e carregar
    as dependências de forma assíncrona.
    """

    def __init__(self, app):
        """
        Inicializa o AppStarter.

        Args:
            app (QApplication): A instância principal da aplicação Qt.
        """
        self.app = app
        self.launcher = None
        self.config_manager = None
        self.splash = None

    def show_splash(self):
        """
        Cria e exibe a tela de carregamento (Splash Screen) com efeito de fade in.
        Inicia também o timer para o carregamento dos módulos pesados.
        """
        # Carregamento da imagem da splash screen
        pixmap = QPixmap("assets/pipcam_icon.png")
        if pixmap.isNull():
            pixmap = QPixmap(156, 156)
            pixmap.fill(Qt.GlobalColor.darkBlue)
        else:
            pixmap = pixmap.scaled(
                128,
                128,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )

        # Configuração da janela da splash screen
        self.splash = QSplashScreen(pixmap, Qt.WindowType.WindowStaysOnTopHint)
        self.splash.setWindowOpacity(0)
        self.splash.show()

        # Efeito de animação (Fade in)
        self.fade_in = QPropertyAnimation(self.splash, b"windowOpacity")
        self.fade_in.setDuration(200)
        self.fade_in.setStartValue(0.0)
        self.fade_in.setEndValue(1.0)
        self.fade_in.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self.fade_in.start()

        # Agenda o carregamento dos módulos
        QTimer.singleShot(300, self.load_modules)

    def load_modules(self):
        """
        Carrega as dependências do sistema e exibe a janela principal (Launcher),
        escondendo a splash screen.
        """
        launcher_cls, config_cls = load_heavy_modules()

        self.config_manager = config_cls()
        self.app.aboutToQuit.connect(self.config_manager._do_save)

        self.launcher = launcher_cls()
        self.launcher.show()

        # Efeito de encerramento da splash screen (Fade out)
        self.fade_out = QPropertyAnimation(self.splash, b"windowOpacity")
        self.fade_out.setDuration(200)
        self.fade_out.setStartValue(1.0)
        self.fade_out.setEndValue(0.0)
        self.fade_out.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self.fade_out.finished.connect(
            lambda: self.splash.close() if self.splash else None
        )
        self.fade_out.start()


if __name__ == "__main__":
    # Configuração inicial da Aplicação Qt
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    # Prepara diretórios e arquivos de configuração
    init_app_environment()

    # Inicializa e apresenta o splash screen
    starter = AppStarter(app)
    starter.show_splash()

    sys.exit(app.exec())
