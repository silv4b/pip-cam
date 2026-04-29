from utils.functions import IS_WINDOWS
import sounddevice as sd
import cv2


class DeviceManager:
    """
    Classe utilitária para gerenciar dispositivos de hardware (Câmeras e Microfones).
    Abstrai as diferenças entre sistemas operacionais (Windows vs Linux/MacOS).
    """

    # ==========================================
    # Sessão de Controle de Câmeras
    # ==========================================
    
    @staticmethod
    def get_cameras():
        """
        Retorna uma lista de nomes de câmeras disponíveis no sistema.
        No Windows, utiliza pygrabber para obter os nomes reais.
        No Linux/MacOS, faz um scan genérico nas portas do OpenCV.
        
        Returns:
            list: Lista de strings com os nomes das câmeras.
        """
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
        """
        Lista câmeras no Linux/MacOS de forma genérica testando índices do OpenCV.
        
        Returns:
            list: Lista de nomes genéricos (ex: "Camera 0", "Camera 1").
        """
        devices = []
        for i in range(10):
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                # OpenCV não retorna nome confiável, usamos um nome genérico
                devices.append(f"Camera {i}")
                cap.release()
        return devices

    @staticmethod
    def get_camera_index(name):
        """
        Busca o índice do sistema operacional correspondente ao nome de uma câmera.
        
        Args:
            name (str): O nome da câmera procurada.
            
        Returns:
            int: O índice da câmera ou -1 se não for encontrada.
        """
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
            # Para Linux, extrai o índice do nome genérico (ex: "Camera 0" -> 0)
            if name.startswith("Camera "):
                try:
                    return int(name.split()[-1])
                except:
                    pass
            return -1

    @staticmethod
    def open_camera(index):
        """
        Inicializa e retorna o objeto cv2.VideoCapture de forma segura para o SO atual.
        Aplica DSHOW apenas no Windows para melhor compatibilidade e velocidade.
        
        Args:
            index (int): Índice da câmera no SO.
            
        Returns:
            cv2.VideoCapture: O objeto de captura do OpenCV inicializado.
        """
        if IS_WINDOWS:
            return cv2.VideoCapture(index, cv2.CAP_DSHOW)
        else:
            return cv2.VideoCapture(index)

    @staticmethod
    def get_next_available_camera(current_index, ignored_names):
        """
        Retorna o índice e o nome da próxima câmera disponível, 
        ignorando as câmeras presentes na lista de ignoradas.
        
        Args:
            current_index (int): O índice da câmera atualmente em uso.
            ignored_names (list): Lista de nomes de câmeras que o usuário optou por ignorar.
            
        Returns:
            tuple: (novo_indice, novo_nome) da próxima câmera, ou (-1, None) se não houver.
        """
        all_devices = DeviceManager.get_cameras()
        devices = [d for d in all_devices if d not in ignored_names]

        if not devices:
            return -1, None

        current_cam_name = all_devices[current_index] if 0 <= current_index < len(all_devices) else ""

        # Lógica de seleção ciclica para pular para a próxima câmera
        if len(devices) > 1 or (len(devices) == 1 and current_cam_name not in devices):
            try:
                current_idx_in_filtered = devices.index(current_cam_name)
                next_idx_in_filtered = (current_idx_in_filtered + 1) % len(devices)
            except ValueError:
                next_idx_in_filtered = 0

            new_cam_name = devices[next_idx_in_filtered]
            new_index = DeviceManager.get_camera_index(new_cam_name)
            return new_index, new_cam_name
        
        return current_index, current_cam_name

    # ==========================================
    # Sessão de Controle de Microfones
    # ==========================================
    
    @staticmethod
    def get_microphones():
        """
        Obtém a lista de nomes de dispositivos de entrada de áudio (Microfones) do sistema.
        
        Returns:
            list: Lista de nomes de microfones únicos.
        """
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
        """
        Obtém o índice numérico (ID) do dispositivo de microfone com base no nome.
        
        Args:
            name (str): Nome exato do microfone retornado por get_microphones().
            
        Returns:
            int: O índice do microfone no sounddevice, ou -1 se não encontrar.
        """
        try:
            devices = sd.query_devices()
            for i, dev in enumerate(devices):
                if dev["name"] == name and dev["max_input_channels"] > 0:
                    return i
            return -1
        except:
            return -1
