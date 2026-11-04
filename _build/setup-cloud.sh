#!/usr/bin/env bash
# Prepara uma sessão nova (claude.ai/code na nuvem, ou um clone novo no computador) para gerar e testar a app.
#  1. instala o Playwright e o Chromium (para os testes);
#  2. descarrega o espelho da API para _build/mirror/ e o calendário oficial para _build/data/fixtures.json,
#     e confere a última jornada contra a API oficial.
# Uso (a partir da raiz do repositório):  bash _build/setup-cloud.sh
# Pode correr-se mais de uma vez (só refaz o que for preciso).
set -u
cd "$(dirname "$0")/.."

# Python: python3 no Linux; no Windows (Git Bash) o python3 pode ser só o atalho da Microsoft Store → usar py
if python3 -c "import sys" >/dev/null 2>&1; then PY=python3; elif command -v py >/dev/null 2>&1; then PY=py; else PY=python; fi
echo "== Python: $($PY --version 2>&1)"

echo "== Playwright"
if ! $PY -c "import playwright" >/dev/null 2>&1; then
  $PY -m pip install -q playwright || $PY -m pip install -q --user playwright || $PY -m pip install -q --break-system-packages playwright
fi
# Chromium: com as dependências do sistema quando der (Linux); senão só o browser
$PY -m playwright install --with-deps chromium >/dev/null 2>&1 || $PY -m playwright install chromium || echo "AVISO: o Chromium não ficou instalado (os testes não vão correr)"

echo "== Espelho da API e calendário oficial"
$PY -X utf8 _build/pool/espelho.py
rc=$?
if [ $rc -ne 0 ]; then echo "AVISO: espelho.py acabou com código $rc (ver a mensagem acima)"; fi

echo "== Pronto. Próximo passo: git pull (live.json mais recente da GitHub Action) e ler o CLAUDE.md."
exit 0
