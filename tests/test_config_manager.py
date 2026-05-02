import pytest
from unittest.mock import patch, MagicMock
from classes.core.config_manager import ConfigManager


@pytest.fixture(autouse=True)
def reset_config_manager():
    """Fixture automática que reseta o Singleton do ConfigManager entre cada teste, evitando contaminação de estado."""
    ConfigManager._instance = None
    yield
    ConfigManager._instance = None


@pytest.fixture
def config_manager(qtbot):
    """Fornece uma instância limpa do ConfigManager para cada teste."""
    return ConfigManager()


class TestConfigManagerGet:
    def test_get_returns_default_when_key_not_exists(self, config_manager):
        """Verifica que get() retorna o valor padrão informado quando a chave não existe no cache."""
        result = config_manager.get("nonexistent_key", "default")
        assert result == "default"

    def test_get_returns_value_when_key_exists(self, config_manager):
        """Confirma que get() retorna o valor armazenado quando a chave existe no cache."""
        config_manager.configs["test_key"] = "test_value"
        result = config_manager.get("test_key")
        assert result == "test_value"

    def test_get_returns_none_when_no_default(self, config_manager):
        """Verifica que get() retorna None quando a chave não existe e nenhum valor padrão é fornecido."""
        result = config_manager.get("nonexistent_key")
        assert result is None


class TestConfigManagerSetGlobal:
    def test_set_global_stores_value(self, config_manager, tmp_path):
        """Testa que set_global() armazena o valor no cache e agenda o salvamento via timer de debounce (200ms)."""
        config_manager.configs.clear()
        config_file = tmp_path / "pip_cam_config" / "pip_config.json"
        config_file.parent.mkdir(parents=True, exist_ok=True)

        config_manager._save_timer.start = MagicMock()
        config_manager.set_global("border_color", "#ff0000")
        assert config_manager.configs["border_color"] == "#ff0000"
        config_manager._save_timer.start.assert_called_once_with(200)

    def test_set_global_overwrites_existing(self, config_manager):
        """Confirma que set_global() substitui o valor de uma chave existente pelo novo valor."""
        config_manager.configs["last_mode"] = "Circulo"
        with patch("classes.core.config_manager.save_all_configs"):
            config_manager.set_global("last_mode", "Quadrado")
            assert config_manager.configs["last_mode"] == "Quadrado"


class TestConfigManagerSetMode:
    def test_set_mode_creates_new_entry(self, config_manager):
        """Verifica que set_mode() cria uma nova entrada no cache com todos os campos (size, zoom, pan_x, pan_y)."""
        with patch("classes.core.config_manager.save_all_configs"):
            config_manager.set_mode("Camera 1_Circulo", 100, 150, 50, 60)

        assert "Camera 1_Circulo" in config_manager.configs
        mode = config_manager.configs["Camera 1_Circulo"]
        assert mode["size"] == 100
        assert mode["zoom"] == 150
        assert mode["pan_x"] == 50
        assert mode["pan_y"] == 60

    def test_set_mode_updates_existing_entry(self, config_manager):
        """Confirma que set_mode() atualiza os valores de uma entrada existente e adiciona posição x/y."""
        config_manager.configs["Camera 1_Circulo"] = {"size": 50, "zoom": 100}
        with patch("classes.core.config_manager.save_all_configs"):
            config_manager.set_mode("Camera 1_Circulo", 200, 300, 25, 75, x=10, y=20)

        mode = config_manager.configs["Camera 1_Circulo"]
        assert mode["size"] == 200
        assert mode["zoom"] == 300
        assert mode["pan_x"] == 25
        assert mode["pan_y"] == 75
        assert mode["x"] == 10
        assert mode["y"] == 20


class TestConfigManagerGetModeConfig:
    def test_returns_mode_config_when_exists(self, config_manager):
        """Verifica que get_mode_config() retorna a configuração específica quando a chave do modo existe."""
        config_manager.configs["Camera 1_Circulo"] = {"size": 100, "zoom": 150}
        result = config_manager.get_mode_config("Camera 1_Circulo")
        assert result == {"size": 100, "zoom": 150}

    def test_returns_fallback_when_mode_not_exists(self, config_manager):
        """Confirma que get_mode_config() usa o modo de fallback quando a chave específica não existe."""
        config_manager.configs["Circulo"] = {"size": 80, "zoom": 120}
        result = config_manager.get_mode_config("Nonexistent", "Circulo")
        assert result == {"size": 80, "zoom": 120}

    def test_returns_empty_dict_when_nothing_exists(self, config_manager):
        """Garante que get_mode_config() retorna um dicionário vazio quando nem o modo nem o fallback existem."""
        result = config_manager.get_mode_config("Nonexistent", "AlsoNonexistent")
        assert result == {}

    def test_returns_config_for_specific_mode_over_fallback(self, config_manager):
        """Verifica que a configuração específica do modo tem prioridade sobre o fallback genérico."""
        config_manager.configs["Camera 1_Circulo"] = {"size": 100}
        config_manager.configs["Circulo"] = {"size": 50}
        result = config_manager.get_mode_config("Camera 1_Circulo", "Circulo")
        assert result["size"] == 100


class TestConfigManagerSave:
    def test_save_now_calls_save(self, config_manager):
        """Confirma que save_now() interrompe o timer de debounce e chama save_all_configs imediatamente."""
        with patch("classes.core.config_manager.save_all_configs") as mock_save:
            config_manager.save_now()
            mock_save.assert_called_once_with(config_manager.configs)

    def test_request_save_starts_timer(self, config_manager):
        """Verifica que request_save() agenda o salvamento com debounce de 200ms no QTimer."""
        config_manager._save_timer.start = MagicMock()
        config_manager.request_save()
        config_manager._save_timer.start.assert_called_once_with(200)


class TestConfigManagerReload:
    def test_reload_clears_and_updates_configs(self, config_manager):
        """Testa que reload() limpa o cache atual e carrega as configurações frescas do disco, removendo dados stale."""
        config_manager.configs.clear()
        config_manager.configs["stale"] = True

        with patch(
            "classes.core.config_manager.load_all_configs",
            return_value={"fresh": "data"},
        ):
            result = config_manager.reload()

        assert "stale" not in result
        assert result["fresh"] == "data"


class TestConfigManagerSingleton:
    def test_singleton_returns_same_instance(self):
        """Garante que o padrão Singleton funciona: múltiplas instâncias retornam o mesmo objeto em memória."""
        cm1 = ConfigManager()
        cm2 = ConfigManager()
        assert cm1 is cm2
