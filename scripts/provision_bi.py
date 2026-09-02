#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import sys
from urllib.parse import urljoin

import requests

BASE_URL = "http://localhost:8088"
USERNAME = "admin"
PASSWORD = "admin"

DUCKDB_URI = "duckdb:////data/northwind_bi.duckdb"

DATASETS = [
    "v_order_details",
    "fct_order_details",
    "dim_customer",
    "dim_product",
    "dim_employee",
    "dim_shipper",
    "dim_date",
]

CHARTS = [
    (
        "Total revenue",
        {
            "viz_type": "big_number_total",
            "granularity_sqla": "order_date",
            "time_range": "No filter",
            "metric": {"expressionType": "SQL", "sqlExpression": "SUM(revenue)",
                       "label": "SUM(revenue)"},
            "subheader": "v_order_details",
        },
    ),
    (
        "Orders (lines)",
        {
            "viz_type": "big_number_total",
            "granularity_sqla": "order_date",
            "time_range": "No filter",
            "metric": {"expressionType": "SQL",
                       "sqlExpression": "COUNT(*)",
                       "label": "COUNT(*)"},
            "subheader": "v_order_details",
        },
    ),
    (
        "Revenue over time (month)",
        {
            "viz_type": "echarts_timeseries_line",
            "granularity_sqla": "order_date",
            "time_grain_sqla": "P1M",
            "time_range": "No filter",
            "groupby": [],
            "metrics": [{"expressionType": "SQL", "sqlExpression": "SUM(revenue)",
                         "label": "SUM(revenue)"}],
        },
    ),
    (
        "Revenue by category",
        {
            "viz_type": "dist_bar",
            "time_range": "No filter",
                        "groupby": ["category_name"],
            "metrics": [{"expressionType": "SQL", "sqlExpression": "SUM(revenue)",
                         "label": "SUM(revenue)"}],
            "order_desc": True,
        },
    ),
    (
        "Revenue by country",
        {
            "viz_type": "dist_bar",
            "time_range": "No filter",
                        "groupby": ["customer_country"],
            "metrics": [{"expressionType": "SQL", "sqlExpression": "SUM(revenue)",
                         "label": "SUM(revenue)"}],
            "order_desc": True,
        },
    ),
    (
        "Top products",
        {
            "viz_type": "dist_bar",
            "time_range": "No filter",
                        "groupby": ["product_name"],
            "metrics": [{"expressionType": "SQL", "sqlExpression": "SUM(revenue)",
                         "label": "SUM(revenue)"}],
            "orientation": "horizontal",
            "order_desc": True,
        },
    ),
    (
        "Revenue by shipper",
        {
            "viz_type": "pie",
            "time_range": "No filter",
            "groupby": ["shipper_company_name"],
            "metric": {"expressionType": "SQL", "sqlExpression": "SUM(revenue)",
                       "label": "SUM(revenue)"},
        },
    ),
]


