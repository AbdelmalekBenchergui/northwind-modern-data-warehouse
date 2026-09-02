FROM apache/airflow:2.10.3

USER airflow

COPY requirements-airflow.txt /requirements-airflow.txt
RUN pip install --no-cache-dir --timeout 120 -r /requirements-airflow.txt