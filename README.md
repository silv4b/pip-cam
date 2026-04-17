# PiP Cam

PiP Cam é um widget de câmera flutuante (Picture-in-Picture) desenvolvido com Python 3.12+ e PyQt6. Oferece uma sobreposição de webcam customizável para criadores de conteúdo e apresentações de tela.

## Funcionalidades Principais

* Formatos Geométricos: Suporte para Círculo, Quadrado (1:1) e Retângulo (4:3) com bordas arredondadas.
* Memória de Estado: O aplicativo armazena a última posição, tamanho e formato individualmente para cada modo.
* Posicionamento Inteligente: Centralização automática baseada na resolução do monitor caso não existam dados salvos.
* Atalhos Globais (Hotkeys):
  * `Alt + =` : Aumentar tamanho.
  * `Alt + -` : Diminuir tamanho.
  * `Alt + S` : Alternar visibilidade (Mostrar/Esconder).
  * `Esc`: Fechar widget.
* Launcher de Configuração:
  * Identificação de hardware via DirectShow.
  * Campo de largura inicial editável com validação numérica.
  * Sincronização de dados ao fechar o widget.

## Requisitos e Instalação

### 1. Requisitos do Sistema

* Sistema Operacional: Windows 10 ou 11.
* Python: Versão 3.12 recomendada.

### 2. Dependências

* opencv-python
* PyQt6
* pygrabber
* keyboard

### 3. Instalação via UV

```bash
uv add opencv-python pyqt6 pygrabber keyboard
uv sync
uv run main.py
```

## Instruções de Uso

1. Launcher: Selecione a câmera e o formato. O campo de largura será preenchido com o último valor salvo para aquele modo.
2. Interação no Widget:
    * Mover: Clique e arraste o widget.
    * Redimensionar: Utilize os botões flutuantes ou os atalhos de teclado.
    * Fechar: Utilize o botão X ou a tecla Esc.
3. Fluxo: O atalho Alt + S permite ocultar a câmera durante gravações sem encerrar o processo, mantendo a posição exata ao reaparecer.

## Notas Técnicas

* Execução como Administrador: Pode ser necessário para o funcionamento correto dos atalhos globais em sistemas com restrições de segurança.
* Estabilidade: Utiliza sistema de sinais (Signals) do Qt para garantir que comandos externos não causem instabilidade na thread principal de interface.
