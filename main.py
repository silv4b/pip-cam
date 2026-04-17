import sys
from PyQt6.QtWidgets import QApplication
from classes.launcher import Launcher


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    launcher = Launcher()
    launcher.show()
    sys.exit(app.exec())
