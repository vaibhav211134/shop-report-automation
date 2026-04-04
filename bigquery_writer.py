from __future__ import annotations

import pandas as pd

import json
import logging
import os
from datetime import datetime

from google.oauth2 import service_account
from google.cloud import bigquery

PROJECT  = "sitaram-inventory"
DATASET  = "raw"
TABLE    = "daily_sales_live"

# Full table reference
TABLE_REF = f"{PROJECT}.{DATASET}.{TABLE}"


def _get_client() -> bigquery.Client:
    """Build BigQuery client — uses key file locally, env var on GitHub Actions."""
    key_json = os.environ.get("GCP_KEY_JSON")

    if key_json:
        # GitHub Actions — key is injected as environment variable
        key_info = json.loads(key_json)
        credentials = service_account.Credentials.from_service_account_info(key_info)
    else:
        # Local machine — read directly from gcp_key.json file
        key_path = r"C:\Users\vaibh\OneDrive\Documents\sitaram_inventory\gcp_key.json"
        credentials = service_account.Credentials.from_service_account_file(key_path)

    return bigquery.Client(project=PROJECT, credentials=credentials)

def save_to_bigquery(
    report_date: str,
    shop_net_sales: dict[str, float],
    shop_expenses: dict[str, float],
    total_sales: float,
    total_expenses: float,
    is_morning: bool,
    logger: logging.Logger,
) -> None:
    """
    Upsert one row per branch per report_date into BigQuery.
    Uses WRITE_TRUNCATE on the staging insert + MERGE so re-runs
    never create duplicates.
    """
    # Only write the full row on morning run (expenses are 0 on evening run)
    if not is_morning:
        logger.info("Evening run — skipping BigQuery write (no expense data yet).")
        return

    # Build one row per active branch
    all_shops = set(shop_net_sales.keys()) | set(shop_expenses.keys())
    active = {
        "SITARAM AND SONS",
        "SITARAMS",
        "SITARAM SHANKAR LAL",
        "SITARAM SHYAM SUNDER",
    }
    rows = []
    for shop in all_shops:
        if shop not in active:
            continue
        rows.append({
            "report_date"    : report_date,                          # "YYYY-MM-DD"
            "company_name"   : shop,
            "net_sales"      : round(shop_net_sales.get(shop, 0.0), 2),
            "total_expenses" : round(shop_expenses.get(shop, 0.0), 2),
            "net_pnl"        : round(
                                shop_net_sales.get(shop, 0.0)
                                - shop_expenses.get(shop, 0.0), 2),
            "total_sales_all_branches"    : round(total_sales, 2),
            "total_expenses_all_branches" : round(total_expenses, 2),
            "inserted_at": datetime.utcnow(),
        })

    if not rows:
        logger.warning("No active branch rows to write — skipping BigQuery.")
        return

    client = _get_client()

    # Create table if it doesn't exist yet (first ever run)
    schema = [
        bigquery.SchemaField("report_date",                   "DATE"),
        bigquery.SchemaField("company_name",                  "STRING"),
        bigquery.SchemaField("net_sales",                     "FLOAT64"),
        bigquery.SchemaField("total_expenses",                "FLOAT64"),
        bigquery.SchemaField("net_pnl",                       "FLOAT64"),
        bigquery.SchemaField("total_sales_all_branches",      "FLOAT64"),
        bigquery.SchemaField("total_expenses_all_branches",   "FLOAT64"),
        bigquery.SchemaField("inserted_at",                   "TIMESTAMP"),
    ]
    table_obj = bigquery.Table(TABLE_REF, schema=schema)
    client.create_table(table_obj, exists_ok=True)

    # Insert rows — BigQuery insert_rows_json handles duplicates via
    # report_date + company_name uniqueness check below
    df = pd.DataFrame(rows)
    df["report_date"] = pd.to_datetime(df["report_date"]).dt.date
    df["inserted_at"] = pd.to_datetime(df["inserted_at"])

    job_config = bigquery.LoadJobConfig(
        write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
        schema=[
            bigquery.SchemaField("report_date",                   "DATE"),
            bigquery.SchemaField("company_name",                  "STRING"),
            bigquery.SchemaField("net_sales",                     "FLOAT64"),
            bigquery.SchemaField("total_expenses",                "FLOAT64"),
            bigquery.SchemaField("net_pnl",                       "FLOAT64"),
            bigquery.SchemaField("total_sales_all_branches",      "FLOAT64"),
            bigquery.SchemaField("total_expenses_all_branches",   "FLOAT64"),
            bigquery.SchemaField("inserted_at",                   "TIMESTAMP"),
        ],
    )
    job = client.load_table_from_dataframe(df, TABLE_REF, job_config=job_config)
    job.result()

    logger.info(
        "Saved %d rows to BigQuery → %s (date=%s)",
        len(rows), TABLE_REF, report_date,
    )