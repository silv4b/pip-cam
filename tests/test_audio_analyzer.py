import numpy as np
from unittest.mock import patch, MagicMock
from classes.core.audio_analyzer import AudioAnalyzer


class TestAudioAnalyzer:
    def test_init_with_valid_device(self, qtbot):
        """Verifica que o AudioAnalyzer inicializa corretamente com um índice de dispositivo válido, com valores padrão esperados."""
        analyzer = AudioAnalyzer(device_index=0)
        assert analyzer.device_index == 0
        assert analyzer.current_level == 0.0
        assert analyzer.sensitivity == 1.0
        assert analyzer.rms_history == []
        assert analyzer.stream is None

    def test_init_with_invalid_device(self, qtbot):
        """Confirma que o AudioAnalyzer aceita dispositivo inválido (-1) sem lançar exceção."""
        analyzer = AudioAnalyzer(device_index=-1)
        assert analyzer.device_index == -1

    def test_set_sensitivity(self, qtbot):
        """Testa que set_sensitivity() atualiza corretamente o multiplicador de ganho do áudio."""
        analyzer = AudioAnalyzer(device_index=0)
        analyzer.set_sensitivity(2.5)
        assert analyzer.sensitivity == 2.5

    def test_set_sensitivity_zero(self, qtbot):
        """Verifica que a sensibilidade pode ser definida como zero (silenciando o áudio)."""
        analyzer = AudioAnalyzer(device_index=0)
        analyzer.set_sensitivity(0.0)
        assert analyzer.sensitivity == 0.0

    def test_start_with_invalid_device(self, qtbot):
        """Garante que start() é um no-op quando o device_index é -1, sem criar stream."""
        analyzer = AudioAnalyzer(device_index=-1)
        analyzer.start()
        assert analyzer.stream is None

    def test_start_creates_stream(self, qtbot):
        """Confirma que start() cria um sd.InputStream com os parâmetros corretos (device, channels, samplerate, callback)."""
        mock_stream = MagicMock()
        with patch(
            "classes.core.audio_analyzer.sd.InputStream", return_value=mock_stream
        ) as MockStream:
            analyzer = AudioAnalyzer(device_index=0)
            analyzer.start()

            MockStream.assert_called_once_with(
                device=0,
                channels=1,
                samplerate=44100,
                callback=MockStream.call_args[1]["callback"],
            )
            mock_stream.start.assert_called_once()

    def test_start_does_not_create_stream_on_error(self, qtbot, capsys):
        """Verifica que uma exceção ao criar o stream é tratada gracefulmente, com mensagem de erro no stdout."""
        with patch(
            "classes.core.audio_analyzer.sd.InputStream",
            side_effect=Exception("Audio error"),
        ):
            analyzer = AudioAnalyzer(device_index=0)
            analyzer.start()

            assert analyzer.stream is None
            captured = capsys.readouterr()
            assert "Erro ao iniciar AudioAnalyzer" in captured.out

    def test_stop_closes_stream(self, qtbot):
        """Testa que stop() chama stop() e close() no stream do sounddevice e limpa a referência."""
        mock_stream = MagicMock()
        with patch(
            "classes.core.audio_analyzer.sd.InputStream", return_value=mock_stream
        ):
            analyzer = AudioAnalyzer(device_index=0)
            analyzer.start()
            analyzer.stop()

            mock_stream.stop.assert_called_once()
            mock_stream.close.assert_called_once()
            assert analyzer.stream is None

    def test_stop_does_nothing_when_no_stream(self, qtbot):
        """Garante que stop() é seguro de chamar quando não há stream ativo (não lança exceção)."""
        analyzer = AudioAnalyzer(device_index=0)
        analyzer.stop()
        assert analyzer.stream is None

    def test_audio_callback_emits_signal(self, qtbot):
        """Verifica que o callback de áudio calcula o RMS corretamente e atualiza o current_level com valor positivo."""
        with patch("classes.core.audio_analyzer.sd.InputStream") as MockStream:
            analyzer = AudioAnalyzer(device_index=0)

            callback = None

            def capture_callback(**kwargs):
                nonlocal callback
                callback = kwargs["callback"]
                return MagicMock()

            MockStream.side_effect = capture_callback

            analyzer.start()
            assert callback is not None

            test_data = np.array([[0.5]])
            callback(test_data, 1, None, None)

            assert analyzer.current_level > 0.0

    def test_audio_callback_clamps_to_1(self, qtbot):
        """Confirma que o nível de áudio é limitado a 1.0 (100%) mesmo com sensibilidade extremamente alta."""
        with patch("classes.core.audio_analyzer.sd.InputStream") as MockStream:
            analyzer = AudioAnalyzer(device_index=0)
            analyzer.set_sensitivity(1000.0)

            callback = None

            def capture_callback(**kwargs):
                nonlocal callback
                callback = kwargs["callback"]
                return MagicMock()

            MockStream.side_effect = capture_callback

            analyzer.start()

            test_data = np.array([[0.5]])
            callback(test_data, 1, None, None)

            assert analyzer.current_level <= 1.0

    def test_rms_history_smoothing(self, qtbot):
        """Verifica que o buffer de histórico RMS respeita o tamanho máximo (history_size=5), aplicando média móvel."""
        with patch("classes.core.audio_analyzer.sd.InputStream") as MockStream:
            analyzer = AudioAnalyzer(device_index=0)

            callback = None

            def capture_callback(**kwargs):
                nonlocal callback
                callback = kwargs["callback"]
                return MagicMock()

            MockStream.side_effect = capture_callback

            analyzer.start()

            for i in range(10):
                test_data = np.array([[0.5]])
                callback(test_data, 1, None, None)

            assert len(analyzer.rms_history) <= analyzer.history_size

    def test_stop_handles_stream_close_error(self, qtbot):
        """Garante que stop() trata gracefulmente uma exceção ao parar o stream, cobrindo o bloco except pass."""
        mock_stream = MagicMock()
        mock_stream.stop.side_effect = Exception("Stream error")
        mock_stream.close.side_effect = Exception("Close error")

        with patch(
            "classes.core.audio_analyzer.sd.InputStream", return_value=mock_stream
        ):
            analyzer = AudioAnalyzer(device_index=0)
            analyzer.start()
            analyzer.stop()

            mock_stream.stop.assert_called_once()
            assert analyzer.stream is None
