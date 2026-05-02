<!-- markdownlint-disable MD060 -->

# Guia de Testes Automatizados - PiP Cam

## Visão Geral

O projeto PiP Cam possui **125 testes automatizados** distribuídos em 8 arquivos de teste, cobrindo **93%** do código-fonte. A suíte utiliza **pytest** como framework principal, **pytest-qt** para testes de interface gráfica e **unittest.mock** para simulação de hardware e filesystem.

### Como Executar

```bash
# Rodar todos os testes
uv run pytest

# Rodar com relatório de cobertura
uv run poe test

# Rodar um arquivo específico
uv run pytest tests/test_video_processor.py

# Modo verbose (mostra nome de cada teste)
uv run pytest -v

# Rodar um teste específico
uv run pytest tests/test_video_processor.py::TestProcessFrame::test_zoom_applies_correctly
```

### Estrutura de Testes

```text
tests/
├── conftest.py                  # Fixtures globais (isolamento de filesystem)
├── test_video_processor.py      # Processamento de imagem (24 testes)
├── test_shortcut_signals.py     # Sinais de atalhos do teclado (11 testes)
├── test_device_manager.py       # Gerenciamento de hardware (22 testes)
├── test_config_manager.py       # Gerenciamento de configurações (14 testes)
├── test_audio_analyzer.py       # Análise de áudio/microfone (13 testes)
├── test_filter_dialogs.py       # Diálogo de filtragem de dispositivos (12 testes)
├── test_floating_toolbar.py     # Barra de ferramentas flutuante (13 testes)
└── test_functions.py            # Utilitários e I/O (16 testes)
```

## Configuração Global (`conftest.py`)

### Fixture: `mock_paths` (aplicada automaticamente)

Redireciona todas as constantes de caminho do módulo `utils/functions.py` (`BASE_DIR`, `CONFIG_FILE`, `AVATAR_DIR`) para diretórios temporários isolados por teste. Isso garante que:

- Nenhum teste leia configurações reais do AppData do usuário
- Nenhum teste crie ou modifique arquivos no sistema real
- Cada teste receba um diretório limpo e isolado
- O diretório temporário seja automaticamente removido após o teste

## 1. Processamento de Vídeo (`test_video_processor.py`)

**Classe testada:** `VideoProcessor` (em `classes/core/video_processor.py`)
**Total de testes:** 24

### TestProcessFrame — Processamento de Frames

| Teste | Descrição |
|-------|-----------|
| `test_returns_none_for_none_frame` | Garante que `process_frame` retorna `None` ao receber um frame inválido, evitando crashes na aplicação. |
| `test_returns_qimage_for_valid_frame` | Verifica que um frame válido (numpy array) é convertido com sucesso para `QImage`. |
| `test_returns_qimage_with_correct_format` | Confirma que o `QImage` resultante usa o formato RGB888, garantindo compatibilidade com PyQt6. |
| `test_returns_correct_dimensions` | Valida que o frame mantém suas dimensões originais quando não há zoom e o aspect ratio é preservado. |
| `test_zoom_applies_correctly` | Testa que o zoom de 2x (valor 200) é aplicado corretamente e gera um `QImage` válido. |
| `test_pan_center` | Verifica que o pan centralizado (50/50) com zoom funciona sem erros. |
| `test_pan_extreme_left` | Testa o pan horizontal no extremo esquerdo (`pan_x=0`) com zoom. |
| `test_pan_extreme_right` | Testa o pan horizontal no extremo direito (`pan_x=100`) com zoom. |
| `test_pan_extreme_top` | Testa o pan vertical no extremo superior (`pan_y=0`) com zoom. |
| `test_pan_extreme_bottom` | Testa o pan vertical no extremo inferior (`pan_y=100`) com zoom. |
| `test_no_zoom_no_crop_needed` | Confirma que sem zoom e com target igual ao original, o frame mantém suas dimensões exatas. |
| `test_flip_horizontal_is_applied` | Verifica que o espelhamento horizontal (`cv2.flip`) é aplicado: pixels brancos à esquerda aparecem à direita. |
| `test_bgr_to_rgb_conversion` | Confirma que a conversão de BGR (OpenCV) para RGB (Qt) é feita corretamente: canal azul vira vermelho. |
| `test_various_aspect_ratios` | Testa que o processamento aceita diferentes aspect ratios (16:9, 4:3, 1:1) e sempre retorna um `QImage` válido. |
| `test_max_zoom` | Valida que o zoom máximo (500 = 5x) é aplicado sem erros. |

