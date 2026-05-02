# Guia de Releases e Versionamento Automático

Este documento descreve o fluxo de trabalho para gerar executáveis (`.exe`) do Windows utilizando **GitHub Actions** e **Git Tags**.

## 1. O Conceito de Tag

No Git, uma **Tag** é um marcador fixo em um ponto específico do seu histórico que você considera importante. Para este projeto, usamos Tags para sinalizar versões estáveis (ex: `v1.0.0`, `v1.1.0`).

O workflow configurado no GitHub Actions monitora a criação dessas Tags para disparar o processo de build e publicação.

## 2. Passo a Passo para Gerar uma Release

Sempre que o projeto estiver pronto para uma nova versão, siga estes comandos no seu terminal:

### Passo A: Commitar as alterações

Certifique-se de que todo o seu código refatorado e os novos workflows foram enviados para o repositório.

```bash
git add .
git commit -m "feat(ci): implementa automação de releases via tags"
git push origin main
```

### Passo B: Criar a Tag de versão

Escolha um número de versão seguindo o padrão `vX.Y.Z`.

```bash
# Cria a tag localmente
git tag v1.0.0
```

### Passo C: Enviar a Tag para o GitHub

É este comando que "ativa" a Action de Build e Release.

```bash
# Envia a tag específica para o servidor
git push origin v1.0.0
```

## 3. O que acontece nos bastidores (CI/CD)

Assim que o comando `git push origin v1.0.0` é executado, o GitHub Actions segue esta rotina:

1. **Provisionamento**: Inicia uma máquina virtual com **Windows Latest**.
2. **Ambiente**: Instala o **uv**, configura o **Python 3.12** e sincroniza as dependências.
3. **Compilação**: Executa o **PyInstaller**, embutindo as pastas `classes` e `utils` no binário.
4. **Publicação**:
    * Cria uma nova entrada na aba **Releases** do repositório.
    * Nomeia a release como "Release v1.0.0".
    * Faz o upload do arquivo `PiPCamPro.exe` como um artefato pronto para download.

## 4. Revisão de Comandos Úteis

| Comando | Descrição |
| :--- | :--- |
| `git tag` | Lista todas as tags criadas no projeto. |
| `git tag -d v1.0.0` | Apaga uma tag local (caso tenha errado o nome). |
| `git push origin --delete v1.0.0` | Apaga uma tag que já foi enviada para o GitHub. |
| `git show v1.0.0` | Mostra os detalhes e o commit atrelado àquela tag. |

## 5. Dicas de Versionamento (Semantic Versioning)

Para manter o projeto organizado, seguir esta lógica para os números:

* **v1.0.0**: Primeira versão estável.
* **v1.0.1 (Patch)**: Quando você apenas corrige um bug (fix).
* **v1.1.0 (Minor)**: Quando você adiciona uma nova funcionalidade (feat).
* **v2.0.0 (Major)**: Quando há uma mudança incompatível ou uma refatoração total da interface.

## 6. Commits a partir de versões

Para listar commits a partir de alguma versão. (para os PRs).

Comando: `git log <versao>..HEAD --oneline`

Exemplo: `git log v1.2.3.1-alpha..HEAD --oneline`
