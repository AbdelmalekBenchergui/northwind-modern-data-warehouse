from __future__ import annotations

import os
from pathlib import Path

import requests
from airflow.hooks.base import BaseHook

PROJECT_DIR = Path("/opt/airflow")
PROFILE_DIR = PROJECT_DIR / "profiles"
SCRIPTS_DIR = PROJECT_DIR / "project-scripts"
SEEDS_DIR = PROJECT_DIR / "seeds"

WAREHOUSE_DB = str(PROJECT_DIR / "target" / "northwind.duckdb")
BI_DB = "/data/northwind_bi.duckdb"


def dbt_environment() -> dict[str, str]:
    return {
        "DBT_PROFILES_DIR": str(PROFILE_DIR),
        "PATH": os.environ.get("PATH", ""),
        "DBT_USE_EXPERIMENTAL_PARSER": "True",
    }


def _superset_session(conn, base: str) -> requests.Session:
    session = requests.Session()
    login = session.post(
        f"{base}/api/v1/security/login",
        json={
            "username": conn.login,
            "password": conn.password,
            "provider": "db",
            "refresh": True,
        },
        timeout=60,
    )
    login.raise_for_status()
    session.headers.update(
        {"Authorization": f"Bearer {login.json()['access_token']}"}
    )
    csrf = session.get(
        f"{base}/api/v1/security/csrf_token/"
    ).json().get("result", "")
    if csrf:
        session.headers.update({"X-CSRFToken": csrf})
    return session


def warm_superset_dashboard(dashboard_id: int = 1) -> str:
    conn = BaseHook.get_connection("superset")
    base = f"http://{conn.host}:{conn.port}"
    session = _superset_session(conn, base)

    listed = session.get(f"{base}/api/v1/dashboard/{dashboard_id}/charts").json()
    chart_ids = [c.get("id") for c in listed.get("result", [])]

    result: list[tuple[int, int, str]] = []
    for cid in chart_ids:
        r = session.put(
            f"{base}/api/v1/chart/warm_up_cache",
            json={"chart_id": cid, "dashboard_id": dashboard_id},
            timeout=120,
        )
        body = r.text[:200]
        result.append((cid, r.status_code, body))

    summary = "; ".join(
        f"chart {cid} -> {code}: {body}" for cid, code, body in result
    )
    return f"warmed {len(chart_ids)} chart(s) on dashboard {dashboard_id}\n{summary}"