### TestCreateMaskedPixmap — Máscaras e Bordas

| Teste | Descrição |
|---|---|
| `test_circle_mode` | Testa a geração de máscara com retângulo arredondado (usa "Circulo" sem acento, cai no `else`). |
| `test_square_mode` | Testa a geração de máscara com retângulo arredondado ("1:1 Quadrado"). |
| `test_4x3_mode` | Testa a geração de máscara para o formato 4:3 com borda. |
| `test_no_border` | Verifica que a máscara é gerada corretamente mesmo quando a borda está desabilitada (`show_border=False`). |
| `test_with_pixmap_input` | Testa que `create_masked_pixmap` aceita `QPixmap` de entrada (avatar estático) com crop centralizado. |
| `test_different_border_colors` | Valida que diversas cores hexadecimais de borda são aceitas sem erros. |
| `test_default_border_width` | Verifica que a função funciona usando apenas os valores padrão de `border_width` e `show_border`. |
| `test_has_transparent_background` | Confirma que o pixmap gerado possui canal alpha (fundo transparente), essencial para o widget flutuante. |
| `test_circle_mode_with_accent` | Testa a geração de máscara circular usando o nome correto com acento ("Círculo"), cobrindo o caminho `addEllipse`. |

## 2. Sinais de Atalhos (`test_shortcut_signals.py`)

**Classe testada:** `ShortcutSignals` (em `classes/shortcut_signals.py`)
**Total de testes:** 11

| Teste | Descrição |
|---|---|
| `test_signals_exist` | Verifica que todos os 8 sinais esperados estão definidos na classe `ShortcutSignals`. |
| `test_resize_signal_emits_int` | Confirma que o `resize_signal` emite corretamente um valor inteiro positivo (aumentar tamanho). |
| `test_resize_signal_negative` | Confirma que o `resize_signal` emite corretamente um valor inteiro negativo (diminuir tamanho). |
| `test_toggle_signal` | Testa que o `toggle_signal` (visibilidade da janela) é emitido sem argumentos. |
| `test_toggle_avatar_signal` | Testa que o `toggle_avatar_signal` (ligar/desligar avatar) é emitido corretamente. |
| `test_toggle_mic_signal` | Testa que o `toggle_mic_signal` (ligar/desligar microfone) é emitido corretamente. |
| `test_toggle_camera_signal` | Testa que o `toggle_camera_signal` (alternar câmera) é emitido corretamente. |
| `test_toggle_format_signal` | Testa que o `toggle_format_signal` (alternar formato da máscara) é emitido corretamente. |
| `test_toggle_border_mode_signal` | Testa que o `toggle_border_mode_signal` (modo Discord/áudio) é emitido corretamente. |
| `test_toggle_border_visibility_signal` | Testa que o `toggle_border_visibility_signal` (mostrar/ocultar borda) é emitido corretamente. |
| `test_multiple_emissions` | Verifica que múltiplas emissões do `resize_signal` são recebidas na ordem correta pelo listener. |

## 3. Gerenciamento de Dispositivos (`test_device_manager.py`)

**Classe testada:** `DeviceManager` (em `classes/core/device_manager.py`)
**Total de testes:** 22

### TestGetNextAvailableCamera — Seleção Cíclica de Câmera

