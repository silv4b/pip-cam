import json
import sys
import os

CONFIG_FILE = "pip_config.json"


def load_all_configs():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                return json.load(f)
        except:  # noqa
            return {}
    return {}


def save_all_configs(configs):
    """Salva o dicionário completo de configurações no disco."""
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(configs, f, indent=4)
    except Exception as e:
        print(f"Erro ao salvar configurações: {e}")


def resource_path(relative_path):
    """Retorna o caminho absoluto para o recurso, funcionando em Dev e no PyInstaller"""
    try:
        # O PyInstaller cria uma pasta temporária e armazena o caminho em _MEIPASS
        base_path = sys._MEIPASS  # type: ignore
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)
