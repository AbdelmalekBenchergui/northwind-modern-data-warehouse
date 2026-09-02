#!/usr/bin/env python3

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import duckdb
import requests

PROJECT_ROOT = Path(__file__).resolve().parent.parent
BI_DB = PROJECT_ROOT / "data" / "northwind_bi.duckdb"
ANALYSES_DIR = PROJECT_ROOT / "analyses"

BASE_URL = os.environ.get("SUPERSET_BASE", "http://localhost:8088")
USERNAME = os.environ.get("SUPERSET_USER", "admin")
PASSWORD = os.environ.get("SUPERSET_PASSWORD", "admin")

ANALYSIS_SPEC = {
    "ca_par_categorie.sql": ("category_name", "SUM(revenue)"),
    "ca_par_pays.sql": ("customer_country", "SUM(revenue)"),
    "ca_par_transporteur.sql": ("shipper_company_name", "SUM(revenue)"),
    "ca_par_mois.sql": ("order_date_month", "SUM(revenue)"),
}

SPECIAL_ANALYSES = [
    "ca_cumule_par_mois.sql",
    "ca_par_vendeur.sql",
    "part_de_marche_categorie.sql",
    "top_10_produits.sql",
]


class SupersetClient:
    def __init__(self, base: str) -> None:
        self.base = base.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        r = self.session.post(
            self.base + "/api/v1/security/login",
            json={"username": USERNAME, "password": PASSWORD,
                  "provider": "db", "refresh": True},
        )
        r.raise_for_status()
        self.session.headers.update(
            {"Authorization": f"Bearer {r.json()['access_token']}"}
        )

    def _post(self, path: str, payload: dict) -> dict:
        r = self.session.post(self.base + path, json=payload)
        r.raise_for_status()
        return r.json()

    def chart_data(self, groupby: str | None, measure: str,
                   timeseries: bool = False) -> list:
        metric = {"expressionType": "SQL", "sqlExpression": measure,
                  "label": measure}
        granularity = "order_date" if (timeseries or groupby) else None
        query = {
            "metrics": [metric],
            "granularity": granularity,
            "time_range": "No filter",
            "groupby": [groupby] if groupby else [],
            "is_timeseries": timeseries,
            "row_limit": 10000,
            "extras": {},
        }
        if granularity:
            query["time_grain_sqla"] = "P1M"
        body = {"datasource": {"id": 1, "type": "table"},
                "force": True, "result_format": "json",
                "queries": [query]}
        result = self._post("/api/v1/chart/data", body)
        return result["result"][0].get("data") or []


def _month_key(value) -> str:
    import datetime
    if isinstance(value, datetime.datetime):
        return value.strftime("%Y-%m")
    if isinstance(value, (int, float)) and value > 10_000_000_000:
        dt = datetime.datetime.fromtimestamp(
            float(value) / 1000.0, datetime.timezone.utc
        )
        return dt.strftime("%Y-%m")
    s = str(value).strip()
    for token in s.replace("T", " ").replace("Z", " ").split():
        if ":" not in token and "-" in token and len(token) >= 7:
            return token[:7]
    if s.replace(".", "", 1).isdigit() and float(s) > 10_000_000_000:
        dt = datetime.datetime.fromtimestamp(
            float(s) / 1000.0, datetime.timezone.utc
        )
        return dt.strftime("%Y-%m")
    return s[:7]


def ground_truth(groupby: str | None, measure: str) -> list:
    con = duckdb.connect(str(BI_DB), read_only=True)
    try:
        if groupby:
            if groupby == "order_date_month":
                expr = "date_trunc('month', order_date)"
                rows = con.execute(
                    f"SELECT strftime({expr}, '%Y-%m') AS k, {measure} AS m "
                    f"FROM v_order_details GROUP BY {expr} ORDER BY m DESC"
                ).fetchall()
                return [(str(r[0]), float(r[1])) for r in rows]
            sql = (
                f"SELECT {groupby} AS k, {measure} AS m "
                f"FROM v_order_details GROUP BY {groupby} ORDER BY m DESC"
            )
            return [(str(r[0]), float(r[1])) for r in con.execute(sql).fetchall()]
        sql = f"SELECT {measure} AS m FROM v_order_details"
        return [(None, float(con.execute(sql).fetchone()[0]))]
    finally:
        con.close()


def chart_actual(client: SupersetClient, groupby: str | None, measure: str) -> dict:
    rows = client.chart_data(groupby, measure)
    out: dict = {}
    for row in rows:
        value = None
        for v in row.values():
            if isinstance(v, (int, float)):
                value = float(v)
        if groupby:
            label = str(row.get(groupby))
            if label != "None" and value is not None:
                out[label] = value
        elif value is not None:
            out["total"] = value
    return out


def verify_grouped(client, analysis, groupby, measure, limit, tolerance) -> bool:
    truth = ground_truth(groupby, measure)[:limit]
    actual = chart_actual(client, groupby, measure)
    mismatches = 0
    for label, exp in truth:
        act = actual.get(label)
        if act is None or abs(exp - act) > tolerance:
            mismatches += 1
    ok = mismatches == 0
    print(
        f"[ {'PASS' if ok else 'FAIL'} ] {analysis:<32} top-{limit} values match "
        f"(mismatches={mismatches}/{limit})"
    )
    if not ok:
        for label, exp in truth[:3]:
            act = actual.get(label)
            print(f"        {label!r}: expected={exp:,.2f} actual={act}")
    return ok


