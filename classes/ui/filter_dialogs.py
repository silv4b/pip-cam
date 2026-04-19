from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QDialogButtonBox,
)
from PyQt6.QtCore import Qt


class FilterDialog(QDialog):
    def __init__(self, title, items_list, ignored_list, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setFixedWidth(440)
        self.setFixedHeight(400)
        self.layout = QVBoxLayout(self)

        self.label = QLabel(f"Selecione os itens que deseja OCULTAR:")
        self.layout.addWidget(self.label)

        self.list_widget = QListWidget()
        for item_data in items_list:
            # Se for uma tupla (como nas câmeras), pegamos o nome (index 0)
            name = item_data[0] if isinstance(item_data, tuple) else item_data

            item = QListWidgetItem(name)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(
                Qt.CheckState.Checked
                if name in ignored_list
                else Qt.CheckState.Unchecked
            )
            self.list_widget.addItem(item)

        self.layout.addWidget(self.list_widget)

        self.buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        self.layout.addWidget(self.buttons)

    def get_selected_items(self):
        ignored = []
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                ignored.append(item.text())
        return ignored
