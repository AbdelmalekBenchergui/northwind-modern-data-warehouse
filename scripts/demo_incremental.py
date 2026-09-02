#!/usr/bin/env python3

from __future__ import annotations

import csv
import random
from datetime import date, timedelta
from pathlib import Path

from faker import Faker

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ORDERS = PROJECT_ROOT / "seeds" / "orders.csv"
ORDER_DETAILS = PROJECT_ROOT / "seeds" / "order_details.csv"
PRODUCTS = PROJECT_ROOT / "seeds" / "products.csv"
CUSTOMERS = PROJECT_ROOT / "seeds" / "customers.csv"
EMPLOYEES = PROJECT_ROOT / "seeds" / "employees.csv"
SHIPPERS = PROJECT_ROOT / "seeds" / "shippers.csv"

NUM_ORDERS = 3
LINES_PER_ORDER = (1, 4)
NUM_CUSTOMERS_TO_MODIFY = 2
NUM_PRODUCTS_TO_MODIFY = 3
CALENDAR_MAX = date(1998, 12, 31)

fake = Faker()


def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as fh:
        return list(csv.DictReader(fh))


def _write_rows(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _random_date(after: str) -> str:
    base = date.fromisoformat(after)
    offset = random.randint(1, 14)
    result = base + timedelta(days=offset)
    if result > CALENDAR_MAX:
        result = CALENDAR_MAX
    return result.isoformat()


def _modify_customers(customers: list[dict]) -> int:
    count = min(NUM_CUSTOMERS_TO_MODIFY, len(customers))
    targets = random.sample(customers, count)
    modified = 0
    for row in targets:
        field = random.choice(["contact_name", "contact_title", "phone", "fax"])
        old = row[field]
        if field == "contact_name":
            row[field] = fake.name()
        elif field == "contact_title":
            row[field] = random.choice([
                "Owner", "Sales Representative", "Marketing Manager",
                "Purchasing Manager", "Order Administrator", "Sales Agent",
            ])
        elif field == "phone":
            row[field] = fake.phone_number()[:20]
        elif field == "fax":
            row[field] = fake.phone_number()[:20] if old else ""
        if row[field] != old:
            modified += 1
            print(f"  customer {row['customer_id']}: {field} '{old}' -> '{row[field]}'")
    return modified


def _modify_products(products: list[dict]) -> int:
    count = min(NUM_PRODUCTS_TO_MODIFY, len(products))
    targets = random.sample(products, count)
    modified = 0
    for row in targets:
        field = random.choice(["unit_price", "units_in_stock", "reorder_level"])
        old = row[field]
        if field == "unit_price":
            row[field] = str(round(float(old) * random.uniform(0.7, 1.3), 2))
        elif field == "units_in_stock":
            row[field] = str(random.randint(0, 125))
        elif field == "reorder_level":
            row[field] = str(random.randint(0, 30))
        if row[field] != old:
            modified += 1
            print(f"  product {row['product_id']}: {field} '{old}' -> '{row[field]}'")
    return modified


def main() -> None:
    orders = _read_rows(ORDERS)
    details = _read_rows(ORDER_DETAILS)
    products = _read_rows(PRODUCTS)
    customers = _read_rows(CUSTOMERS)
    employees = _read_rows(EMPLOYEES)
    shippers = _read_rows(SHIPPERS)

    if not orders:
        raise SystemExit("seeds/orders.csv is empty")

    fieldnames_orders = list(orders[0].keys())
    fieldnames_details = list(details[0].keys())
    fieldnames_products = list(products[0].keys())
    fieldnames_customers = list(customers[0].keys())
    max_order_id = max(int(row["order_id"]) for row in orders)
    existing_ids = {row["order_id"] for row in orders}
    last_date = max(row["order_date"] for row in orders)

    product_prices = {row["product_id"]: float(row["unit_price"]) for row in products}
    product_ids = list(product_prices.keys())

    appended_orders = 0
    appended_lines = 0

    for i in range(1, NUM_ORDERS + 1):
        new_id = str(max_order_id + i)
        if new_id in existing_ids:
            print(f"order {new_id} already present - skipping")
            continue

        order_date = _random_date(last_date)
        order_dt = date.fromisoformat(order_date)
        required_dt = min(order_dt + timedelta(days=random.randint(7, 21)), CALENDAR_MAX)
        required_date = required_dt.isoformat()
        ship_offset = random.randint(1, max(1, (required_dt - order_dt).days))
        shipped_dt = min(order_dt + timedelta(days=ship_offset), CALENDAR_MAX)
        shipped_date = shipped_dt.isoformat() if random.random() > 0.15 else ""

        shipper = random.choice(shippers)
        customer = random.choice(customers)
        employee = random.choice(employees)

        new_order = {
            "order_id": new_id,
            "customer_id": customer["customer_id"],
            "employee_id": employee["employee_id"],
            "order_date": order_date,
            "required_date": required_date,
            "shipped_date": shipped_date,
            "ship_via": shipper["shipper_id"],
            "freight": str(round(random.uniform(2.0, 200.0), 2)),
            "ship_name": customer["company_name"],
            "ship_address": customer["address"],
            "ship_city": customer["city"],
            "ship_region": customer.get("region", ""),
            "ship_postal_code": customer["postal_code"],
            "ship_country": customer["country"],
        }
        orders.append(new_order)

        num_lines = random.randint(*LINES_PER_ORDER)
        chosen_products = random.sample(product_ids, min(num_lines, len(product_ids)))

        for pid in chosen_products:
            base_price = product_prices[pid]
            unit_price = round(base_price * random.uniform(0.8, 1.2), 2)
            quantity = random.randint(1, 100)
            discount = random.choice(["0", "0.05", "0.1", "0.15", "0.2", "0.25"])

            details.append({
                "order_id": new_id,
                "product_id": str(pid),
                "unit_price": str(unit_price),
                "quantity": str(quantity),
                "discount": discount,
            })
            appended_lines += 1

        appended_orders += 1
        existing_ids.add(new_id)

    print(f"\n--- modifying dimensions for SCD ---")
    customers_changed = _modify_customers(customers)
    products_changed = _modify_products(products)

    _write_rows(ORDERS, fieldnames_orders, orders)
    _write_rows(ORDER_DETAILS, fieldnames_details, details)
    if customers_changed:
        _write_rows(CUSTOMERS, fieldnames_customers, customers)
    if products_changed:
        _write_rows(PRODUCTS, fieldnames_products, products)

    print(f"\nappended orders    : {appended_orders}")
    print(f"appended lines     : {appended_lines}")
    print(f"customers changed  : {customers_changed}")
    print(f"products changed   : {products_changed}")
    print(f"next step          : dbt seed")
    print(f"then               : dbt build")


if __name__ == "__main__":
    main()
