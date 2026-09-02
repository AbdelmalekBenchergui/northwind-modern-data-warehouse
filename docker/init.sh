#!/usr/bin/env bash
set -e

echo "==> Running Superset database migrations..."
superset db upgrade

echo "==> Initializing roles/permissions..."
superset init

echo "==> Bootstrapping admin user (skips if it already exists)..."
superset fab create-admin \
    --username "${ADMIN_USERNAME:-admin}" \
    --firstname Admin \
    --lastname User \
    --email "${ADMIN_EMAIL:-admin@northwind.example}" \
    --password "${ADMIN_PASSWORD:-admin}" \
    || echo "Admin user already present, continuing."

echo "==> Starting Superset on :8088..."
exec superset run -p 8088 -h 0.0.0.0 --with-threads --reload --debugger