"""
Load Raw Data into Snowflake
Uploads generated CSVs into RAW schema tables.
Handles NaN -> NULL conversion properly, and falls back to
row-by-row insert with full error text if a bulk insert fails.
"""

import sys
import pandas as pd
import snowflake.connector
from config import SNOWFLAKE_CONFIG

print("=" * 60)
print("LOADING RAW DATA INTO SNOWFLAKE")
print("=" * 60)


def clean(df):
    """Convert pandas NaN/NaT to real Python None so Snowflake gets NULL,
    not the literal text 'nan'."""
    return df.astype(object).where(pd.notnull(df), None)


print("\n[1/4] Connecting to Snowflake...")
try:
    conn = snowflake.connector.connect(**SNOWFLAKE_CONFIG)
    cursor = conn.cursor()
    print("✓ Connected to Snowflake")
except Exception as e:
    print(f"✗ Connection failed: {e}")
    print("\nCheck config.py — account / user / password / warehouse / database / schema")
    sys.exit(1)


def load_table(csv_path, table_name, create_sql, insert_sql, columns):
    print(f"\nLoading {table_name} ...")
    df = clean(pd.read_csv(csv_path))
    cursor.execute(create_sql)

    rows = list(df[columns].itertuples(index=False, name=None))

    try:
        cursor.executemany(insert_sql, rows)
        conn.commit()
        print(f"✓ Loaded {len(rows)}/{len(rows)} rows into {table_name}")
        return
    except Exception as e:
        conn.rollback()
        print(f"  Bulk insert hit an error, retrying row by row to isolate it:")
        print(f"  {e}")

    # Fallback: row by row, so we can show exactly which row and why
    success = 0
    shown = 0
    for i, r in enumerate(rows):
        try:
            cursor.execute(insert_sql, r)
            success += 1
        except Exception as row_err:
            if shown < 3:  # only show the first few, not flood the terminal
                print(f"    Row {i} failed: {r}")
                print(f"    Reason: {row_err}")
                shown += 1
    conn.commit()
    print(f"✓ Loaded {success}/{len(rows)} rows into {table_name} (after row-by-row retry)")


# --- ERP Vendor Master ---
load_table(
    "data/erp_vendor_master.csv",
    "erp_vendor_master",
    """CREATE OR REPLACE TABLE erp_vendor_master (
        vendor_id STRING, vendor_name STRING, tax_id STRING,
        city STRING, phone STRING, last_updated STRING, source_system STRING
    )""",
    "INSERT INTO erp_vendor_master VALUES (%s,%s,%s,%s,%s,%s,%s)",
    ["vendor_id", "vendor_name", "tax_id", "city", "phone", "last_updated", "source_system"]
)

# --- Procurement Supplier Export ---
load_table(
    "data/proc_supplier_export.csv",
    "proc_supplier_export",
    """CREATE OR REPLACE TABLE proc_supplier_export (
        supplier_id STRING, supplier_name STRING, tax_id STRING,
        city STRING, email STRING, last_updated STRING, source_system STRING
    )""",
    "INSERT INTO proc_supplier_export VALUES (%s,%s,%s,%s,%s,%s,%s)",
    ["supplier_id", "supplier_name", "tax_id", "city", "email", "last_updated", "source_system"]
)

# --- Ground Truth (evaluation reference, not part of the pipeline itself) ---
load_table(
    "data/match_truth.csv",
    "match_truth",
    """CREATE OR REPLACE TABLE match_truth (
        pair_id INT, erp_id STRING, proc_id STRING, clean_name STRING, match_type STRING
    )""",
    "INSERT INTO match_truth VALUES (%s,%s,%s,%s,%s)",
    ["pair_id", "erp_id", "proc_id", "clean_name", "match_type"]
)

# --- Verify ---
print("\n" + "=" * 60)
print("VERIFICATION")
print("=" * 60)

for t in ["erp_vendor_master", "proc_supplier_export", "match_truth"]:
    cursor.execute(f"SELECT COUNT(*) FROM {t}")
    print(f"{t:24s} {cursor.fetchone()[0]} rows")

cursor.close()
conn.close()
print("\n✓ Done. Next: Stage 2 (profiling SQL)")
print("=" * 60)