def verify_monthly(client, analysis, measure, tolerance) -> bool:
    truth = {k: v for k, v in ground_truth("order_date_month", measure)}
    rows = client.chart_data("order_date_month", measure, timeseries=True)
    actual: dict = {}
    for row in rows:
        value = None
        for v in row.values():
            if isinstance(v, (int, float)):
                value = float(v)
        ts = row.get("__timestamp")
        if ts is not None and value is not None:
            key = _month_key(ts)
            actual[key] = actual.get(key, 0.0) + value
    mismatches = 0
    for key, exp in truth.items():
        if actual.get(key) is None or abs(exp - actual.get(key, 0.0)) > tolerance:
            mismatches += 1
    ok = mismatches == 0
    print(
        f"[ {'PASS' if ok else 'FAIL'} ] {analysis:<32} all {len(truth)} months "
        f"match (mismatches={mismatches})"
    )
    if not ok:
        for key, exp in sorted(
            truth.items(), key=lambda kv: kv[1], reverse=True
        )[:3]:
            print(f"        {key!r}: expected={exp:,.2f} "
                  f"actual={actual.get(key)}")
    return ok


def verify_counts(client, analysis, measure, tolerance) -> bool:
    truth = ground_truth(None, measure)
    actual = chart_actual(client, None, measure)
    exp = truth[0][1] if truth else 0.0
    act = actual.get("total", 0.0)
    ok = abs(exp - act) <= tolerance
    print(
        f"[ {'PASS' if ok else 'FAIL'} ] {analysis:<32} expected={exp:,.2f} "
        f"actual={act:,.2f}"
    )
    return ok


def report_special_analyses() -> None:
    print("== Analyses with special semantics (not 1:1 on the dashboard) ==")
    notes = {
        "ca_cumule_par_mois.sql": "cumulative revenue over time (running total)",
        "ca_par_vendeur.sql": "revenue by salesperson (no chart) -> GAP",
        "part_de_marche_categorie.sql": "category market share % (no chart) -> GAP",
        "top_10_produits.sql": "top-10 products (chart shows all products, not top 10)",
    }
    for a in SPECIAL_ANALYSES:
        print(f"  {a:<32} {notes.get(a, '')}")
    print()


def verify_all(limit: int, tolerance: float) -> int:
    if not BI_DB.exists():
        print(f"[ERROR] missing {BI_DB} -- run `make bi-export` first")
        return 2

    client = SupersetClient(BASE_URL)
    exit_code = 0

    print(f"== Comparing 'analyses/*.sql' vs live dashboard chart data "
          f"({BASE_URL}) ==\n")

    checks = [("ca_par_categorie.sql", "category_name", "SUM(revenue)", None),
              ("ca_par_pays.sql", "customer_country", "SUM(revenue)", None),
              ("ca_par_transporteur.sql", "shipper_company_name", "SUM(revenue)",
               None),
              ("ca_par_mois.sql", "order_date_month", "SUM(revenue)", "monthly")]
    for analysis, grp, meas, kind in checks:
        try:
            if kind == "monthly":
                ok = verify_monthly(client, analysis, meas, tolerance)
            else:
                ok = verify_grouped(client, analysis, grp, meas, limit, tolerance)
        except Exception as exc:
            ok = False
            print(f"[ ERROR ] {analysis:<32} {exc}")
        exit_code |= (0 if ok else 1)

    try:
        ok = verify_counts(client, "total-revenue (big_number)", "SUM(revenue)",
                           tolerance)
        exit_code |= (0 if ok else 1)
    except Exception as exc:
        exit_code = 1
        print(f"[ ERROR ] total-revenue (big_number) {exc}")
    try:
        ok = verify_counts(client, "orders-lines (big_number)", "COUNT(*)",
                           tolerance)
        exit_code |= (0 if ok else 1)
    except Exception as exc:
        exit_code = 1
        print(f"[ ERROR ] orders-lines (big_number) {exc}")

    print()
    report_special_analyses()

    present = {p for p in os.listdir(ANALYSES_DIR) if p.endswith(".sql")}
    for a in list(ANALYSIS_SPEC) + SPECIAL_ANALYSES:
        if a not in present:
            print(f"[ WARN ] analyses file missing: {a}")

    print(f"=> EXIT {exit_code}")
    return exit_code


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Verify that the Superset dashboard reflects the ad-hoc SQL analyses."
    )
    p.add_argument("--limit", type=int, default=5,
                   help="top-N values to compare (default 5)")
    p.add_argument("--tolerance", type=float, default=1.0,
                   help="allowed absolute difference in values (default 1.0)")
    p.add_argument("--base", default=BASE_URL, help="Superset base URL")
    return p.parse_args()


def main() -> None:
    global BASE_URL
    args = parse_args()
    BASE_URL = args.base
    sys.exit(verify_all(limit=args.limit, tolerance=args.tolerance))


if __name__ == "__main__":
    main()