| Teste | Descrição |
|---|---|
| `test_returns_next_camera` | Verifica que a próxima câmera na lista é selecionada ao passar o índice atual (0 → Camera B). |
| `test_skips_ignored_cameras` | Confirma que câmeras na lista de ignoradas são puladas na seleção (Camera B ignorada → vai para Camera C). |
| `test_cycles_back_to_first` | Testa que ao chegar na última câmera, a seleção cicla de volta para a primeira. |
| `test_returns_minus_one_when_no_cameras` | Garante que retorna `(-1, None)` quando não há nenhuma câmera disponível no sistema. |
| `test_returns_minus_one_when_all_ignored` | Garante que retorna `(-1, None)` quando todas as câmeras estão na lista de ignoradas. |
| `test_single_camera_available` | Quando há apenas uma câmera e ela é a atual, retorna ela mesma sem alteração. |
| `test_current_camera_is_ignored_returns_next` | Quando a câmera atual está na lista de ignoradas, seleciona a próxima disponível. |
| `test_invalid_current_index` | Quando o índice atual é inválido (fora do range), seleciona a primeira câmera disponível. |

### TestGetCameraIndex — Busca de Índice por Nome

| Teste | Descrição |
|---|---|
| `test_finds_camera_by_name` | Em modo não-Windows, retorna `-1` para nomes que não seguem o padrão "Camera N". |
| `test_finds_linux_camera_by_name` | Em modo Linux/Mac, extrai o índice numérico do nome genérico "Camera N" e retorna corretamente. |
| `test_windows_returns_index_when_found` | Em Windows, retorna o índice correto quando a câmera existe na lista do pygrabber. |
| `test_windows_returns_minus_one_when_not_found` | Em Windows, retorna `-1` quando o nome não existe na lista do pygrabber. |
| `test_windows_returns_minus_one_on_pygrabber_error` | Em Windows, retorna `-1` quando pygrabber lança uma exceção (COM error). |

### TestGetMicrophones — Listagem de Microfones

| Teste | Descrição |
|---|---|
| `test_returns_list_of_mics` | Verifica que `get_microphones` retorna apenas dispositivos com canais de entrada, excluindo alto-falantes. |
| `test_removes_duplicates` | Confirma que microfones com nomes duplicados são retornados apenas uma vez. |
| `test_returns_empty_on_error` | Garante que uma exceção do `sounddevice` é tratada gracefulmente, retornando lista vazia. |

### TestGetMicInfo — Detalhes do Microfone

| Teste | Descrição |
|---|---|
| `test_finds_mic_by_name` | Verifica que `get_mic_info` retorna o índice correto do dispositivo de áudio pelo nome. |
| `test_returns_minus_one_when_not_found` | Retorna `-1` quando o nome do microfone procurado não existe na lista de dispositivos. |
| `test_returns_minus_one_on_error` | Garante que uma exceção do `sounddevice` retorna `-1` como fallback seguro. |

### TestGetCameras — Listagem de Câmeras por SO

| Teste | Descrição |
|---|---|
| `test_windows_returns_camera_list` | Em Windows, `get_cameras` usa pygrabber para retornar a lista de dispositivos de entrada. |
| `test_windows_returns_empty_on_error` | Em Windows, se pygrabber falhar, retorna lista vazia e imprime erro. |
| `test_linux_scans_opencv_indices` | Em Linux/Mac, faz scan nos índices do OpenCV e retorna nomes genéricos ("Camera 0", "Camera 1"). |

### TestOpenCamera — Abertura de Câmera

| Teste | Descrição |
|---|---|
| `test_windows_opens_with_dshow` | Em Windows, `open_camera` usa a flag `CAP_DSHOW` (700) para melhor compatibilidade. |
| `test_linux_opens_without_flags` | Em Linux/Mac, `open_camera` abre o dispositivo sem flags adicionais. |

## 4. Gerenciamento de Configurações (`test_config_manager.py`)

**Classe testada:** `ConfigManager` (em `classes/core/config_manager.py`)
**Total de testes:** 14

> **Nota:** Este arquivo usa a fixture `reset_config_manager` (definida localmente) que reseta o Singleton do `ConfigManager` entre cada teste, evitando contaminação de estado.

### TestConfigManagerGet — Leitura de Configurações

| Teste | Descrição |
|---|---|
| `test_get_returns_default_when_key_not_exists` | Verifica que `get()` retorna o valor padrão informado quando a chave não existe no cache. |
| `test_get_returns_value_when_key_exists` | Confirma que `get()` retorna o valor armazenado quando a chave existe no cache. |
| `test_get_returns_none_when_no_default` | Verifica que `get()` retorna `None` quando a chave não existe e nenhum valor padrão é fornecido. |

