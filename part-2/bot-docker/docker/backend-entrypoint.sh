#!/bin/sh
set -eu

python - <<'PY'
import os
import sys
import time

import psycopg

timeout = int(os.environ.get("DB_STARTUP_TIMEOUT", "60"))
deadline = time.monotonic() + timeout
params = {
    "host": os.environ.get("POSTGRES_HOST", "db"),
    "port": int(os.environ.get("POSTGRES_PORT", "5432")),
    "dbname": os.environ.get("POSTGRES_DB", "postgres"),
    "user": os.environ.get("POSTGRES_USER", "postgres"),
    "password": os.environ.get("POSTGRES_PASSWORD", ""),
}
last_error = None

while time.monotonic() < deadline:
    try:
        with psycopg.connect(**params):
            print("PostgreSQL is available.", flush=True)
            break
    except psycopg.Error as exc:
        last_error = exc
        print("Waiting for PostgreSQL...", file=sys.stderr, flush=True)
        time.sleep(2)
else:
    raise SystemExit(f"Timed out waiting for PostgreSQL after {timeout}s: {last_error}")
PY

knowledge_path="${KNOWLEDGE_FILE_PATH:-/app/data/knowledge}"
python scripts/reindex_kb.py "$knowledge_path"

exec "$@"
