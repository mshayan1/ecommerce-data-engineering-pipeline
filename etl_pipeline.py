
import os
import io
import logging
import pandas as pd
import psycopg
from psycopg import sql

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)
logger = logging.getLogger(__name__)

DATABASE_URL = os.environ["NEON_DATABASE_URL"]

# Public mirror of the Olist dataset
BASE_URL = (
    "https://raw.githubusercontent.com/"
    "olist/work-at-olist-data/master/datasets/"
)

FILES = {
    "customers": "olist_customers_dataset.csv",
    "products": "olist_products_dataset.csv",
    "orders": "olist_orders_dataset.csv",
}

# Columns and SQL types for the target tables
SCHEMAS = {
    "customers": {
        "customer_id": "TEXT PRIMARY KEY",
        "customer_unique_id": "TEXT",
        "customer_zip_code_prefix": "INTEGER",
        "customer_city": "TEXT",
        "customer_state": "TEXT",
    },
    "products": {
        "product_id": "TEXT PRIMARY KEY",
        "product_category_name": "TEXT",
        "product_name_lenght": "DOUBLE PRECISION",
        "product_description_lenght": "DOUBLE PRECISION",
        "product_photos_qty": "DOUBLE PRECISION",
        "product_weight_g": "DOUBLE PRECISION",
        "product_length_cm": "DOUBLE PRECISION",
        "product_height_cm": "DOUBLE PRECISION",
        "product_width_cm": "DOUBLE PRECISION",
    },
    "orders": {
        "order_id": "TEXT PRIMARY KEY",
        "customer_id": "TEXT NOT NULL",
        "order_status": "TEXT",
        "order_purchase_timestamp": "TIMESTAMP",
        "order_approved_at": "TIMESTAMP",
        "order_delivered_carrier_date": "TIMESTAMP",
        "order_delivered_customer_date": "TIMESTAMP",
        "order_estimated_delivery_date": "TIMESTAMP",
    },
}

def extract(filename):
    url = BASE_URL + filename
    logger.info("Extracting %s", filename)
    df = pd.read_csv(url)

    if df.empty:
        raise ValueError(f"{filename} contains no rows")

    return df

def transform(table, df):
    if table == "orders":
        date_cols = [
            "order_purchase_timestamp",
            "order_approved_at",
            "order_delivered_carrier_date",
            "order_delivered_customer_date",
            "order_estimated_delivery_date",
        ]
        for col in date_cols:
            df[col] = pd.to_datetime(df[col], errors="coerce")

    if table == "customers":
        df["customer_city"] = df["customer_city"].str.strip().str.lower()
        df["customer_state"] = df["customer_state"].str.strip().str.upper()

    if table == "products":
        df["product_category_name"] = (
            df["product_category_name"].fillna("unknown").str.strip()
        )

    primary_key = {
        "orders": "order_id",
        "customers": "customer_id",
        "products": "product_id",
    }[table]

    if df[primary_key].isna().any():
        raise ValueError(f"{table}: null primary keys found")

    if df[primary_key].duplicated().any():
        raise ValueError(f"{table}: duplicate primary keys found")

    return df

def load(table, df):
    schema = SCHEMAS[table]
    columns = list(schema.keys())

    # Reject unexpected/missing columns before writing
    if set(df.columns) != set(columns):
        raise ValueError(f"Unexpected columns in {table}")

    create_columns = sql.SQL(", ").join(
        sql.SQL("{} {}").format(sql.Identifier(col), sql.SQL(dtype))
        for col, dtype in schema.items()
    )

    insert_query = sql.SQL(
        "INSERT INTO {} ({}) VALUES ({}) ON CONFLICT DO NOTHING"
    ).format(
        sql.Identifier(table),
        sql.SQL(", ").join(map(sql.Identifier, columns)),
        sql.SQL(", ").join(sql.Placeholder() for _ in columns),
    )

    records = [
        tuple(None if pd.isna(value) else value for value in row)
        for row in df[columns].itertuples(index=False, name=None)
    ]

    with psycopg.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            cur.execute(
                sql.SQL("CREATE TABLE IF NOT EXISTS {} ({})").format(
                    sql.Identifier(table), create_columns
                )
            )
            cur.executemany(insert_query, records)
            cur.execute(
                sql.SQL("SELECT COUNT(*) FROM {}").format(
                    sql.Identifier(table)
                )
            )
            total = cur.fetchone()[0]

    logger.info("%s: processed %s rows; database total %s",
                table, len(records), total)

def main():
    for table, filename in FILES.items():
        df = extract(filename)
        df = transform(table, df)
        load(table, df)

    logger.info("ETL pipeline completed successfully")

if __name__ == "__main__":
    main()
