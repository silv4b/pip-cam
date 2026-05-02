from unittest.mock import patch, MagicMock
from classes.core.device_manager import DeviceManager


class TestGetNextAvailableCamera:
    def test_returns_next_camera(self):
        """Verifica que a próxima câmera na lista é selecionada ao passar o índice atual (0 -> Camera B)."""
        devices = ["Camera A", "Camera B", "Camera C"]
        with patch.object(DeviceManager, "get_cameras", return_value=devices):
            with patch.object(DeviceManager, "get_camera_index", return_value=1):
                new_idx, new_name = DeviceManager.get_next_available_camera(0, [])
                assert new_name == "Camera B"
                assert new_idx == 1

    def test_skips_ignored_cameras(self):
        """Confirma que câmeras na lista de ignoradas são puladas na seleção (Camera B ignorada -> vai para Camera C)."""
        devices = ["Camera A", "Camera B", "Camera C"]
        with patch.object(DeviceManager, "get_cameras", return_value=devices):
            with patch.object(DeviceManager, "get_camera_index", return_value=2):
                new_idx, new_name = DeviceManager.get_next_available_camera(
                    0, ["Camera B"]
                )
                assert new_name == "Camera C"

    def test_cycles_back_to_first(self):
        """Testa que ao chegar na última câmera, a seleção cicla de volta para a primeira."""
        devices = ["Camera A", "Camera B"]
        with patch.object(DeviceManager, "get_cameras", return_value=devices):
            with patch.object(DeviceManager, "get_camera_index", return_value=0):
                new_idx, new_name = DeviceManager.get_next_available_camera(1, [])
                assert new_name == "Camera A"

    def test_returns_minus_one_when_no_cameras(self):
        """Garante que retorna (-1, None) quando não há nenhuma câmera disponível no sistema."""
        with patch.object(DeviceManager, "get_cameras", return_value=[]):
            new_idx, new_name = DeviceManager.get_next_available_camera(0, [])
            assert new_idx == -1
            assert new_name is None

    def test_returns_minus_one_when_all_ignored(self):
        """Garante que retorna (-1, None) quando todas as câmeras estão na lista de ignoradas."""
        devices = ["Camera A", "Camera B"]
        with patch.object(DeviceManager, "get_cameras", return_value=devices):
            new_idx, new_name = DeviceManager.get_next_available_camera(
                0, ["Camera A", "Camera B"]
            )
            assert new_idx == -1
            assert new_name is None

    def test_single_camera_available(self):
        """Quando há apenas uma câmera e ela é a atual, retorna ela mesma sem alteração."""
        devices = ["Camera A"]
        with patch.object(DeviceManager, "get_cameras", return_value=devices):
            new_idx, new_name = DeviceManager.get_next_available_camera(0, [])
            assert new_idx == 0
            assert new_name == "Camera A"

    def test_current_camera_is_ignored_returns_next(self):
        """Quando a câmera atual está na lista de ignoradas, seleciona a próxima disponível."""
        devices = ["Camera A", "Camera B"]
        with patch.object(DeviceManager, "get_cameras", return_value=devices):
            with patch.object(DeviceManager, "get_camera_index", side_effect=[1, 0]):
                new_idx, new_name = DeviceManager.get_next_available_camera(
                    0, ["Camera A"]
                )
                assert new_name == "Camera B"

    def test_invalid_current_index(self):
        """Quando o índice atual é inválido (fora do range), seleciona a primeira câmera disponível."""
        devices = ["Camera A", "Camera B"]
        with patch.object(DeviceManager, "get_cameras", return_value=devices):
            with patch.object(DeviceManager, "get_camera_index", return_value=0):
                new_idx, new_name = DeviceManager.get_next_available_camera(99, [])
                assert new_idx == 0
                assert new_name == "Camera A"


class TestGetCameraIndex:
    def test_finds_camera_by_name(self):
        """Em modo não-Windows, get_camera_index retorna -1 para nomes que não seguem o padrão 'Camera N'."""
        devices = ["Camera A", "Camera B", "Camera C"]
        with patch.object(DeviceManager, "get_cameras", return_value=devices):
            with patch("classes.core.device_manager.IS_WINDOWS", False):
                idx = DeviceManager.get_camera_index("Camera B")
                assert idx == -1

    def test_finds_linux_camera_by_name(self):
        """Em modo Linux/Mac, extrai o índice numérico do nome genérico 'Camera N' e retorna corretamente."""
        idx = DeviceManager.get_camera_index("Camera 2")
        with patch("classes.core.device_manager.IS_WINDOWS", False):
            idx = DeviceManager.get_camera_index("Camera 2")
            assert idx == 2

    def test_windows_returns_index_when_found(self):
        """Em Windows, get_camera_index retorna o índice correto quando a câmera existe na lista do pygrabber."""
        mock_graph = MagicMock()
        mock_graph.get_input_devices.return_value = [
            "Webcam HD",
            "USB Camera",
            "OBS Virtual",
        ]

        with patch("classes.core.device_manager.IS_WINDOWS", True):
            with patch("pygrabber.dshow_graph.FilterGraph", return_value=mock_graph):
                idx = DeviceManager.get_camera_index("USB Camera")
                assert idx == 1

    def test_windows_returns_minus_one_when_not_found(self):
        """Em Windows, get_camera_index retorna -1 quando o nome não existe na lista do pygrabber."""
        mock_graph = MagicMock()
        mock_graph.get_input_devices.return_value = ["Webcam HD", "USB Camera"]

        with patch("classes.core.device_manager.IS_WINDOWS", True):
            with patch("pygrabber.dshow_graph.FilterGraph", return_value=mock_graph):
                idx = DeviceManager.get_camera_index("Nonexistent Camera")
                assert idx == -1

    def test_windows_returns_minus_one_on_pygrabber_error(self):
        """Em Windows, get_camera_index retorna -1 quando pygrabber lança uma exceção (COM error)."""
        with patch("classes.core.device_manager.IS_WINDOWS", True):
            with patch(
                "pygrabber.dshow_graph.FilterGraph",
                side_effect=Exception("COM error"),
            ):
                idx = DeviceManager.get_camera_index("Webcam HD")
                assert idx == -1


