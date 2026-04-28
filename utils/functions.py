import json
import sys
import os
import shutil
import platform

IS_WINDOWS = os.name == "nt"
IS_LINUX = os.name == "posix" and platform.system() in ("Linux", "Darwin")
IS_MACOS = platform.system() == "Darwin"
SYSTEM = platform.system()

# Configurações de diretórios centralizados
if os.name == "nt":
    # No Windows, usamos a pasta AppData do usuário
    APPDATA = os.environ.get("APPDATA", os.path.expanduser("~\\AppData\\Roaming"))
    BASE_DIR = os.path.join(APPDATA, "PiP_Cam")

    # Migração do diretório local para o AppData (se existir localmente e não no AppData)
    LOCAL_BASE_DIR = "pip_cam_config"
    if os.path.exists(LOCAL_BASE_DIR) and not os.path.exists(BASE_DIR):
        try:
            # Tenta criar a pasta pai se necessário
            os.makedirs(os.path.dirname(BASE_DIR), exist_ok=True)
            shutil.move(LOCAL_BASE_DIR, BASE_DIR)
            print(f"Migrado diretório de configuração: {LOCAL_BASE_DIR} -> {BASE_DIR}")
        except Exception as e:
            print(f"Erro ao migrar diretório local para AppData: {e}")
else:
    # No Linux/MacOS usamos uma pasta oculta na home
    BASE_DIR = os.path.join(os.path.expanduser("~"), ".pip_cam_config")

CONFIG_FILE = os.path.join(BASE_DIR, "pip_config.json")
AVATAR_DIR = os.path.join(BASE_DIR, "avatars")

# Garante que as pastas existam
os.makedirs(AVATAR_DIR, exist_ok=True)


# Migração: Se existirem arquivos na raiz, move para a pasta centralizada
def _migrate_old_files():
    try:
        migrated = False
        # Move config
        OLD_CONFIG = "pip_config.json"
        if os.path.exists(OLD_CONFIG) and not os.path.exists(CONFIG_FILE):
            shutil.move(OLD_CONFIG, CONFIG_FILE)
            print(f"Migrado: {OLD_CONFIG} -> {CONFIG_FILE}")
            migrated = True

        # Move avatars
        OLD_AVATAR_DIR = "avatar"
        if os.path.exists(OLD_AVATAR_DIR):
            for file in os.listdir(OLD_AVATAR_DIR):
                old_path = os.path.join(OLD_AVATAR_DIR, file)
                new_path = os.path.join(AVATAR_DIR, file)
                if not os.path.exists(new_path):
                    shutil.move(old_path, new_path)
            # Remove a pasta antiga se estiver vazia
            try:
                os.rmdir(OLD_AVATAR_DIR)
            except:
                pass
            print(f"Migrados avatares de {OLD_AVATAR_DIR} para {AVATAR_DIR}")
            migrated = True

        # Se migrou algo, precisamos atualizar os caminhos INTERNOS do JSON
        if migrated and os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r") as f:
                content = f.read()

            # Substitui o caminho antigo pelo novo no texto do JSON
            new_content = content.replace('"avatar/', f'"{AVATAR_DIR}/')
            new_content = new_content.replace("\\\\avatar\\\\", f"{AVATAR_DIR}\\\\")

            with open(CONFIG_FILE, "w") as f:
                f.write(new_content)
            print("Caminhos internos de avatares atualizados no config.")

    except Exception as e:
        print(f"Erro na migração: {e}")


_migrate_old_files()


DEFAULT_CONFIGS = {
    "border_color": "#4d6fc4",
    "border_mode": "Cor Sólida",
    "last_mode": "Círculo",
    "last_camera_name": "",
    "use_avatar": False,
    "avatar_path": "",
    "multi_cam_mode": False,
    "hide_toolbar": False,
    "starts_muted": False,
    "ignored_cameras": [],
    "ignored_mics": [],
    "mic_device": -1,
    "audio_sensitivity": 2.0,
    "audio_threshold": 0.01,
}


def load_all_configs():
    """Carrega as configurações do JSON, criando o arquivo com padrões se não existir."""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                data = json.load(f)
                # Faz merge com os defaults para garantir que novas chaves existam
                return {**DEFAULT_CONFIGS, **data}
        except Exception as e:
            print(f"Erro ao ler JSON: {e}. Usando padrões.")
            return DEFAULT_CONFIGS

    # Se não existe, cria com os padrões
    save_all_configs(DEFAULT_CONFIGS)
    return DEFAULT_CONFIGS


def save_all_configs(configs):
    """Salva o dicionário completo de configurações no disco."""
    try:
        # Garante que a pasta existe antes de tentar salvar o arquivo
        os.makedirs(BASE_DIR, exist_ok=True)
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
