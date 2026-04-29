from utils.functions import load_all_configs, save_all_configs
from PyQt6.QtCore import QTimer


class ConfigManager:
    """
    Encapsula o acesso às configurações do sistema utilizando o padrão Singleton.
    Mantém um cache em memória e gerencia o salvamento otimizado (debounce) em disco
    para evitar I/O excessivo.
    """

    _instance = None

    def __new__(cls):
        """
        Garante a criação de apenas uma instância da classe (Singleton).
        Inicializa o timer de salvamento com debounce.
        """
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
            cls._instance.configs = load_all_configs()
            
            # Timer de Debounce para salvamento automático
            cls._instance._save_timer = QTimer()
            cls._instance._save_timer.setSingleShot(True)
            cls._instance._save_timer.setInterval(500)  # Debounce de 500ms
            cls._instance._save_timer.timeout.connect(cls._instance._do_save)
        return cls._instance

    # ==========================================
    # Sessão de Leitura de Dados
    # ==========================================

    def reload(self):
        """
        Recarrega as configurações do disco, atualizando o cache local 
        sem perder a referência de memória do dicionário existente.
        
        Returns:
            dict: As configurações atualizadas.
        """
        new_data = load_all_configs()
        self.configs.clear()
        self.configs.update(new_data)
        return self.configs

    def get(self, key, default=None):
        """
        Busca o valor de uma configuração no cache local.
        
        Args:
            key (str): A chave da configuração a ser buscada.
            default (any): Valor retornado caso a chave não exista.
            
        Returns:
            any: O valor da configuração.
        """
        return self.configs.get(key, default)

    def get_mode_config(self, mode_key, fallback_mode=None):
        """
        Recupera as configurações específicas de um modo (ex: "Camera 1_Círculo").
        Caso não exista, tenta buscar num modo de fallback.
        
        Args:
            mode_key (str): Chave específica do modo.
            fallback_mode (str): Chave genérica a ser usada como fallback.
            
        Returns:
            dict: O dicionário com as configurações do modo (tamanho, pan, zoom, etc).
        """
        return self.configs.get(mode_key, self.configs.get(fallback_mode, {}))

    # ==========================================
    # Sessão de Escrita e Salvamento
    # ==========================================

    def set_global(self, key, value):
        """
        Atualiza uma configuração de nível global no cache e agenda um salvamento.
        
        Args:
            key (str): A chave a ser atualizada.
            value (any): O novo valor.
        """
        self.configs[key] = value
        self.request_save()

    def set_mode(self, mode_key, size, zoom, pan_x, pan_y, x=0, y=0):
        """
        Atualiza um bloco de configurações específico para um modo/câmera
        no cache e agenda um salvamento.
        
        Args:
            mode_key (str): Chave específica do modo.
            size (int): Tamanho base.
            zoom (int): Nível de zoom.
            pan_x (int): Alinhamento horizontal.
            pan_y (int): Alinhamento vertical.
            x (int): Posição X da janela no monitor.
            y (int): Posição Y da janela no monitor.
        """
        if mode_key not in self.configs:
            self.configs[mode_key] = {}

        self.configs[mode_key].update(
            {"size": size, "zoom": zoom, "pan_x": pan_x, "pan_y": pan_y, "x": x, "y": y}
        )
        self.request_save()

    def request_save(self):
        """
        Agenda o salvamento em disco. Utiliza o timer para evitar 
        múltiplas gravações seguidas (I/O intensivo).
        """
        self._save_timer.start(200)

    def save_now(self):
        """
        Força a execução imediata do salvamento das configurações em disco,
        interrompendo qualquer timer de debounce agendado.
        """
        self._save_timer.stop()
        self._do_save()

    def _do_save(self):
        """
        Método interno que executa fisicamente a gravação do cache 
        para o arquivo JSON no disco.
        """
        save_all_configs(self.configs)
        print("Configurações salvas no disco com sucesso.")
