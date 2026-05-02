import pytest
import json
import os
import sys
from unittest.mock import patch, MagicMock
import utils.functions as uf


class TestInitAppEnvironment:
    def test_creates_avatar_directory(self, tmp_path, monkeypatch):
        """Verifica que init_app_environment() cria o diretório de avatares se ele não existir."""
        avatar_dir = tmp_path / "avatars"
        with patch.object(uf, "AVATAR_DIR", str(avatar_dir)):
            with patch.object(uf, "BASE_DIR", str(tmp_path)):
                uf.init_app_environment()
                assert avatar_dir.exists()

    def test_calls_migration(self, tmp_path, monkeypatch):
        """Confirma que init_app_environment() executa a função de migração de arquivos antigos."""
        avatar_dir = tmp_path / "avatars"
        with patch.object(uf, "AVATAR_DIR", str(avatar_dir)):
            with patch.object(uf, "BASE_DIR", str(tmp_path)):
                with patch.object(uf, "_migrate_old_files") as mock_migrate:
                    uf.init_app_environment()
                    mock_migrate.assert_called_once()


class TestMigrateOldFiles:
    def test_skips_migration_when_old_config_not_exists(self, tmp_path):
        """Quando pip_config.json antigo não existe, _migrate_old_files() não executa nenhuma migração."""
        with patch.object(uf, "CONFIG_FILE", str(tmp_path / "new" / "pip_config.json")):
            with patch.object(uf, "AVATAR_DIR", str(tmp_path / "avatars")):
                with patch("shutil.move") as mock_move:
                    uf._migrate_old_files()
                    mock_move.assert_not_called()

    def test_skips_avatar_migration_when_old_dir_not_exists(self, tmp_path):
        """Quando a pasta 'avatar' antiga não existe, avatares não são migrados."""
        with patch.object(uf, "CONFIG_FILE", str(tmp_path / "nonexistent.json")):
            with patch.object(uf, "AVATAR_DIR", str(tmp_path / "avatars")):
                with patch("shutil.move") as mock_move:
                    uf._migrate_old_files()
                    mock_move.assert_not_called()


class TestLoadAllConfigs:
    def test_returns_defaults_when_file_not_exists(self, tmp_path):
        """Quando o arquivo de configuração não existe, load_all_configs() retorna as configurações padrão."""
        nonexistent = tmp_path / "nonexistent.json"
        with patch.object(uf, "CONFIG_FILE", str(nonexistent)):
            with patch.object(uf, "save_all_configs") as mock_save:
                result = uf.load_all_configs()
                assert result == uf.DEFAULT_CONFIGS
                mock_save.assert_called_once()

    def test_loads_existing_file(self, tmp_path):
        """Quando o arquivo existe e é válido, load_all_configs() retorna seu conteúdo mergeado com defaults."""
        config_file = tmp_path / "config.json"
        custom_data = {"last_mode": "Quadrado", "border_color": "#ff0000"}
        config_file.write_text(json.dumps(custom_data))

        with patch.object(uf, "CONFIG_FILE", str(config_file)):
            result = uf.load_all_configs()
            assert result["last_mode"] == "Quadrado"
            assert result["border_color"] == "#ff0000"

    def test_returns_defaults_on_invalid_json(self, tmp_path, capsys):
        """Quando o arquivo existe mas é JSON inválido, retorna defaults e imprime mensagem de erro."""
        config_file = tmp_path / "config.json"
        config_file.write_text("{invalid json")

        with patch.object(uf, "CONFIG_FILE", str(config_file)):
            result = uf.load_all_configs()
            assert result == uf.DEFAULT_CONFIGS
            captured = capsys.readouterr()
            assert "Erro ao ler JSON" in captured.out


class TestSaveAllConfigs:
    def test_creates_directory_and_saves(self, tmp_path):
        """save_all_configs() cria o diretório base se não existir e salva o JSON corretamente."""
        base_dir = tmp_path / "new_dir"
        config_file = base_dir / "config.json"

        with patch.object(uf, "BASE_DIR", str(base_dir)):
            with patch.object(uf, "CONFIG_FILE", str(config_file)):
                uf.save_all_configs({"test": True})
                assert config_file.exists()

    def test_saves_valid_json(self, tmp_path):
        """Confirma que o arquivo salvo é um JSON válido e legível."""
        base_dir = tmp_path
        config_file = base_dir / "config.json"

        with patch.object(uf, "BASE_DIR", str(base_dir)):
            with patch.object(uf, "CONFIG_FILE", str(config_file)):
                uf.save_all_configs({"key": "value"})

                with open(config_file, "r") as f:
                    data = json.load(f)
                    assert data["key"] == "value"

    def test_handles_save_error(self, tmp_path, capsys):
        """Se ocorrer erro ao salvar (ex: permissões), a exceção é tratada e mensagem é impressa."""
        with patch.object(uf, "BASE_DIR", "/root/restricted"):
            with patch.object(uf, "CONFIG_FILE", "/root/restricted/config.json"):
                with patch("os.makedirs", side_effect=PermissionError("Access denied")):
                    uf.save_all_configs({"test": True})
                    captured = capsys.readouterr()
                    assert "Erro ao salvar configurações" in captured.out


class TestResourcePath:
    def test_returns_absolute_path_in_development(self):
        """Em modo desenvolvimento (sem PyInstaller), resource_path retorna caminho absoluto relativo ao script."""
        result = uf.resource_path("assets/icon.png")
        assert os.path.isabs(result)
        assert "assets" in result
        assert "icon.png" in result

    def test_returns_path_from_meipass_in_production(self):
        """Quando empacotado com PyInstaller, resource_path usa _MEIPASS como base."""
        with patch.object(sys, "_MEIPASS", "/tmp/frozen_app", create=True):
            result = uf.resource_path("assets/icon.png")
            assert "frozen_app" in result
            assert "assets" in result
            assert "icon.png" in result
