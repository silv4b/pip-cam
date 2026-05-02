from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QDialogButtonBox,
    QHBoxLayout, 
    QPushButton
)
from PyQt6.QtCore import Qt


class FilterDialog(QDialog):
    """
    Modal de diálogo utilizado para listar dispositivos (câmeras ou microfones)
    e permitir que o usuário selecione quais deles deseja ocultar (ignorar).
    """

    def __init__(self, title, items_list, ignored_list, parent=None):
        """
        Inicializa o diálogo de filtro.
        
        Args:
            title (str): O título da janela do diálogo.
            items_list (list): A lista de todos os dispositivos disponíveis.
            ignored_list (list): A lista de dispositivos que já estão marcados como ignorados.
            parent (QWidget, optional): O widget pai desta janela.
        """
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setFixedWidth(440)
        self.setFixedHeight(400)
        self.layout = QVBoxLayout(self)

        self.label = QLabel(f"Selecione os itens que deseja OCULTAR:")
        self.layout.addWidget(self.label)

        # ==========================================
        # Sessão de Botões de Ação Rápida
        # ==========================================

        bulk_layout = QHBoxLayout()
        self.btn_all = QPushButton("Marcar Todos")
        self.btn_none = QPushButton("Desmarcar Todos")
        bulk_layout.addWidget(self.btn_all)
        bulk_layout.addWidget(self.btn_none)
        self.layout.addLayout(bulk_layout)

        self.btn_all.clicked.connect(
            lambda: self.set_all_checks(Qt.CheckState.Checked)
        )
        self.btn_none.clicked.connect(
            lambda: self.set_all_checks(Qt.CheckState.Unchecked)
        )

        # ==========================================
        # Sessão de Listagem de Itens (Checkbox)
        # ==========================================

        self.list_widget = QListWidget()
        for item_data in items_list:
            # Se for uma tupla (como nas câmeras antigas), pegamos o nome (index 0)
            name = item_data[0] if isinstance(item_data, tuple) else item_data

            item = QListWidgetItem(name)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            
            # Marca o checkbox se o item estiver na lista de ignorados
            item.setCheckState(
                Qt.CheckState.Checked
                if name in ignored_list
                else Qt.CheckState.Unchecked
            )
            self.list_widget.addItem(item)

        self.layout.addWidget(self.list_widget)

        # ==========================================
        # Sessão de Confirmação (OK/Cancel)
        # ==========================================

        self.buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        self.layout.addWidget(self.buttons)

    def set_all_checks(self, state):
        """
        Aplica um estado de verificação (marcado ou desmarcado) a todos 
        os itens da lista simultaneamente.
        
        Args:
            state (Qt.CheckState): O estado a ser aplicado (Checked ou Unchecked).
        """
        for i in range(self.list_widget.count()):
            self.list_widget.item(i).setCheckState(state)

    def get_selected_items(self):
        """
        Coleta e retorna os textos de todos os itens que estão marcados.
        
        Returns:
            list: Lista contendo os nomes dos dispositivos selecionados (para serem ignorados).
        """
        ignored = []
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                ignored.append(item.text())
        return ignored
