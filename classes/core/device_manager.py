from utils.functions import IS_WINDOWS
import sounddevice as sd
import cv2


class DeviceManager:
    @staticmethod
    def get_cameras():
        """Retorna uma lista de nomes de câmeras disponíveis."""
        if IS_WINDOWS:
            try:
                from pygrabber.dshow_graph import FilterGraph

                return FilterGraph().get_input_devices()
            except Exception as e:
                print(f"Erro ao listar câmeras no Windows: {e}")
                return []
        else:
            return DeviceManager._get_linux_cameras()

    @staticmethod
    def _get_linux_cameras():
        """Lista câmeras no Linux/MacOS usando OpenCV."""
        devices = []
        for i in range(10):
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                # Tenta obter o nome do dispositivo
                name = cap.get(cv2.CAP_PROP_FOURCC)
                # OpenCV não retorna nome confiável, usamos um nome genérico
                devices.append(f"Camera {i}")
                cap.release()
        return devices

    @staticmethod
    def get_camera_index(name):
        """Busca o índice de uma câmera pelo seu nome."""
        if IS_WINDOWS:
            try:
                from pygrabber.dshow_graph import FilterGraph

                devices = FilterGraph().get_input_devices()
                if name in devices:
                    return devices.index(name)
                return -1
            except:
                return -1
        else:
            # Para Linux, extrai o índice do nome (ex: "Camera 0" -> 0)
            if name.startswith("Camera "):
                try:
                    return int(name.split()[-1])
                except:
                    pass
            return -1

    @staticmethod
    def get_microphones():
        try:
            devices = sd.query_devices()
            all_mics = []
            seen = set()
            for dev in devices:
                if dev["max_input_channels"] > 0:
                    name = dev["name"]
                    if name not in seen:
                        seen.add(name)
                        all_mics.append(name)
            return all_mics
        except Exception as e:
            print(f"Erro ao listar microfones: {e}")
            return []

    @staticmethod
    def get_mic_info(name):
        try:
            devices = sd.query_devices()
            for i, dev in enumerate(devices):
                if dev["name"] == name and dev["max_input_channels"] > 0:
                    return i
            return -1
        except:
            return -1
