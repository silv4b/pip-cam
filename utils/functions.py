import json
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


def save_mode_config(mode_name, size, x, y):
    configs = load_all_configs()
    configs[mode_name] = {"size": size, "x": x, "y": y}
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(configs, f, indent=4)
    except Exception as e:
        print(f"Erro ao salvar: {e}")
