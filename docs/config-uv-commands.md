<!-- markdownlint-disable MD001 -->

# Wrapper para comandos `uv`

Em meus ambientes de desenvolvimento, costumo usar o `uv` em conjunto com o `poethepoet`, de forma que no arquivo `pyproject.toml`, eu possa criar meus próprios scripts de comandos. O `poethepoet` é uma ferramenta que permite criar tarefas (tasks) em Python que serão executadas pelo `uv`.

Em uma instalação em nível de projeto, você precisará prefixar os comandos com `uv run` (por exemplo, `uv run poe test`). Para evitar o uso excessivo de `uv run poe <comando>`, criei um `wrapper` (função) que executa os comandos diretamente.

### No Windows

```powershell
function uv {
    $uvBuiltins = @('add', 'remove', 'export', 'sync', 'lock', 'init', 'venv', 'python', 'run', 'tool', 'self', 'help', 'pip')
    $uvPath = (Get-Command uv -CommandType Application).Source

    if ($args.Count -gt 0 -and $args[0] -notin $uvBuiltins) {
        # Em vez de 'run poe', usamos 'run python -m poethepoet'
        # Isso contorna o erro 4551 pois o Windows confia no executável do Python
        & $uvPath run python -m poethepoet @args
    }
    else {
        # Comandos nativos do uv passam direto
        & $uvPath @args
    }
}
```

Essa função deve ser criada no seu arquivo de `.profile` do powershell, o `$PROFILE`. Esse arquivo pode ser acessado com um `code $PROFILE` no powershell.

### No Linux/Mac

Alternativamente, caso o projeto seja executado em um ambiente linux/mac, onde o `uv` seja um executável em nível de usuário, a função deve ser adicionada ao arquivo de profile do `bash` ou `zsh`.

```bash
uv() {
    # Lista de comandos nativos
    local uv_builtins=("add" "remove" "export" "sync" "lock" "init" "venv" "python" "run" "tool" "self" "help" "pip")

    # Se não houver argumentos, apenas chama o uv real
    if [ $# -eq 0 ]; then
        command uv
        return
    fi

    # Lógica: Se o primeiro argumento NÃO está na lista E não começa com "-"
    if [[ ! " ${uv_builtins[@]} " =~ " $1 " ]] && [[ ! "$1" =~ ^- ]]; then
        # Executa via Poe
        command uv run poe "$@"
    else
        # Executa o comando UV original
        command uv "$@"
    fi
}
```

### Exemplo de arquivo `pyproject.toml`

Após feitas essas configurações, basta abrir um novo terminal e os comandos funcionarão diretamente, sem necessidade de prefixar com `uv run poe`. Para um exemplo completo, veja o arquivo `pyproject.toml` deste projeto.

No exemplo abaixo, estou configurando tarefas para o `coverage` e `pytest`.

```toml
...

[tool.poe.tasks]
cov-run = "uv run coverage run -m pytest"

...
```

Com isso, basta usar `uv cov-run` em vez de `uv run poe cov-run` ou mesmo `uv run coverage run -m pytest`.
