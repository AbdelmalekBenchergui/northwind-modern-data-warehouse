# Northwind Data Warehouse

End-to-end data warehouse built on the classic Northwind retail dataset using **dbt Core** on **DuckDB**, with **Apache Superset** for BI and **Apache Airflow** for orchestration.

## Stack

| Layer | Tool |
|-------|------|
| ELT | dbt Core 1.12 + dbt-duckdb 1.10 |
| Warehouse | DuckDB (file-based) |
| BI | Apache Superset 4.1 |
| Orchestration | Apache Airflow 2.10.3 (Celery) |
| Linting | SQLFluff (DuckDB dialect) |

## Architecture

```
raw (seeds) → staging (views) → marts (tables) → BI copy → Superset
                                      ↓
                                   snapshots (Type-2 SCD)
```

**Pipeline layers:**

- **raw** — 9 CSV seeds loaded via `dbt seed`
- **staging** — thin 1:1 views that rename and cast columns
- **marts** — star schema with 5 dimensions + 1 incremental fact + 1 OBT
- **snapshots** — Type-2 SCD for customers and products
- **consumption** — ad-hoc analyses + Superset dashboard

## Data Model

### Dimensions
| Table | Description |
|-------|-------------|
| `dim_customer` | Customer master with surrogate key |
| `dim_product` | Product with denormalized category + supplier |
| `dim_employee` | Employee with manager hierarchy |
| `dim_shipper` | Shipping companies |
| `dim_date` | Calendar dimension (year, quarter, month, weekday) |

### Fact
| Table | Description |
|-------|-------------|
| `fct_order_details` | Order line items (incremental, delete+insert) |

### One-Big-Table
| Table | Description |
|-------|-------------|
| `obt_order_details` | Denormalized fact + all dimensions for BI |

### Snapshots
| Table | Description |
|-------|-------------|
| `snap_customers` | Type-2 SCD on customer profile changes |
| `snap_products` | Type-2 SCD on product attribute changes |

## Project Layout

```
models/          sources.yml · docs.md · exposures.yml · staging/ · marts/
seeds/           raw CSVs + seed_schema.yml
snapshots/       Type-2 SCD models
analyses/        ad-hoc revenue queries
macros/          generate_schema_name override
scripts/         export_bi_duckdb.py · provision_bi.py · verify_analyses_against_dashboard.py · demo_incremental.py
docker/          Superset Dockerfile + init.sh
airflow/         Dockerfile · requirements · profiles/ · scripts/ · dags/
compose.yaml     Airflow + Superset stack
```

## Quick Start

### Local (dbt only)

```bash
make setup       # create venv + install dependencies
make deps        # install dbt packages
make seed        # load raw CSVs
make build       # full pipeline: seed → snapshot → models → tests → analyses
make lint        # lint SQL with sqlfluff
make docs        # generate dbt docs
make serve       # serve docs at localhost:8080
```

Warehouse output: `target/northwind.duckdb`

### BI (Superset)

```bash
make bi-export   # export read-only BI copy → data/northwind_bi.duckdb
make bi-up       # start Superset + provision dashboard
make bi-down     # stop Superset
```

Dashboard: http://localhost:8088/superset/dashboard/1/ (login: `admin` / `admin`)

### Orchestration (Airflow + Superset)

```bash
make air-up      # start full stack
make air-down    # stop everything
```

| Service | URL |
|---------|-----|
| Airflow UI | http://localhost:8080 |
| Superset | http://localhost:8088 |

### DAGs

| DAG | Schedule | Description |
|-----|----------|-------------|
| `northwind_full_build` | Daily | Full rebuild: seed → build → export → warm Superset |
| `northwind_incremental_demo` | Manual | Demo incremental loading with new orders |

### Verification


```bash
make verify-bi   # compare analyses/*.sql against live dashboard
```

## Facts

- 2,164 order lines · 834 orders
- Total revenue ≈ €1,268,259.29
- 77 data tests, all passing
