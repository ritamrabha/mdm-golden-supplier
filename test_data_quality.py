"""
Stage 6: Automated Data Quality Tests
Run with: pytest test_data_quality.py -v

Each test asserts an invariant that MUST hold if Stages 0-5 ran
correctly. Every one of these maps directly back to a question from
the "what SHOULD be impossible in a correct golden_supplier table?"
exercise — that question list IS this test suite.
"""

import pytest
import snowflake.connector
from config import SNOWFLAKE_CONFIG


@pytest.fixture(scope="session")
def conn():
    connection = snowflake.connector.connect(**SNOWFLAKE_CONFIG)
    yield connection
    connection.close()


@pytest.fixture(scope="session")
def cur(conn):
    cursor = conn.cursor()
    yield cursor
    cursor.close()


def scalar(cur, query):
    cur.execute(query)
    return cur.fetchone()[0]


# ------------------------------------------------------------
# Identity: no supplier should ever appear twice
# ------------------------------------------------------------

def test_no_duplicate_golden_ids(cur):
    total = scalar(cur, "SELECT COUNT(*) FROM CURATED.golden_supplier")
    distinct = scalar(cur, "SELECT COUNT(DISTINCT golden_id) FROM CURATED.golden_supplier")
    assert total == distinct, f"{total - distinct} duplicate golden_id(s) found"


# ------------------------------------------------------------
# Completeness: every source row lands in exactly one outcome
# (merged, pending steward review, or standalone) — never zero,
# never two.
# ------------------------------------------------------------

def test_every_erp_row_accounted_for_exactly_once(cur):
    total_erp = scalar(cur, "SELECT COUNT(*) FROM RAW.erp_vendor_master")
    merged = scalar(cur, "SELECT COUNT(*) FROM STAGING.mutual_best_pairs WHERE match_status = 'AUTO_MERGE'")
    pending = scalar(cur, "SELECT COUNT(*) FROM STAGING.mutual_best_pairs WHERE match_status = 'STEWARD_REVIEW'")
    standalone = scalar(cur, "SELECT COUNT(*) FROM CURATED.golden_supplier WHERE source_composition = 'ERP_ONLY'")
    assert merged + pending + standalone == total_erp, (
        f"ERP rows don't reconcile: {merged}+{pending}+{standalone} != {total_erp}"
    )


def test_every_proc_row_accounted_for_exactly_once(cur):
    total_proc = scalar(cur, "SELECT COUNT(*) FROM RAW.proc_supplier_export")
    merged = scalar(cur, "SELECT COUNT(*) FROM STAGING.mutual_best_pairs WHERE match_status = 'AUTO_MERGE'")
    pending = scalar(cur, "SELECT COUNT(*) FROM STAGING.mutual_best_pairs WHERE match_status = 'STEWARD_REVIEW'")
    standalone = scalar(cur, "SELECT COUNT(*) FROM CURATED.golden_supplier WHERE source_composition = 'PROCUREMENT_ONLY'")
    assert merged + pending + standalone == total_proc, (
        f"Procurement rows don't reconcile: {merged}+{pending}+{standalone} != {total_proc}"
    )


# ------------------------------------------------------------
# Required fields
# ------------------------------------------------------------

def test_no_null_supplier_name(cur):
    nulls = scalar(cur, "SELECT COUNT(*) FROM CURATED.golden_supplier WHERE supplier_name IS NULL")
    assert nulls == 0, f"{nulls} golden record(s) with no supplier_name"


def test_no_null_golden_id(cur):
    nulls = scalar(cur, "SELECT COUNT(*) FROM CURATED.golden_supplier WHERE golden_id IS NULL")
    assert nulls == 0, f"{nulls} golden record(s) with no golden_id"


# ------------------------------------------------------------
# Lineage integrity — every merged record must have exactly 5
# lineage rows (name, tax_id, city, phone, email), no more, no less
# ------------------------------------------------------------

def test_lineage_row_count_matches_merged_count(cur):
    merged = scalar(cur, "SELECT COUNT(*) FROM CURATED.golden_supplier WHERE source_composition = 'MERGED'")
    lineage = scalar(cur, "SELECT COUNT(*) FROM CURATED.record_lineage")
    expected = merged * 5
    assert lineage == expected, f"Expected {expected} lineage rows (5 per merge), got {lineage}"


def test_every_merged_record_has_full_lineage(cur):
    cur.execute("""
        SELECT g.golden_id, COUNT(l.attribute) AS attr_count
        FROM CURATED.golden_supplier g
        LEFT JOIN CURATED.record_lineage l ON g.golden_id = l.golden_id
        WHERE g.source_composition = 'MERGED'
        GROUP BY g.golden_id
        HAVING COUNT(l.attribute) != 5
    """)
    incomplete = cur.fetchall()
    assert incomplete == [], f"{len(incomplete)} merged record(s) missing lineage rows: {incomplete[:5]}"


# ------------------------------------------------------------
# Matching correctness against ground truth
# ------------------------------------------------------------

def test_no_hard_negatives_auto_merged(cur):
    cur.execute("""
        SELECT COUNT(*)
        FROM STAGING.mutual_best_pairs mb
        JOIN RAW.match_truth gt
          ON mb.erp_id = gt.erp_id AND mb.proc_id = gt.proc_id
        WHERE mb.match_status = 'AUTO_MERGE' AND gt.match_type = 'hard_negative'
    """)
    leaked = cur.fetchone()[0]
    assert leaked == 0, f"{leaked} hard-negative pair(s) were incorrectly auto-merged"


def test_steward_queue_pairs_not_in_golden_supplier(cur):
    cur.execute("""
        SELECT COUNT(*)
        FROM CURATED.steward_queue sq
        JOIN CURATED.golden_supplier g
          ON g.source_composition = 'MERGED'
         AND g.golden_id = sq.erp_id || '_' || sq.proc_id
    """)
    leaked = cur.fetchone()[0]
    assert leaked == 0, f"{leaked} steward-queue pair(s) were auto-merged despite being pending review"


if __name__ == "__main__":
    import sys
    sys.exit(pytest.main([__file__, "-v"]))
