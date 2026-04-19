from pygrabber.dshow_graph import FilterGraph
import sounddevice as sd


class DeviceManager:
    @staticmethod
    def get_cameras():
        try:
            return FilterGraph().get_input_devices()
        except Exception as e:
            print(f"Erro ao listar câmeras: {e}")
            return []

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
        # Útil para pegar o index real do dispositivo pelo nome
        try:
            devices = sd.query_devices()
            for i, dev in enumerate(devices):
                if dev["name"] == name and dev["max_input_channels"] > 0:
                    return i
            return -1
        except:
            return -1
