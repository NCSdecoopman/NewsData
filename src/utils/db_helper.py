import os
import psycopg2


def get_pg_conn():
    return psycopg2.connect(
        dbname=os.getenv("PGDATABASE", "newsdata"),
        user=os.getenv("PGUSER", "postgres"),
        password=os.getenv("PGPASSWORD", "admin"),
        host=os.getenv("PGHOST", "localhost"),
        port=os.getenv("PGPORT", "5432"),
    )