class SupersetClient:
    def __init__(self, base: str) -> None:
        self.base = base.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        self._login()
        self.session.headers.update({"X-CSRFToken": self.csrf})

    def _login(self) -> None:
        r = self.session.post(
            urljoin(self.base, "/api/v1/security/login"),
            json={"username": USERNAME, "password": PASSWORD,
                  "provider": "db", "refresh": True},
        )
        r.raise_for_status()
        token = r.json()["access_token"]
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        csrf = self.session.get(
            urljoin(self.base, "/api/v1/security/csrf_token/")
        ).json().get("result", "")
        self.csrf = csrf
        if csrf:
            self.session.headers.update({"X-CSRFToken": csrf})

    def api(self, method: str, path: str, **kwargs) -> dict:
        r = self.session.request(method, urljoin(self.base, path), **kwargs)
        try:
            payload = r.json()
        except ValueError:
            payload = {"text": r.text}
        if r.status_code >= 400:
            raise RuntimeError(f"{method} {path} -> {r.status_code}: {json.dumps(payload)[:800]}")
        return payload

    def ensure_database(self) -> int:
        existing = self.api(
            "GET", "/api/v1/database/?q=(columns:!(id,database_name,sqlalchemy_uri))"
        ).get("result") or []
        for db in existing:
            if db.get("database_name") == "Northwind (DuckDB)":
                print(f"database OK (id={db['id']})")
                return db["id"]
            if db.get("sqlalchemy_uri", "").replace(" ", "") == DUCKDB_URI.replace(" ", ""):
                print(f"database OK (id={db['id']})")
                return db["id"]
        try:
            payload = self.api(
                "POST", "/api/v1/database/",
                json={"database_name": "Northwind (DuckDB)",
                      "sqlalchemy_uri": DUCKDB_URI,
                      "expose_in_sqllab": True},
            )
        except RuntimeError as exc:
            if "already exists" not in exc.args[0]:
                raise
            db_id = next(d["id"] for d in existing
                         if d.get("database_name") == "Northwind (DuckDB)")
            print(f"database re-used (id={db_id})")
            return db_id
        db_id = payload["id"]
        print(f"database created (id={db_id})")
        return db_id

    def ensure_datasets(self, db_id: int) -> dict[str, int]:
        ids: dict[str, int] = {}
        existing = self.api("GET", "/api/v1/dataset/").get("result") or []
        by_table = {d["table_name"]: d["id"] for d in existing}
        if "obt_order_details" in by_table:
            self.api("DELETE", f"/api/v1/dataset/{by_table['obt_order_details']}")
            print("removed stale dataset obt_order_details")
            del by_table["obt_order_details"]
        for table in DATASETS:
            if table in by_table:
                ids[table] = by_table[table]
                continue
            payload = self.api(
                "POST", "/api/v1/dataset/",
                json={"database": db_id, "schema": "main", "table_name": table},
            )
            ids[table] = payload["id"]
        for table in DATASETS:
            print(f"dataset OK {table} (id={ids[table]})")
        return ids

    def ensure_charts(self, dataset_ids: dict[str, int], dash_id: int) -> dict[str, int]:
        existing = {c["slice_name"]: c for c in
                    self.api("GET", "/api/v1/chart/").get("result") or []}
        chart_ids: dict[str, int] = {}
        ds_id = dataset_ids["v_order_details"]
        for name, form_data in CHARTS:
            viz_type = form_data["viz_type"]
            form = dict(form_data)
            form["datasource"] = f"{ds_id}__table"
            form["slice_name"] = name
            body = {"slice_name": name, "viz_type": viz_type,
                    "datasource_id": ds_id, "datasource_type": "table",
                    "owners": [1],
                    "dashboards": [dash_id],
                    "params": json.dumps(form)}
            if name in existing:
                cid = existing[name]["id"]
                self.api("PUT", f"/api/v1/chart/{cid}", json=body)
                print(f"chart updated {name} (id={cid})")
                chart_ids[name] = cid
                continue
            payload = self.api("POST", "/api/v1/chart/", json=body)
            chart_ids[name] = payload["id"]
            print(f"chart created {name} (id={chart_ids[name]})")
        return chart_ids

    def ensure_dashboard(self) -> int:
        existing = self.api("GET", "/api/v1/dashboard/").get("result") or []
        dash_id = next(
            (d["id"] for d in existing if d.get("dashboard_title") == "Northwind - Revenue"),
            None,
        )
        if dash_id is None:
            payload = self.api(
                "POST", "/api/v1/dashboard/",
                json={
                    "dashboard_title": "Northwind - Revenue",
                    "slug": "northwind-revenue",
                    "published": True,
                },
            )
            dash_id = payload["id"]
            print(f"dashboard created (id={dash_id})")
        else:
            print(f"dashboard OK (id={dash_id})")

        return dash_id

    def _embed_charts(self, dash_id: int, chart_ids: dict[str, int]) -> None:
        rows = [
            ["Total revenue", "Orders (lines)"],
            ["Revenue over time (month)"],
            ["Revenue by category", "Revenue by country"],
            ["Top products", "Revenue by shipper"],
        ]
        widths = {
            "Total revenue": 6, "Orders (lines)": 6,
            "Revenue over time (month)": 12,
            "Revenue by category": 6, "Revenue by country": 6,
            "Top products": 6, "Revenue by shipper": 6,
        }

        pos: dict = {
            "DASHBOARD_VERSION_KEY": "v2",
            "ROOT_ID": {
                "type": "ROOT", "id": "ROOT_ID",
                "children": ["GRID_ID"], "parents": [],
            },
            "GRID_ID": {
                "type": "GRID", "id": "GRID_ID",
                "children": [], "parents": ["ROOT_ID"],
            },
        }
        grid_children = []
        for i, row in enumerate(rows):
            row_id = f"ROW-{i}"
            pos[row_id] = {
                "type": "ROW", "id": row_id, "children": [],
                "parents": ["ROOT_ID", "GRID_ID"],
                "meta": {"background": "BACKGROUND_TRANSPARENT"},
            }
            grid_children.append(row_id)
            for name in row:
                cid = chart_ids[name]
                c_id = f"CHART-{cid}"
                pos[c_id] = {
                    "type": "CHART", "id": c_id, "children": [],
                    "meta": {"width": widths[name], "height": 50,
                             "chartId": cid, "sliceName": name},
                    "parents": ["ROOT_ID", "GRID_ID", row_id],
                }
                pos[row_id]["children"].append(c_id)
        pos["GRID_ID"]["children"] = grid_children

        other_ids = [cid for n, cid in chart_ids.items()]
        chart_config = {}
        for name, cid in chart_ids.items():
            chart_config[str(cid)] = {
                "id": cid,
                "width": widths[name],
                "height": 50,
                "crossFilters": {
                    "scope": "global",
                    "chartsInScope": [c for c in other_ids if c != cid],
                },
            }
        meta = {
            "timed_refresh_immune_slices": [],
            "expanded_slices": {},
            "refresh_frequency": 0,
            "color_scheme": "",
            "label_colors": {},
            "chart_configuration": chart_config,
            "global_chart_configuration": {
                "scope": {
                    "rootPath": ["ROOT_ID"],
                    "excluded": [],
                },
                "chartsInScope": other_ids,
            },
            "shared_label_colors": {},
            "color_scheme_domain": [],
            "cross_filters_enabled": True,
        }

        self.api(
            "PUT", f"/api/v1/dashboard/{dash_id}",
            json={"position_json": json.dumps(pos),
                  "json_metadata": json.dumps(meta)},
        )
        print(f"dashboard layout embedded ({len(chart_ids)} charts)")


def main() -> None:
    args = parse_args()
    client = SupersetClient(args.base)
    db_id = client.ensure_database()
    ds_ids = client.ensure_datasets(db_id)
    dash_id = client.ensure_dashboard()
    chart_ids = client.ensure_charts(ds_ids, dash_id)
    client._embed_charts(dash_id, chart_ids)

    print(f"\n-> Dashboard: {args.base}/superset/dashboard/{dash_id}/")
    print("-" * 60)
    print(f"  DB connection : {DUCKDB_URI}")
    print(f"  datasets      : {len(DATASETS)}")
    print(f"  charts        : {chart_ids}")
    print(f"  login         : {USERNAME} / {PASSWORD}")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Provision BI in Apache Superset")
    p.add_argument("--base", default=BASE_URL, help=f"Superset base URL (default {BASE_URL})")
    return p.parse_args()


if __name__ == "__main__":
    try:
        main()
    except RuntimeError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        sys.exit(1)