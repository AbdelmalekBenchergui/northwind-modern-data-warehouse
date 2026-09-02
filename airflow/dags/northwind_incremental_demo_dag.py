from __future__ import annotations

import pendulum

from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator

from common import PROJECT_DIR, SCRIPTS_DIR, dbt_environment, warm_superset_dashboard

DAG_ID = "northwind_incremental_demo"
DEFAULTS = {
    "owner": "dataeng",
    "retries": 1,
    "retry_delay": pendulum.duration(minutes=2),
}

with DAG(
    dag_id=DAG_ID,
    default_args=DEFAULTS,
    description=(
        "Incremental demo: append new orders -> dbt seed -> "
        "incremental rebuild of fct_order_details -> export -> warm Superset."
    ),
    schedule=None,
    start_date=pendulum.datetime(2026, 1, 1, tz="UTC"),
    tags=["northwind", "incremental", "demo"],
) as dag:
    project = str(PROJECT_DIR)
    profiles = str(PROJECT_DIR / "profiles")

    demo_append = BashOperator(
        task_id="demo_append_orders",
        bash_command=f"python {SCRIPTS_DIR}/demo_incremental.py",
        env=dbt_environment(),
    )

    dbt_seed = BashOperator(
        task_id="dbt_seed",
        bash_command=f"cd {project} && dbt seed --profiles-dir {profiles}",
        env=dbt_environment(),
    )

    dbt_snapshot = BashOperator(
        task_id="dbt_snapshot",
        bash_command=f"cd {project} && dbt snapshot --profiles-dir {profiles}",
        env=dbt_environment(),
    )

    dbt_incremental = BashOperator(
        task_id="dbt_build_incremental",
        bash_command=(
            f"cd {project} && dbt build --select fct_order_details+ "
            f"--profiles-dir {profiles}"
        ),
        env=dbt_environment(),
    )

    export_bi = BashOperator(
        task_id="export_bi",
        bash_command=f"python {SCRIPTS_DIR}/export_bi_duckdb.py",
        env=dbt_environment(),
    )

    refresh_superset = PythonOperator(
        task_id="refresh_superset",
        python_callable=warm_superset_dashboard,
        op_kwargs={"dashboard_id": 1},
    )

    demo_append >> dbt_seed >> [dbt_snapshot, dbt_incremental] >> export_bi >> refresh_superset
