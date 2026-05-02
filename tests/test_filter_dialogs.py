from PyQt6.QtCore import Qt
from classes.ui.filter_dialogs import FilterDialog


class TestFilterDialog:
    def test_dialog_creation(self, qtbot):
        """Verifica que o FilterDialog é criado corretamente com o título informado."""
        items = ["Camera A", "Camera B", "Camera C"]
        dialog = FilterDialog("Test Dialog", items, [])
        qtbot.add_widget(dialog)
        assert dialog.windowTitle() == "Test Dialog"

    def test_items_populated_correctly(self, qtbot):
        """Confirma que todos os itens da lista são adicionados ao QListWidget na ordem correta."""
        items = ["Camera A", "Camera B", "Camera C"]
        dialog = FilterDialog("Test", items, [])
        qtbot.add_widget(dialog)
        assert dialog.list_widget.count() == 3
        assert dialog.list_widget.item(0).text() == "Camera A"

    def test_ignored_items_are_checked(self, qtbot):
        """Verifica que itens presentes na lista de ignorados aparecem com checkbox marcado."""
        items = ["Camera A", "Camera B", "Camera C"]
        dialog = FilterDialog("Test", items, ["Camera B"])
        qtbot.add_widget(dialog)

        assert dialog.list_widget.item(0).checkState() == Qt.CheckState.Unchecked
        assert dialog.list_widget.item(1).checkState() == Qt.CheckState.Checked
        assert dialog.list_widget.item(2).checkState() == Qt.CheckState.Unchecked

    def test_multiple_ignored_items(self, qtbot):
        """Testa que múltiplos itens na lista de ignorados são marcados corretamente com padrão alternado."""
        items = ["A", "B", "C", "D"]
        dialog = FilterDialog("Test", items, ["A", "C"])
        qtbot.add_widget(dialog)

        assert dialog.list_widget.item(0).checkState() == Qt.CheckState.Checked
        assert dialog.list_widget.item(1).checkState() == Qt.CheckState.Unchecked
        assert dialog.list_widget.item(2).checkState() == Qt.CheckState.Checked
        assert dialog.list_widget.item(3).checkState() == Qt.CheckState.Unchecked

    def test_get_selected_items_empty_when_none_checked(self, qtbot):
        """Confirma que get_selected_items() retorna lista vazia quando nenhum checkbox está marcado."""
        items = ["Camera A", "Camera B"]
        dialog = FilterDialog("Test", items, [])
        qtbot.add_widget(dialog)
        assert dialog.get_selected_items() == []

    def test_get_selected_items_returns_checked(self, qtbot):
        """Verifica que get_selected_items() retorna apenas os nomes dos itens com checkbox marcado."""
        items = ["Camera A", "Camera B", "Camera C"]
        dialog = FilterDialog("Test", items, [])
        qtbot.add_widget(dialog)

        dialog.list_widget.item(0).setCheckState(Qt.CheckState.Checked)
        dialog.list_widget.item(2).setCheckState(Qt.CheckState.Checked)

        result = dialog.get_selected_items()
        assert result == ["Camera A", "Camera C"]

    def test_set_all_checks_checked(self, qtbot):
        """Testa que set_all_checks(Checked) marca todos os checkboxes da lista simultaneamente."""
        items = ["A", "B", "C"]
        dialog = FilterDialog("Test", items, [])
        qtbot.add_widget(dialog)

        dialog.set_all_checks(Qt.CheckState.Checked)

        for i in range(dialog.list_widget.count()):
            assert dialog.list_widget.item(i).checkState() == Qt.CheckState.Checked

    def test_set_all_checks_unchecked(self, qtbot):
        """Testa que set_all_checks(Unchecked) desmarca todos os checkboxes, mesmo os que estavam marcados."""
        items = ["A", "B", "C"]
        dialog = FilterDialog("Test", items, ["A", "B", "C"])
        qtbot.add_widget(dialog)

        dialog.set_all_checks(Qt.CheckState.Unchecked)

        for i in range(dialog.list_widget.count()):
            assert dialog.list_widget.item(i).checkState() == Qt.CheckState.Unchecked

    def test_mark_all_button(self, qtbot):
        """Verifica que clicar no botão 'Marcar Todos' marca todos os checkboxes da lista."""
        items = ["A", "B"]
        dialog = FilterDialog("Test", items, [])
        qtbot.add_widget(dialog)

        dialog.btn_all.click()

        assert dialog.list_widget.item(0).checkState() == Qt.CheckState.Checked
        assert dialog.list_widget.item(1).checkState() == Qt.CheckState.Checked

    def test_unmark_all_button(self, qtbot):
        """Verifica que clicar no botão 'Desmarcar Todos' desmarca todos os checkboxes da lista."""
        items = ["A", "B"]
        dialog = FilterDialog("Test", items, ["A", "B"])
        qtbot.add_widget(dialog)

        dialog.btn_none.click()

        assert dialog.list_widget.item(0).checkState() == Qt.CheckState.Unchecked
        assert dialog.list_widget.item(1).checkState() == Qt.CheckState.Unchecked

    def test_handles_tuple_items(self, qtbot):
        """Confirma que o dialog extrai corretamente o nome de itens no formato tupla (nome, indice)."""
        items = [("Camera A", 0), ("Camera B", 1)]
        dialog = FilterDialog("Test", items, [])
        qtbot.add_widget(dialog)

        assert dialog.list_widget.item(0).text() == "Camera A"
        assert dialog.list_widget.item(1).text() == "Camera B"

    def test_empty_items_list(self, qtbot):
        """Garante que o dialog funciona corretamente quando a lista de itens está vazia."""
        dialog = FilterDialog("Test", [], [])
        qtbot.add_widget(dialog)
        assert dialog.list_widget.count() == 0
        assert dialog.get_selected_items() == []
