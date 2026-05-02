"""
conftest.py - Configurações compartilhadas para toda a suíte de testes.

Este arquivo é carregado automaticamente pelo pytest antes de cada teste.
Nele definimos fixtures globais que são reutilizadas por todos os módulos de teste,
evitando duplicação de código de setup.

Fixtures definidas:
    - mock_paths (autouse): Redireciona todos os caminhos de filesystem (BASE_DIR,
      CONFIG_FILE, AVATAR_DIR) para diretórios temporários isolados por teste,
      evitando que os testes leiam ou escrevam no AppData real do usuário.
"""

import sys
import os
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture(autouse=True)
def mock_paths(tmp_path, monkeypatch):
    """Fixture automática que isola o filesystem durante os testes.

    Redireciona as constantes de caminho do módulo utils.functions para
    diretórios temporários criados pelo pytest (tmp_path), garantindo que:

    1. Nenhum teste leia configurações reais do AppData do usuário
    2. Nenhum teste crie ou modifique arquivos no sistema real
    3. Cada teste receba um diretório limpo e isolado
    4. O diretório temporário seja automaticamente removido após o teste

    Esta fixture usa autouse=True, ou seja, é aplicada em TODOS os testes
    automaticamente sem necessidade de declará-la como parâmetro.

    Args:
        tmp_path: Diretório temporário fornecido pelo pytest, único por teste.
        monkeypatch: Utilitário do pytest para sobrescrever atributos/módulos.
    """
    monkeypatch.setattr("utils.functions.BASE_DIR", str(tmp_path / "pip_cam_config"))
    monkeypatch.setattr(
        "utils.functions.CONFIG_FILE",
        str(tmp_path / "pip_cam_config" / "pip_config.json"),
    )
    monkeypatch.setattr(
        "utils.functions.AVATAR_DIR", str(tmp_path / "pip_cam_config" / "avatars")
    )
    monkeypatch.setattr("utils.functions.IS_WINDOWS", True)
