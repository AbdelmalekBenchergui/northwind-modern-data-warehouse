FROM apache/superset:4.1.1

RUN pip install --no-cache-dir duckdb-engine duckdb

COPY --chmod=0755 init.sh /usr/local/bin/superset-init

ENTRYPOINT ["/usr/local/bin/superset-init"]