### TestConfigManagerSetGlobal — Escrita de Configurações Globais

| Teste | Descrição |
|---|---|
| `test_set_global_stores_value` | Testa que `set_global()` armazena o valor no cache e agenda o salvamento via timer de debounce (200ms). |
| `test_set_global_overwrites_existing` | Confirma que `set_global()` substitui o valor de uma chave existente pelo novo valor. |

### TestConfigManagerSetMode — Configurações por Modo/Câmera

| Teste | Descrição |
|---|---|
| `test_set_mode_creates_new_entry` | Verifica que `set_mode()` cria uma nova entrada no cache com todos os campos (`size`, `zoom`, `pan_x`, `pan_y`). |
| `test_set_mode_updates_existing_entry` | Confirma que `set_mode()` atualiza os valores de uma entrada existente e adiciona posição `x`/`y`. |

### TestConfigManagerGetModeConfig — Recuperação de Configurações por Modo

| Teste | Descrição |
|---|---|
| `test_returns_mode_config_when_exists` | Verifica que `get_mode_config()` retorna a configuração específica quando a chave do modo existe. |
| `test_returns_fallback_when_mode_not_exists` | Confirma que `get_mode_config()` usa o modo de fallback quando a chave específica não existe. |
| `test_returns_empty_dict_when_nothing_exists` | Garante que `get_mode_config()` retorna um dicionário vazio quando nem o modo nem o fallback existem. |
| `test_returns_config_for_specific_mode_over_fallback` | Verifica que a configuração específica do modo tem prioridade sobre o fallback genérico. |

### TestConfigManagerSave — Salvamento em Disco

| Teste | Descrição |
|---|---|
| `test_save_now_calls_save` | Confirma que `save_now()` interrompe o timer de debounce e chama `save_all_configs` imediatamente. |
| `test_request_save_starts_timer` | Verifica que `request_save()` agenda o salvamento com debounce de 200ms no `QTimer`. |

### TestConfigManagerReload — Recarregamento

| Teste | Descrição |
|---|---|
| `test_reload_clears_and_updates_configs` | Testa que `reload()` limpa o cache atual e carrega as configurações frescas do disco, removendo dados stale. |

### TestConfigManagerSingleton — Padrão Singleton

| Teste | Descrição |
|---|---|
| `test_singleton_returns_same_instance` | Garante que o padrão Singleton funciona: múltiplas instâncias retornam o mesmo objeto em memória. |

## 5. Análise de Áudio (`test_audio_analyzer.py`)

**Classe testada:** `AudioAnalyzer` (em `classes/core/audio_analyzer.py`)
**Total de testes:** 13

| Teste | Descrição |
|---|---|
| `test_init_with_valid_device` | Verifica que o `AudioAnalyzer` inicializa corretamente com um índice de dispositivo válido, com valores padrão esperados. |
| `test_init_with_invalid_device` | Confirma que o `AudioAnalyzer` aceita dispositivo inválido (`-1`) sem lançar exceção. |
| `test_set_sensitivity` | Testa que `set_sensitivity()` atualiza corretamente o multiplicador de ganho do áudio. |
| `test_set_sensitivity_zero` | Verifica que a sensibilidade pode ser definida como zero (silenciando o áudio). |
| `test_start_with_invalid_device` | Garante que `start()` é um no-op quando o `device_index` é `-1`, sem criar stream. |
| `test_start_creates_stream` | Confirma que `start()` cria um `sd.InputStream` com os parâmetros corretos (`device`, `channels`, `samplerate`, `callback`). |
| `test_start_does_not_create_stream_on_error` | Verifica que uma exceção ao criar o stream é tratada gracefulmente, com mensagem de erro no stdout. |
| `test_stop_closes_stream` | Testa que `stop()` chama `stop()` e `close()` no stream do `sounddevice` e limpa a referência. |
| `test_stop_does_nothing_when_no_stream` | Garante que `stop()` é seguro de chamar quando não há stream ativo (não lança exceção). |
| `test_audio_callback_emits_signal` | Verifica que o callback de áudio calcula o RMS corretamente e atualiza o `current_level` com valor positivo. |
| `test_audio_callback_clamps_to_1` | Confirma que o nível de áudio é limitado a `1.0` (100%) mesmo com sensibilidade extremamente alta. |
| `test_rms_history_smoothing` | Verifica que o buffer de histórico RMS respeita o tamanho máximo (`history_size=5`), aplicando média móvel. |
| `test_stop_handles_stream_close_error` | Garante que `stop()` trata gracefulmente uma exceção ao parar o stream, cobrindo o bloco `except: pass`. |

