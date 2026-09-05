#!/usr/bin/env bash

set -Eeuo pipefail

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)"

FAILURES=0

ok() {
    printf '[OK] %s\n' "$1"
}

fail() {
    printf '[FAIL] %s: %s\n' "$1" "$2" >&2
    FAILURES=$((FAILURES + 1))
}

config_error() {
    printf '[FAIL] %s\n' "$1" >&2
    exit 2
}

cd "$REPO_ROOT"

# Load repository configuration without printing it.
if [[ -f "$REPO_ROOT/.env" ]]; then
    set -a
    # shellcheck disable=SC1091
    source "$REPO_ROOT/.env" || config_error "Unable to load .env"
    set +a
fi

# Application defaults documented by the repository.
: "${OLLAMA_BASE_URL:=http://localhost:11434}"
: "${OLLAMA_MODEL:=gemma4}"
: "${VITE_API_BASE_URL:=http://localhost:8000}"

export OLLAMA_BASE_URL OLLAMA_MODEL VITE_API_BASE_URL

# These are required by the application's Settings.
[[ -n "${DATABASE_URL:-}" ]] || config_error "DATABASE_URL is not set"

command -v curl >/dev/null 2>&1 || config_error "curl is required"

if [[ -x "$REPO_ROOT/backend/.venv/bin/python" ]]; then
    PYTHON_BIN="$REPO_ROOT/backend/.venv/bin/python"
else
    PYTHON_BIN="$(command -v python3 || command -v python || true)"
fi

[[ -n "$PYTHON_BIN" ]] || config_error "Python is required"

if [[ -x "$REPO_ROOT/backend/.venv/bin/alembic" ]]; then
    ALEMBIC_BIN="$REPO_ROOT/backend/.venv/bin/alembic"
else
    ALEMBIC_BIN="$(command -v alembic || true)"
fi

[[ -n "$ALEMBIC_BIN" ]] || config_error "Alembic is required"

# ------------------------------------------------------------
# 1. PostgreSQL
# ------------------------------------------------------------
if "$PYTHON_BIN" - <<'PY' >/dev/null 2>&1
import asyncio
import os

import asyncpg

dsn = os.environ["DATABASE_URL"].replace(
    "postgresql+asyncpg://",
    "postgresql://",
    1,
)

async def main() -> None:
    conn = await asyncpg.connect(dsn=dsn, timeout=5)
    try:
        value = await conn.fetchval("SELECT 1")
        if value != 1:
            raise RuntimeError("unexpected database response")
    finally:
        await conn.close()

asyncio.run(main())
PY
then
    ok "PostgreSQL"
else
    fail "PostgreSQL" "database connection failed"
fi

# ------------------------------------------------------------
# 2. Alembic migration state
# ------------------------------------------------------------
CURRENT_OUTPUT=""
HEADS_OUTPUT=""

CURRENT_RC=0
HEADS_RC=0

CURRENT_OUTPUT="$(
    cd "$REPO_ROOT/backend"
    "$ALEMBIC_BIN" current 2>/dev/null
)" || CURRENT_RC=$?

HEADS_OUTPUT="$(
    cd "$REPO_ROOT/backend"
    "$ALEMBIC_BIN" heads 2>/dev/null
)" || HEADS_RC=$?

if [[ "$CURRENT_RC" -ne 0 || "$HEADS_RC" -ne 0 ]]; then
    fail "migrations" "unable to read Alembic migration state"
else
    CURRENT_OUTPUT="$CURRENT_OUTPUT" \
    HEADS_OUTPUT="$HEADS_OUTPUT" \
    "$PYTHON_BIN" - <<'PY' >/dev/null 2>&1
import os
import re

current_text = os.environ["CURRENT_OUTPUT"]
heads_text = os.environ["HEADS_OUTPUT"]

current_match = re.search(
    r"Current revision\(s\):\s*(.+)",
    current_text,
)

if current_match:
    current_revisions = set(
        re.findall(
            r"\b[0-9a-f]{7,40}\b",
            current_match.group(1),
        )
    )
else:
    current_revisions = set(
        re.findall(
            r"^\s*([0-9a-f]{7,40})\b",
            current_text,
            re.MULTILINE,
        )
    )

head_revisions = set(
    re.findall(
        r"^\s*([0-9a-f]{7,40})\s+\(head\)\s*$",
        heads_text,
        re.MULTILINE,
    )
)

if current_revisions and head_revisions and current_revisions == head_revisions:
    raise SystemExit(0)

raise SystemExit(1)
PY

    if [[ "$?" -eq 0 ]]; then
        ok "migrations"
    else
        fail "migrations" "database revision does not match repository heads"
    fi
fi

# ------------------------------------------------------------
# 3. Backend
BACKEND_URL="${VITE_API_BASE_URL%/}"
# ------------------------------------------------------------
if curl -fsS --max-time 5 \
    -o /dev/null \
    "$BACKEND_URL/health"
then
    ok "backend"
else
    fail "backend" "GET "$BACKEND_URL/health" failed"
fi

# ------------------------------------------------------------
# 4. Ollama
# ------------------------------------------------------------
OLLAMA_URL="${OLLAMA_BASE_URL%/}"

# Avoid localhost/IPv6 ambiguity when the configured URL is localhost.
if [[ "$OLLAMA_URL" == "http://localhost:11434" ]]; then
    OLLAMA_URL="http://127.0.0.1:11434"
fi

OLLAMA_RESPONSE=""

if OLLAMA_RESPONSE="$(
    curl -fsS --max-time 5 \
        "$OLLAMA_URL/api/tags" 2>/dev/null
)"
then
    ok "Ollama"
else
    fail "Ollama" "GET /api/tags failed"
fi

# ------------------------------------------------------------
# 5. Ollama model
# ------------------------------------------------------------
if [[ -n "$OLLAMA_RESPONSE" ]]; then
    if OLLAMA_RESPONSE="$OLLAMA_RESPONSE" \
        OLLAMA_MODEL="$OLLAMA_MODEL" \
        "$PYTHON_BIN" - <<'PY' >/dev/null 2>&1
import json
import os

payload = json.loads(os.environ["OLLAMA_RESPONSE"])
configured = os.environ["OLLAMA_MODEL"]

def with_default_latest(name: str) -> str:
    last_segment = name.rsplit("/", 1)[-1]
    if ":" not in last_segment:
        return f"{name}:latest"
    return name

expected = with_default_latest(configured)

for model in payload.get("models", []):
    name = model.get("name") or model.get("model")
    if isinstance(name, str) and with_default_latest(name) == expected:
        raise SystemExit(0)

raise SystemExit(1)
PY
    then
        ok "Ollama model"
    else
        fail "Ollama model" "configured model is not available"
    fi
else
    fail "Ollama model" "model list is unavailable"
fi

# ------------------------------------------------------------
# 6. Frontend HTTP
# ------------------------------------------------------------
FRONTEND_OK=0

for FRONTEND_URL in \
    "http://localhost:5173/" \
    "http://127.0.0.1:5173/"
do
    if curl -fsS --max-time 5 \
        -o /dev/null \
        "$FRONTEND_URL"
    then
        FRONTEND_OK=1
        break
    fi
done

if [[ "$FRONTEND_OK" -eq 1 ]]; then
    ok "Frontend HTTP"
else
    fail "Frontend HTTP" \
        "Vite dev server is not reachable at the documented default port"
fi

# ------------------------------------------------------------
# Final result
# ------------------------------------------------------------
if [[ "$FAILURES" -eq 0 ]]; then
    exit 0
fi

exit 1
