#!/usr/bin/env bash
set -e

# Make sure the dbt profile used by the DAGs exists and points at the
# shared warehouse path (/opt/airflow/target == host ./target).
PROFILES_DIR="${DBT_PROFILES_DIR:-/opt/airflow/profiles}"
PROFILE="${PROFILES_DIR}/profiles.yml"

if [ ! -f "${PROFILE}" ]; then
  cat > "${PROFILE}" <<YAML
northwind:
  target: duckdb
  outputs:
    duckdb:
      type: duckdb
      path: /opt/airflow/target/northwind.duckdb
      threads: 4
YAML
  echo "generated ${PROFILE}"
else
  echo "dbt profile present: ${PROFILE}"
fi

# Pre-fetch dbt hub packages (dbt_utils) so the first DAG run does not need
# network access.
cd /opt/airflow
dbt deps --profiles-dir "${PROFILES_DIR}" || echo "dbt deps completed (or cached)"