## 6. Diálogo de Filtragem (`test_filter_dialogs.py`)

**Classe testada:** `FilterDialog` (em `classes/ui/filter_dialogs.py`)
**Total de testes:** 12

| Teste | Descrição |
|---|---|
| `test_dialog_creation` | Verifica que o `FilterDialog` é criado corretamente com o título informado. |
| `test_items_populated_correctly` | Confirma que todos os itens da lista são adicionados ao `QListWidget` na ordem correta. |
| `test_ignored_items_are_checked` | Verifica que itens presentes na lista de ignorados aparecem com checkbox marcado. |
| `test_multiple_ignored_items` | Testa que múltiplos itens na lista de ignorados são marcados corretamente com padrão alternado. |
| `test_get_selected_items_empty_when_none_checked` | Confirma que `get_selected_items()` retorna lista vazia quando nenhum checkbox está marcado. |
| `test_get_selected_items_returns_checked` | Verifica que `get_selected_items()` retorna apenas os nomes dos itens com checkbox marcado. |
| `test_set_all_checks_checked` | Testa que `set_all_checks(Checked)` marca todos os checkboxes da lista simultaneamente. |
| `test_set_all_checks_unchecked` | Testa que `set_all_checks(Unchecked)` desmarca todos os checkboxes, mesmo os que estavam marcados. |
| `test_mark_all_button` | Verifica que clicar no botão "Marcar Todos" marca todos os checkboxes da lista. |
| `test_unmark_all_button` | Verifica que clicar no botão "Desmarcar Todos" desmarca todos os checkboxes da lista. |
| `test_handles_tuple_items` | Confirma que o dialog extrai corretamente o nome de itens no formato tupla `(nome, indice)`. |
| `test_empty_items_list` | Garante que o dialog funciona corretamente quando a lista de itens está vazia. |

## 7. Barra de Ferramentas Flutuante (`test_floating_toolbar.py`)

**Classe testada:** `FloatingToolbar` (em `classes/ui/floating_toolbar.py`)
**Total de testes:** 13

| Teste | Descrição |
|---|---|
| `test_toolbar_creation` | Verifica que a `FloatingToolbar` é criada e inicia oculta (`hide()` é chamado no `__init__`). |
| `test_all_buttons_exist` | Confirma que todos os 8 botões de controle estão presentes na toolbar. |
| `test_close_signal` | Testa que clicar no botão de fechar emite o sinal `close_requested`. |
| `test_resize_plus_signal` | Confirma que o botão "+" emite `resize_requested` com valor positivo (20) para aumentar o widget. |
| `test_resize_minus_signal` | Confirma que o botão "-" emite `resize_requested` com valor negativo (-20) para diminuir o widget. |
| `test_camera_toggle_signal` | Testa que o botão de câmera emite o sinal `camera_toggled` ao ser clicado. |
| `test_mic_toggle_signal` | Testa que o botão de microfone emite o sinal `mic_toggled` ao ser clicado. |
| `test_avatar_toggle_signal` | Testa que o botão de avatar emite o sinal `avatar_toggled` ao ser clicado. |
| `test_format_toggle_signal` | Testa que o botão de formato emite o sinal `format_toggled` ao ser clicado. |
| `test_border_mode_toggle_signal` | Testa que o botão de modo de borda (Discord/áudio) emite o sinal `border_mode_toggled` ao ser clicado. |
| `test_button_tooltips` | Verifica que os botões possuem tooltips informativos indicando o atalho de teclado correspondente. |
| `test_button_sizes` | Confirma que todos os botões têm tamanho fixo de 32x32 pixels, garantindo consistência visual. |
| `test_all_signals_defined` | Verifica que todos os 7 sinais de comunicação com o widget pai estão definidos na classe. |

