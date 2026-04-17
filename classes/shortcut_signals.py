from PyQt6.QtCore import pyqtSignal, QObject


class ShortcutSignals(QObject):
    resize_signal = pyqtSignal(int)
    toggle_signal = pyqtSignal()
