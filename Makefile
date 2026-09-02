.PHONY: help setup deps seed build test lint docs serve freshness ci clean bi-export bi-up bi-down verify-bi air-up air-down

DBT := ./venv/bin/dbt
SQLFLUFF := ./venv/bin/sqlfluff
PYTHON := ./venv/bin/python

help: ## Show available targets
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'

setup: ## Create the virtualenv and install dependencies
	python3 -m venv venv
	./venv/bin/pip install --upgrade pip
	./venv/bin/pip install -r requirements.txt

deps: ## Install dbt packages (dbt_utils, ...)
	$(DBT) deps

seed: ## Load the raw seed data into the `raw` schema
	$(DBT) seed

build: ## Run the full dbt build (seeds, snapshots, models, tests, analyses)
	$(DBT) build

test: ## Run data tests (and units tests once introduced)
	$(DBT) test

lint: ## Lint SQL files with sqlfluff (dbt templater)
	$(SQLFLUFF) lint models analyses

docs: ## Generate the dbt docs site (target/index.html)
	$(DBT) docs generate

serve: ## Serve the dbt docs site locally
	$(DBT) docs serve

freshness: ## Check source freshness
	$(DBT) source freshness

ci: deps seed build lint docs ## CI-like run: deps, seed, full build, lint, docs

bi-export: ## Build the read-only BI copy of the marts (data/northwind_bi.duckdb)
	$(PYTHON) scripts/export_bi_duckdb.py

bi-up: ## Start Apache Superset and auto-provision the BI layer (DB, datasets, charts, dashboard)
	docker compose up -d
	@echo "Waiting for Superset to be ready..."
	@until curl -sf -o /dev/null http://localhost:8088/login/; do sleep 2; done
	$(PYTHON) scripts/provision_bi.py

bi-down: ## Stop Apache Superset
	docker compose down

verify-bi: ## Verify Superset dashboard charts match the analyses/*.sql queries
	$(PYTHON) scripts/verify_analyses_against_dashboard.py

air-up: ## Build + start the Airflow orchestrator stack (Celery) with docker compose
	docker compose build airflow-webserver airflow-scheduler airflow-worker airflow-triggerer
	docker compose run --rm airflow-init
	docker compose up -d
	@echo "Waiting for Airflow to be ready..."
	@until curl -sf -o /dev/null http://localhost:8080/health; do sleep 2; done
	@echo "Airflow UI  : http://localhost:8080  (admin / admin)"
	@echo "DAGs        : northwind_full_build (daily) , northwind_incremental_demo (on-demand)"

air-down: ## Stop the Airflow + Superset orchestrator stack
	docker compose down

clean: ## Remove generated artifacts (target/ and dbt_packages/)
	$(DBT) clean