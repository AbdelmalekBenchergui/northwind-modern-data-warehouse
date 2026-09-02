#!/usr/bin/env python3

from __future__ import annotations

from pathlib import Path

import duckdb

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SOURCE_DB = PROJECT_ROOT / "target" / "northwind.duckdb"
OUT_DIR = PROJECT_ROOT / "data"
DEST_DB = OUT_DIR / "northwind_bi.duckdb"

V_ORDER_DETAILS = """
    select
        fct.order_details_key,
        fct.order_id,
        fct.quantity,
        fct.unit_price,
        fct.discount,
        fct.revenue,
        c.customer_id,
        c.company_name            as customer_company_name,
        c.contact_name,
        c.contact_title,
        c.country                 as customer_country,
        c.city                    as customer_city,
        c.region                  as customer_region,
        c.postal_code             as customer_postal_code,
        c.phone                   as customer_phone,
        c.fax                     as customer_fax,
        p.product_id,
        p.product_name,
        p.category_name,
        p.category_description,
        p.units_in_stock,
        p.units_on_order,
        p.reorder_level,
        p.discontinued,
        p.supplier_company_name,
        p.unit_price              as product_unit_price,
        e.last_name,
        e.first_name,
        e.title,
        e.manager_name,
        s.shipper_id,
        s.company_name            as shipper_company_name,
        s.phone                   as ship_via_phone,
        d.date_day                as order_date,
        d.month                   as order_date_month,
        d.year                    as order_date_year,
        d.is_weekend              as order_date_is_weekend
    from fct_order_details as fct
    left join dim_customer as c on fct.customer_key = c.customer_key
    left join dim_product   as p on fct.product_key   = p.product_key
    left join dim_employee  as e on fct.employee_key  = e.employee_key
    left join dim_shipper   as s on fct.shipper_key   = s.shipper_key
    left join dim_date      as d on fct.order_date_key = d.date_key
"""


def main() -> None:
    if not SOURCE_DB.exists():
        raise SystemExit(f"missing {SOURCE_DB} -- run `dbt build` first")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(DEST_DB))

    con.execute(f"ATTACH '{SOURCE_DB}' AS src (READ_ONLY)")

    con.execute("DROP TABLE IF EXISTS main.obt_order_details")

    for base in ["fct_order_details", "dim_customer", "dim_product", "dim_employee", "dim_shipper", "dim_date"]:
        con.execute(f'CREATE OR REPLACE TABLE main."{base}" AS SELECT * FROM "src"."marts"."{base}"')
        total = con.execute(f'SELECT count(*) FROM main."{base}"').fetchone()[0]
        print(f"exported {base:<22} {total} rows")

    con.execute(f'CREATE OR REPLACE VIEW main.v_order_details AS {V_ORDER_DETAILS}')
    total = con.execute("SELECT count(*) FROM main.v_order_details").fetchone()[0]
    print("exported v_order_details        %d rows" % total)

    con.execute("DETACH src")
    con.close()
    print(f"\nBI copy ready at {DEST_DB}")


if __name__ == "__main__":
    main()