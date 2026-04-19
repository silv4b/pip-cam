from utils.functions import load_all_configs, save_global_config, save_mode_config


class ConfigManager:
    """Encapsula o acesso às configurações do sistema."""

    def __init__(self):
        self.configs = {}
        self.reload()

    def reload(self):
        """Atualiza o cache local das configurações."""
        self.configs = load_all_configs()
        return self.configs

    def get(self, key, default=None):
        """Busca um valor no config."""
        return self.configs.get(key, default)

    def set_global(self, key, value):
        """Salva uma configuração global e atualiza o cache."""
        save_global_config(key, value)
        self.configs[key] = value

    def set_mode(self, mode_key, size, zoom, pan_y, x=0, y=0):
        """Salva uma configuração específica de modo/câmera."""
        save_mode_config(mode_key, size, zoom, pan_y, x, y)
        # Atualizamos o cache local para a chave específica
        if mode_key not in self.configs:
            self.configs[mode_key] = {}

        self.configs[mode_key].update(
            {"size": size, "zoom": zoom, "pan_y": pan_y, "x": x, "y": y}
        )

    def get_mode_config(self, mode_key, fallback_mode=None):
        """Recupera a config de um modo com fallback se não existir."""
        return self.configs.get(mode_key, self.configs.get(fallback_mode, {}))
