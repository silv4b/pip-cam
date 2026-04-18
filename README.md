<!-- markdownlint-disable MD033 MD045 -->

# PiP Cam

![GitHub License](https://img.shields.io/github/license/henriquesebastiao/badges?style=flat&color=22c55e)
![Release](https://img.shields.io/github/v/release/silv4b/pip-cam)
![Windows](https://img.shields.io/badge/Windows-0078D6?style=flat&logo=windows&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?style=flat&logo=python&logoColor=white)

<p align="center"> <img src="assets/pipcam_icon.png" width="60"></p>

PiP (Picture-in-Picture) Cam é um widget de câmera flutuante inteligente desenvolvido com Python 3.12+ e PyQt6. Oferece uma sobreposição de webcam customizável e interativa para criadores de conteúdo, streamers e apresentações.

| PiP Cam Setup                     | PiP Cam Widget                          |
|:---------------------------------:|:---------------------------------------:|
| ![example](/assets/pipcamwin.png) | ![example](/assets/pipcamwinavatar.png) |

## Funcionalidades Principais

* **Formatos Geométricos**: Suporte para Círculo, Quadrado (1:1) e Retângulo (4:3) com anti-aliasing.
* **Sinalizador de Áudio**: Borda inteligente que reage à sua voz (Cinza = Silêncio, Verde = Falando, Vermelho = Mutado).
* **Filtro de Hardware**: Oculte câmeras ou microfones indesejados (como câmeras virtuais ou entradas de áudio vazias) através do seletor dedicado (⚙️).
* **Memória Inteligente**:
  * Salva Zoom, Pan e Tamanho individualmente **por câmera**.
  * Lembra o último formato, posição e comportamento do app em tempo real.
* **Modo Avatar**: Troca instantânea entre a webcam e uma foto de perfil customizada.
* **Toolbar Flutuante**: Painel centralizado que aparece ao passar o mouse, com acesso rápido a todos os controles.

## Atalhos Globais (Hotkeys)

| Atalho    | Ação                                        |
|:---------:|---------------------------------------------|
| `Alt + S` | Mostrar / Ocultar Widget (Fade fluído)      |
| `Alt + C` | Alternar entre Câmeras (Ciclo inteligente)  |
| `Alt + M` | Mutar / Desmutar Áudio (Sinalizador Visual) |
| `Alt + A` | Alternar entre Vídeo e Avatar               |
| `Alt + +` | Aumentar tamanho do widget                  |
| `Alt + -` | Diminuir tamanho do widget                  |
| `Esc`     | Fechar widget                               |

## Requisitos e Instalação

### 1. Requisitos

* Windows 10 ou 11.
* Python 3.12+.

### 2. Instalação via [UV](https://github.com/astral-sh/uv)

```bash
uv sync
uv run main.py
```

## Instruções de Uso

1. **Configuração**: Use o Launcher para selecionar sua câmera e microfone. Clique em ⚙️ para esconder dispositivos que você não usa. Escolha entre "Cor Sólida" ou "Sinalizador de Áudio" para a borda.
2. **Interação**:
    * **Mover**: Clique e arraste o widget para qualquer lugar da tela.
    * **Ajustar**: Use a barra flutuante central para redimensionar ou alternar modos com o mouse.
    * **Persistência**: Qualquer ajuste de zoom ou posição é salvo automaticamente para aquela câmera específica.
3. **Stream/Gravação**: Use `Alt + S` para "sumir" com a câmera durante a live e `Alt + C` para trocar de ângulo sem precisar reabrir o app.
