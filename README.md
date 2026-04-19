<!-- markdownlint-disable MD033 MD045 -->

# PiP Cam

![GitHub License](https://img.shields.io/github/license/henriquesebastiao/badges?style=flat&color=22c55e)
![Release](https://img.shields.io/github/v/release/silv4b/pip-cam)
![Windows](https://img.shields.io/badge/Windows-0078D6?style=flat&logo=windows&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?style=flat&logo=python&logoColor=white)

<p align="center"> <img src="assets/pipcam_icon.png" width="70"></p>

PiP (Picture-in-Picture) Cam é um widget de câmera flutuante inteligente desenvolvido com Python 3.12+ e PyQt6. Oferece uma sobreposição de webcam customizável e interativa para criadores de conteúdo, streamers e apresentações.

| PiP Cam Setup                     | PiP Cam Widget                          |
|:---------------------------------:|:---------------------------------------:|
| ![example](/assets/pipcamwin.png) | ![example](/assets/pipcamwinavatar.png) |

## Funcionalidades Principais

* **Formatos Geométricos**: Suporte para Círculo, Quadrado (1:1) e Retângulo (4:3).
* **Suporte Multi-Câmeras**: Abra múltiplas instâncias de diferentes câmeras simultaneamente.
* **Sinalizador de Áudio**: Borda inteligente que reage à sua voz (estilo Discord).
* **Modo Slim (Minimalista)**: Opção de ocultar controles flutuantes para uma experiência focada 100% em atalhos.
* **Filtro de Descarte**: Oculte câmeras ou microfones indesejados (⚙️) da listagem.
* **Modo Avatar**: Troca instantânea entre webcam e sua foto de perfil (Alt+A).
* **Memória Inteligente**:
  * Salva Zoom, Pan e Tamanho individualmente **por câmera**.
  * Lembra o último formato, posição e comportamento do app.

## Atalhos Globais

| Atalho    | Ação                                       |
|:---------:|--------------------------------------------|
| `Alt + S` | Mostrar / Ocultar Widgets (Fade fluído)    |
| `Alt + C` | Alternar entre Câmeras (Ciclo inteligente) |
| `Alt + M` | Mutar / Desmutar Áudio (Sinalizador Visual)|
| `Alt + A` | Alternar entre Vídeo e Avatar              |
| `Alt + F` | Alternar os shapes do widget               |
| `Alt + D` | Alternar entre os comportamentos da borda  |
| `Alt + +` | Aumentar tamanho do widget                 |
| `Alt + -` | Diminuir tamanho do widget                 |
| `Esc`     | Fechar widget                              |

## Requisitos e Instalação

### 1. Requisitos

* Windows 10 ou 11.
* Python 3.12+.

### 2. Instalação via [uv](https://github.com/astral-sh/uv)

> Caso não tenha o uv em sua máquina, link para instalação [aqui](https://docs.astral.sh/uv/getting-started/installation/).

```bash
uv sync
uv run main.py
```

## Instruções de Uso

1. **Configuração**: Use o Launcher para selecionar sua câmera. Ative o **Modo Multi-Câmeras** se quiser abrir mais de uma janela.
2. **Modo Slim**: Se não quiser que os botões apareçam ao passar o mouse, ative **"Ocultar controles flutuantes"**.
3. **Broadcast**: Use os atalhos globais para controlar todas as suas câmeras abertas de uma só vez.
4. **Interação**:
    * **Mover**: Clique e arraste o widget livremente.
    * **Personalizar**: Ajuste o zoom e pan no launcher; eles serão lembrados para cada câmera específica.

## Disclaimer

A versão que está em release no momento é a [v1.2.0](https://github.com/silv4b/pip-cam/releases/tag/v1.2.0), e ela pode estar desatualizada em relação ao código fonte, pois o projeto está em desenvolvimento ativo, logo, podendo haver funcionalidades ou correções de bugs no código atual, que não estão na versão de release. Para testar o projeto em seu estado mais atualizado, siga os passos de instalação. PRs são sempre bem vindos.
