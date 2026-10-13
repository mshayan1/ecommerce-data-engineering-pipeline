
import os
import pandas as pd
import psycopg
from psycopg import sql
from google.colab import userdata

DATABASE_URL = userdata.get("NEON_DATABASE_URL")
DATA_PATH = "/content/cleaned_data"

TABLES = {
    "customers": "customers_clean.csv",
    "products": "products_clean.csv",
    "orders": "orders_clean.csv",
}

def load_table(table_name, filename):
    path = os.path.join(DATA_PATH, filename)
    df = pd.read_csv(path)
    df = df.astype(object).where(pd.notna(df), None)

    columns = list(df.columns)

    with psycopg.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            query = sql.SQL("""
                INSERT INTO {} ({})
                VALUES ({})
                ON CONFLICT DO NOTHING
            """).format(
                sql.Identifier(table_name),
                sql.SQL(", ").join(map(sql.Identifier, columns)),
                sql.SQL(", ").join(
                    sql.Placeholder() for _ in columns
                )
            )

            cur.executemany(
                query,
                [tuple(row) for row in
                 df.itertuples(index=False, name=None)]
            )

    print(f"Finished loading {table_name}")

def main():
    for table, filename in TABLES.items():
        load_table(table, filename)

    print("ETL pipeline completed successfully!")

if __name__ == "__main__":
    main()
