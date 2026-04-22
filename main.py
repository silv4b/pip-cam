import sys
from PyQt6.QtWidgets import QApplication, QSplashScreen
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QPixmap


def load_heavy_modules():
    from classes.views.launcher import Launcher
    from classes.core.config_manager import ConfigManager

    return Launcher, ConfigManager


class AppStarter:
    def __init__(self, app):
        self.app = app
        self.launcher = None
        self.config_manager = None
        self.splash = None

    def show_splash(self):
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

        self.splash = QSplashScreen(pixmap, Qt.WindowType.WindowStaysOnTopHint)
        self.splash.setWindowOpacity(0)
        self.splash.show()

        self.fade_in = QPropertyAnimation(self.splash, b"windowOpacity")
        self.fade_in.setDuration(200)
        self.fade_in.setStartValue(0.0)
        self.fade_in.setEndValue(1.0)
        self.fade_in.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self.fade_in.start()

        QTimer.singleShot(300, self.load_modules)

    def load_modules(self):
        launcher_cls, config_cls = load_heavy_modules()

        self.config_manager = config_cls()
        self.app.aboutToQuit.connect(self.config_manager._do_save)

        self.launcher = launcher_cls()
        self.launcher.show()

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
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    starter = AppStarter(app)
    starter.show_splash()

    sys.exit(app.exec())
