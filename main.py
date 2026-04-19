import sys
from PyQt6.QtWidgets import QApplication
from classes.views.launcher import Launcher


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    # Garante que as configurações sejam salvas ao fechar o app
    from classes.core.config_manager import ConfigManager
    config_manager = ConfigManager()
    app.aboutToQuit.connect(config_manager._do_save)
    
    launcher = Launcher()
    launcher.show()
    sys.exit(app.exec())