## 8. Utilitários e I/O (`test_functions.py`)

**Módulo testado:** `utils/functions.py`
**Total de testes:** 16

### TestInitAppEnvironment — Inicialização do Ambiente

| Teste | Descrição |
|---|---|
| `test_creates_avatar_directory` | Verifica que `init_app_environment()` cria o diretório de avatares se ele não existir. |
| `test_calls_migration` | Confirma que `init_app_environment()` executa a função de migração de arquivos antigos. |

### TestMigrateOldFiles — Migração de Arquivos Antigos

| Teste | Descrição |
|---|---|
| `test_skips_migration_when_old_config_not_exists` | Quando `pip_config.json` antigo não existe, `_migrate_old_files()` não executa nenhuma migração. |
| `test_skips_avatar_migration_when_old_dir_not_exists` | Quando a pasta `avatar` antiga não existe, avatares não são migrados. |

### TestLoadAllConfigs — Leitura de Configurações

| Teste | Descrição |
|---|---|
| `test_returns_defaults_when_file_not_exists` | Quando o arquivo não existe, `load_all_configs()` retorna as configurações padrão. |
| `test_loads_existing_file` | Quando o arquivo existe e é válido, retorna seu conteúdo mergeado com os defaults. |
| `test_returns_defaults_on_invalid_json` | Quando o arquivo é JSON inválido, retorna defaults e imprime mensagem de erro. |

### TestSaveAllConfigs — Salvamento de Configurações

| Teste | Descrição |
|---|---|
| `test_creates_directory_and_saves` | `save_all_configs()` cria o diretório base se não existir e salva o JSON corretamente. |
| `test_saves_valid_json` | Confirma que o arquivo salvo é um JSON válido e legível. |
| `test_handles_save_error` | Se ocorrer erro ao salvar (ex: permissões), a exceção é tratada e mensagem é impressa. |

### TestResourcePath — Caminho de Recursos

| Teste | Descrição |
|---|---|
| `test_returns_absolute_path_in_development` | Em modo desenvolvimento, `resource_path` retorna caminho absoluto relativo ao script. |
| `test_returns_path_from_meipass_in_production` | Quando empacotado com PyInstaller, `resource_path` usa `_MEIPASS` como base. |

## Cobertura por Módulo

| Módulo | Cobertura | Status |
|---|---|---|
| `audio_analyzer.py` | **100%** | Completo |
| `config_manager.py` | **100%** | Completo |
| `device_manager.py` | **100%** | Completo |
| `video_processor.py` | **100%** | Completo |
| `shortcut_signals.py` | **100%** | Completo |
| `filter_dialogs.py` | **100%** | Completo |
| `floating_toolbar.py` | **100%** | Completo |
| `functions.py` | 64% | 30 linhas restantes (migração no import) |
| **TOTAL** | **93%** | **125 testes passando** |

## Análise de Qualidade dos Testes

### Falsos Positivos Detectados e Corrigidos

- **`test_min_zoom`** (removido): Duplicava `test_returns_correct_dimensions` com os mesmos parâmetros (zoom=100) e as mesmas asserções.
- **`import pytest` ausente** em `test_shortcut_signals.py`: O arquivo funcionava por importação implícita do pytest, mas foi adicionado para seguir boas práticas.

### Linhas Não Cobertas (`functions.py` — 30 linhas)

As linhas 26-35, 57-59, 64-75 e 79-91 são código de migração que executa **durante o import do módulo** (antes dos testes rodarem) e lógica de `_migrate_old_files` que depende de `os.path.exists` com caminhos hardcoded no momento do import. Para cobrir essas linhas seria necessário fazer reload dinâmico do módulo com `importlib.reload()` combinado com mocks complexos — o que traria mais complexidade do que valor, já que são caminhos de migração que rodam uma única vez na vida real.
