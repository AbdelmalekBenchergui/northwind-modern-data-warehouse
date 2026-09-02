from __future__ import annotations

import pendulum

from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator

from common import PROJECT_DIR, SCRIPTS_DIR, dbt_environment, warm_superset_dashboard

DAG_ID = "northwind_full_build"
DEFAULTS = {
    "owner": "dataeng",
    "retries": 1,
    "retry_delay": pendulum.duration(minutes=2),
}

with DAG(
    dag_id=DAG_ID,
    default_args=DEFAULTS,
    description="Full ELT -> BI: seed, dbt build, export, Superset warm-up.",
    schedule="@daily",
    catchup=False,
    start_date=pendulum.datetime(2026, 1, 1, tz="UTC"),
    tags=["northwind", "elt", "bi"],
) as dag:
    project = str(PROJECT_DIR)
    profiles = str(PROJECT_DIR / "profiles")

    dbt_deps = BashOperator(
        task_id="dbt_deps",
        bash_command=f"cd {project} && dbt deps --profiles-dir {profiles}",
        env=dbt_environment(),
    )

    dbt_seed = BashOperator(
        task_id="dbt_seed",
        bash_command=f"cd {project} && dbt seed --profiles-dir {profiles}",
        env=dbt_environment(),
    )

    dbt_build = BashOperator(
        task_id="dbt_build",
        bash_command=f"cd {project} && dbt build --profiles-dir {profiles}",
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

    dbt_deps >> dbt_seed >> dbt_build >> export_bi >> refresh_superset
