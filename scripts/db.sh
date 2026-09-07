#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
pap_pg_bin="${PG_BIN:-/Applications/Postgres.app/Contents/Versions/latest/bin}"
pap_pg_data="$PWD/.cache/postgres"

if [[ ! -x "$pap_pg_bin/pg_ctl" ]]; then
  echo "Set PG_BIN to your PostgreSQL bin directory (with pgvector installed)." >&2
  exit 1
fi

case "${1:-}" in
  up)
    mkdir -p .cache
    if [[ ! -f "$pap_pg_data/PG_VERSION" ]]; then
      "$pap_pg_bin/initdb" -D "$pap_pg_data" -U pap --encoding=UTF8 \
        --auth=scram-sha-256 --pwfile=<(printf '%s\n' pap_local_only)
    fi
    if ! "$pap_pg_bin/pg_ctl" -D "$pap_pg_data" status >/dev/null 2>&1; then
      "$pap_pg_bin/pg_ctl" -D "$pap_pg_data" -l "$pap_pg_data/server.log" \
        -o "-h 127.0.0.1 -p 55432 -c unix_socket_directories=''" -w start
    fi
    unset PGHOSTADDR PGSERVICE PGSERVICEFILE
    export PGHOST=127.0.0.1 PGPORT=55432 PGUSER=pap PGPASSWORD=pap_local_only
    if [[ "$("$pap_pg_bin/psql" -X -v ON_ERROR_STOP=1 -d postgres -tAc \
      "SELECT 1 FROM pg_database WHERE datname = 'pap'")" != "1" ]]; then
      "$pap_pg_bin/createdb" pap
    fi
    ;;
  down)
    if "$pap_pg_bin/pg_ctl" -D "$pap_pg_data" status >/dev/null 2>&1; then
      "$pap_pg_bin/pg_ctl" -D "$pap_pg_data" -m fast -w stop
    fi
    ;;
  *) echo "Usage: bash scripts/db.sh up|down" >&2; exit 1 ;;
esac
