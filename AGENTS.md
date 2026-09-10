# AGENTS.md

Diretrizes para agentes que trabalham neste repositório.

## Commits em Lotes

Sempre que houver múltiplas mudanças não relacionadas, organize os commits em lotes independentes, cada um seguindo a convenção semantic release (em pt-BR):

- `feat:` — novas funcionalidades
- `fix:` — correções de bugs
- `chore:` — tarefas de manutenção (formatação, lint, dependências)
- `docs:` — alterações de documentação
- `refactor:` — refatorações sem mudança de comportamento
- `test:` — adição/ajuste de testes

Regras:

1. Agrupe mudanças relacionadas no mesmo commit; separe mudanças de naturezas diferentes.
2. Escreva a mensagem em português, de forma concisa, no imperativo.
3. Se mudanças em um mesmo arquivo forem de naturezas diferentes (ex.: `feat` e `fix` intercalados no mesmo arquivo), combine em um único commit coerente.
4. Não faça commit sem que o usuário peça explicitamente.
5. Antes de commitar, rode `uv run ruff check .` e `.venv\Scripts\python.exe -m pytest tests/ --tb=short -q`.

## Verificação

- Lint: `uv run ruff check .`
- Testes: `.venv\Scripts\python.exe -m pytest tests/ --tb=short -q`
  - Nota: `uv run pytest` falha com erro de trampoline no Windows; use o python do venv.
