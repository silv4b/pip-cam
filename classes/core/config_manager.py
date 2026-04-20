from utils.functions import load_all_configs, save_all_configs
from PyQt6.QtCore import QTimer


class ConfigManager:
    """Encapsula o acesso às configurações do sistema com cache e salvamento otimizado."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
            cls._instance.configs = load_all_configs()
            cls._instance._save_timer = QTimer()
            cls._instance._save_timer.setSingleShot(True)
            cls._instance._save_timer.setInterval(500)  # Debounce de 500ms
            cls._instance._save_timer.timeout.connect(cls._instance._do_save)
        return cls._instance

    def reload(self):
        """Atualiza o cache local sem perder a referência do dicionário."""
        new_data = load_all_configs()
        self.configs.clear()
        self.configs.update(new_data)
        return self.configs

    def get(self, key, default=None):
        """Busca um valor no cache local."""
        return self.configs.get(key, default)

    def set_global(self, key, value):
        """Atualiza uma configuração global no cache e agenda salvamento."""
        self.configs[key] = value
        self.request_save()

    def set_mode(self, mode_key, size, zoom, pan_x, pan_y, x=0, y=0):
        """Atualiza uma configuração de modo no cache e agenda salvamento."""
        if mode_key not in self.configs:
            self.configs[mode_key] = {}

        self.configs[mode_key].update(
            {"size": size, "zoom": zoom, "pan_x": pan_x, "pan_y": pan_y, "x": x, "y": y}
        )
        self.request_save()

    def request_save(self):
        """Agenda o salvamento em disco para evitar I/O excessivo."""
        self._save_timer.start(200)

    def save_now(self):
        """Força o salvamento imediato em disco."""
        self._save_timer.stop()
        self._do_save()

    def _do_save(self):
        """Executa o salvamento real em disco."""
        save_all_configs(self.configs)
        print("Configurações salvas no disco com sucesso.")

    def get_mode_config(self, mode_key, fallback_mode=None):
        """Recupera a config de um modo com fallback se não existir."""
        return self.configs.get(mode_key, self.configs.get(fallback_mode, {}))