class TestGetMicrophones:
    def test_returns_list_of_mics(self):
        """Verifica que get_microphones retorna apenas dispositivos com canais de entrada, excluindo alto-falantes."""
        mock_devices = [
            {"name": "Mic 1", "max_input_channels": 1},
            {"name": "Speaker", "max_input_channels": 0},
            {"name": "Mic 2", "max_input_channels": 1},
        ]
        with patch(
            "classes.core.device_manager.sd.query_devices", return_value=mock_devices
        ):
            mics = DeviceManager.get_microphones()
            assert mics == ["Mic 1", "Mic 2"]

    def test_removes_duplicates(self):
        """Confirma que microfones com nomes duplicados são retornados apenas uma vez."""
        mock_devices = [
            {"name": "Mic 1", "max_input_channels": 1},
            {"name": "Mic 1", "max_input_channels": 1},
        ]
        with patch(
            "classes.core.device_manager.sd.query_devices", return_value=mock_devices
        ):
            mics = DeviceManager.get_microphones()
            assert mics == ["Mic 1"]

    def test_returns_empty_on_error(self):
        """Garante que uma exceção do sounddevice é tratada gracefulmente, retornando lista vazia."""
        with patch(
            "classes.core.device_manager.sd.query_devices",
            side_effect=Exception("fail"),
        ):
            mics = DeviceManager.get_microphones()
            assert mics == []


class TestGetMicInfo:
    def test_finds_mic_by_name(self):
        """Verifica que get_mic_info retorna o índice correto do dispositivo de áudio pelo nome."""
        mock_devices = [
            {"name": "Mic 1", "max_input_channels": 1},
            {"name": "Speaker", "max_input_channels": 0},
            {"name": "Mic 2", "max_input_channels": 1},
        ]
        with patch(
            "classes.core.device_manager.sd.query_devices", return_value=mock_devices
        ):
            idx = DeviceManager.get_mic_info("Mic 2")
            assert idx == 2

    def test_returns_minus_one_when_not_found(self):
        """Retorna -1 quando o nome do microfone procurado não existe na lista de dispositivos."""
        mock_devices = [
            {"name": "Mic 1", "max_input_channels": 1},
        ]
        with patch(
            "classes.core.device_manager.sd.query_devices", return_value=mock_devices
        ):
            idx = DeviceManager.get_mic_info("Nonexistent")
            assert idx == -1

    def test_returns_minus_one_on_error(self):
        """Garante que uma exceção do sounddevice retorna -1 como fallback seguro."""
        with patch(
            "classes.core.device_manager.sd.query_devices",
            side_effect=Exception("fail"),
        ):
            idx = DeviceManager.get_mic_info("Mic 1")
            assert idx == -1


class TestGetCameras:
    def test_windows_returns_camera_list(self):
        """Em Windows, get_cameras usa pygrabber para retornar a lista de dispositivos de entrada."""
        with patch("classes.core.device_manager.IS_WINDOWS", True):
            mock_graph = MagicMock()
            mock_graph.get_input_devices.return_value = [
                "Webcam HD",
                "USB Camera",
            ]
            with patch("pygrabber.dshow_graph.FilterGraph", return_value=mock_graph):
                cameras = DeviceManager.get_cameras()
                assert cameras == ["Webcam HD", "USB Camera"]

    def test_windows_returns_empty_on_error(self, capsys):
        """Em Windows, se pygrabber falhar, get_cameras retorna lista vazia e imprime erro."""
        with patch("classes.core.device_manager.IS_WINDOWS", True):
            with patch(
                "pygrabber.dshow_graph.FilterGraph",
                side_effect=Exception("COM error"),
            ):
                cameras = DeviceManager.get_cameras()
                assert cameras == []
                captured = capsys.readouterr()
                assert "Erro ao listar câmeras no Windows" in captured.out

    def test_linux_scans_opencv_indices(self):
        """Em Linux/Mac, get_cameras faz scan nos índices do OpenCV e retorna nomes genéricos."""
        with patch("classes.core.device_manager.IS_WINDOWS", False):
            mock_caps = [MagicMock() for _ in range(10)]
            for i, cap in enumerate(mock_caps):
                cap.isOpened.return_value = i in (0, 2)

            with patch("cv2.VideoCapture", side_effect=mock_caps) as MockVideo:
                cameras = DeviceManager.get_cameras()
                assert cameras == ["Camera 0", "Camera 2"]


class TestOpenCamera:
    def test_windows_opens_with_dshow(self):
        """Em Windows, open_camera usa a flag CAP_DSHOW para melhor compatibilidade."""
        mock_cap = MagicMock()
        with patch("classes.core.device_manager.IS_WINDOWS", True):
            with patch("cv2.VideoCapture", return_value=mock_cap) as MockVideo:
                result = DeviceManager.open_camera(0)
                MockVideo.assert_called_once_with(0, 700)
                assert result == mock_cap

    def test_linux_opens_without_flags(self):
        """Em Linux/Mac, open_camera abre o dispositivo sem flags adicionais."""
        mock_cap = MagicMock()
        with patch("classes.core.device_manager.IS_WINDOWS", False):
            with patch("cv2.VideoCapture", return_value=mock_cap) as MockVideo:
                result = DeviceManager.open_camera(0)
                MockVideo.assert_called_once_with(0)
                assert result == mock_cap
