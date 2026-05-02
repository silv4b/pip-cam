from classes.ui.floating_toolbar import FloatingToolbar


class TestFloatingToolbar:
    def test_toolbar_creation(self, qtbot):
        """Verifica que a FloatingToolbar é criada e inicia oculta (hide() é chamado no __init__)."""
        toolbar = FloatingToolbar()
        qtbot.add_widget(toolbar)
        assert toolbar.isHidden()

    def test_all_buttons_exist(self, qtbot):
        """Confirma que todos os 8 botões de controle estão presentes na toolbar."""
        toolbar = FloatingToolbar()
        qtbot.add_widget(toolbar)

        assert toolbar.btn_minus is not None
        assert toolbar.btn_plus is not None
        assert toolbar.btn_format is not None
        assert toolbar.btn_close is not None
        assert toolbar.btn_mic is not None
        assert toolbar.btn_avatar is not None
        assert toolbar.btn_border_mode is not None
        assert toolbar.btn_cam is not None

    def test_close_signal(self, qtbot):
        """Testa que clicar no botão de fechar emite o sinal close_requested."""
        toolbar = FloatingToolbar()
        qtbot.add_widget(toolbar)

        with qtbot.wait_signal(toolbar.close_requested):
            toolbar.btn_close.click()

    def test_resize_plus_signal(self, qtbot):
        """Confirma que o botão '+' emite resize_requested com valor positivo (20) para aumentar o widget."""
        toolbar = FloatingToolbar()
        qtbot.add_widget(toolbar)

        with qtbot.wait_signal(toolbar.resize_requested) as blocker:
            toolbar.btn_plus.click()
        assert blocker.args == [20]

    def test_resize_minus_signal(self, qtbot):
        """Confirma que o botão '-' emite resize_requested com valor negativo (-20) para diminuir o widget."""
        toolbar = FloatingToolbar()
        qtbot.add_widget(toolbar)

        with qtbot.wait_signal(toolbar.resize_requested) as blocker:
            toolbar.btn_minus.click()
        assert blocker.args == [-20]

    def test_camera_toggle_signal(self, qtbot):
        """Testa que o botão de câmera emite o sinal camera_toggled ao ser clicado."""
        toolbar = FloatingToolbar()
        qtbot.add_widget(toolbar)

        with qtbot.wait_signal(toolbar.camera_toggled):
            toolbar.btn_cam.click()

    def test_mic_toggle_signal(self, qtbot):
        """Testa que o botão de microfone emite o sinal mic_toggled ao ser clicado."""
        toolbar = FloatingToolbar()
        qtbot.add_widget(toolbar)

        with qtbot.wait_signal(toolbar.mic_toggled):
            toolbar.btn_mic.click()

    def test_avatar_toggle_signal(self, qtbot):
        """Testa que o botão de avatar emite o sinal avatar_toggled ao ser clicado."""
        toolbar = FloatingToolbar()
        qtbot.add_widget(toolbar)

        with qtbot.wait_signal(toolbar.avatar_toggled):
            toolbar.btn_avatar.click()

    def test_format_toggle_signal(self, qtbot):
        """Testa que o botão de formato emite o sinal format_toggled ao ser clicado."""
        toolbar = FloatingToolbar()
        qtbot.add_widget(toolbar)

        with qtbot.wait_signal(toolbar.format_toggled):
            toolbar.btn_format.click()

    def test_border_mode_toggle_signal(self, qtbot):
        """Testa que o botão de modo de borda (Discord/áudio) emite o sinal border_mode_toggled ao ser clicado."""
        toolbar = FloatingToolbar()
        qtbot.add_widget(toolbar)

        with qtbot.wait_signal(toolbar.border_mode_toggled):
            toolbar.btn_border_mode.click()

    def test_button_tooltips(self, qtbot):
        """Verifica que os botões possuem tooltips informativos indicando o atalho de teclado correspondente."""
        toolbar = FloatingToolbar()
        qtbot.add_widget(toolbar)

        assert toolbar.btn_format.toolTip() == "Alternar Formato (Alt+F)"
        assert toolbar.btn_border_mode.toolTip() == "Modo Discord / Áudio (Alt+D)"

    def test_button_sizes(self, qtbot):
        """Confirma que todos os botões têm tamanho fixo de 32x32 pixels, garantindo consistência visual."""
        toolbar = FloatingToolbar()
        qtbot.add_widget(toolbar)

        assert toolbar.btn_close.size().width() == 32
        assert toolbar.btn_close.size().height() == 32
        assert toolbar.btn_cam.size().width() == 32
        assert toolbar.btn_cam.size().height() == 32

    def test_all_signals_defined(self, qtbot):
        """Verifica que todos os 7 sinais de comunicação com o widget pai estão definidos na classe."""
        toolbar = FloatingToolbar()
        qtbot.add_widget(toolbar)

        assert hasattr(toolbar, "close_requested")
        assert hasattr(toolbar, "resize_requested")
        assert hasattr(toolbar, "camera_toggled")
        assert hasattr(toolbar, "mic_toggled")
        assert hasattr(toolbar, "avatar_toggled")
        assert hasattr(toolbar, "format_toggled")
        assert hasattr(toolbar, "border_mode_toggled")
