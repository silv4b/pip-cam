<!-- markdownlint-disable MD033 MD045 -->

# PiP Cam

<p align="center"> <img src="assets/pipcam_icon.ico" width="100"></p>

PiP (Picture-in-Picture) Cam é um widget de câmera flutuante desenvolvido com Python 3.12+ e PyQt6. Oferece uma sobreposição de webcam/câmeras customizável para criadores de conteúdo e apresentações de tela.

## Funcionalidades Principais

* Formatos Geométricos: Suporte para Círculo, Proporção 1:1 e Proporção 4:3 com margens suavizadas anti-aliasing.
* Personalização Visual: Borda colorida definida pelo usuário (HEX ou utilitário visual).
* Modo Avatar: Alterna em real-time renderização vinda da câmera para sua foto offline de Avatar.
* Zoom e Pan: Ajuste de zoom e alinhamento Y da imagem.
* Memória de Estado: O aplicativo arquiva e recarrega os tamanhos/posições por formato individualmente, além de persistir a paleta de cores, a foto do avatar escolhida no sistema local e com qual alternador do app ("Vídeo" vs "Avatar") a preferência foi encerrada na última partida.
* Posicionamento Inteligente: Centralização automática baseada na resolução do monitor caso não existam dados salvos.
* Atalhos Globais (Hotkeys):
  * `Alt + +` : Aumentar tamanho.
  * `Alt + -` : Diminuir tamanho.
  * `Alt + S` : Alternar visibilidade (Mostrar/Esconder).
  * `Alt + A` : Transição entre Modo Câmera e Modo Avatar.
  * `Esc`: Fechar widget.
* Launcher de Configuração:
  * Identificação de hardware via DirectShow.
  * Seletor integrado para os ajustes de dimensão com autocompletar da última sessão fechada, seletores dinâmicos de arquivos fotográficos e paleta.

## Requisitos e Instalação

### 1. Requisitos do Sistema

* Sistema Operacional: Windows 10 ou 11. (atualemente).
* Python: Versão 3.12 (recomendada).

### 2. Dependências

#### Sistema

* opencv-python
* PyQt6
* pygrabber
* keyboard

#### Desenvolvimento

* poethepoet
* pyinstaller

### 3. Instalação via UV

```bash
uv sync
uv run main.py
```

## Instruções de Uso

1. Launcher: Selecione a câmera e o formato visual desejado. Ajuste a largura inicial da montagem, escolha a cor da borda e anexe um diretório de uma foto de Avatar para transições rápidas em live. O software cuida de salvar as informações para o próximo uso.
2. Interação no Widget:
    * Mover: Clique e arraste de qualquer parte interna ou bordas limitantes do visual.
    * Redimensionar: O painel flutuante que surge da base com margem dinâmica, ou por comandos atrelados ao teclado.
    * Fechar: Utilize o botão ✕ ou o seu `Esc`.
3. Dinâmica em Gravações:
    * Ocultamento (`Alt + S`): permite ocultar a câmera e trazê-la de forma fluida nos exatos frames X e Y onde elas residiam por encobrimento de UI.
    * Bypass Visual (`Alt + A`): alterna em real-time renderização vinda da câmera para sua foto offline de Avatar.
