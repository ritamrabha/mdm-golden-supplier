-- ============================================================
-- STAGE 3: STANDARDIZATION
-- Unions both sources into one shape and builds a clean_name
-- column suitable for fuzzy matching. raw_name is preserved
-- untouched alongside it — never overwrite the source value.
-- ============================================================

USE DATABASE mdm_golden_supplier;

CREATE OR REPLACE TABLE STAGING.suppliers_standardized AS

WITH erp_src AS (
    SELECT
        'ERP'         AS source_system,
        vendor_id     AS source_id,
        vendor_name   AS raw_name,
        tax_id,
        city,
        phone         AS contact,
        last_updated
    FROM RAW.erp_vendor_master
),

proc_src AS (
    SELECT
        'PROCUREMENT' AS source_system,
        supplier_id   AS source_id,
        supplier_name AS raw_name,
        tax_id,
        city,
        email         AS contact,
        last_updated
    FROM RAW.proc_supplier_export
),

unioned AS (
    SELECT * FROM erp_src
    UNION ALL
    SELECT * FROM proc_src
),

-- Step 1: uppercase, strip periods/commas, expand & to AND
step1 AS (
    SELECT *,
        REPLACE(REPLACE(REPLACE(UPPER(raw_name), '.', ''), ',', ''), '&', ' AND ') AS name_a
    FROM unioned
),

-- Step 2: collapse any irregular/multiple whitespace to single spaces
step2 AS (
    SELECT *,
        REGEXP_REPLACE(TRIM(name_a), '\\s+', ' ') AS name_b
    FROM step1
),

-- Step 3: canonicalize legal-suffix and business-term abbreviations
--         (these are exactly the variants the corruption step introduces)
step3 AS (
    SELECT *,
        REGEXP_REPLACE(name_b, '\\bINCORPORATED\\b', 'INC')          AS name_c
    FROM step2
),
step4 AS (
    SELECT *,
        REGEXP_REPLACE(name_c, '\\bCORPORATION\\b', 'CORP')          AS name_d
    FROM step3
),
step5 AS (
    SELECT *,
        REGEXP_REPLACE(name_d, '\\bLIMITED\\b', 'LTD')               AS name_e
    FROM step4
),
step6 AS (
    SELECT *,
        REGEXP_REPLACE(name_e, '\\bCOMPANY\\b', 'CO')                AS name_f
    FROM step5
),
step7 AS (
    SELECT *,
        REGEXP_REPLACE(name_f, '\\b(SVCS|SVC)\\b', 'SERVICES')       AS name_g
    FROM step6
),
step8 AS (
    SELECT *,
        REGEXP_REPLACE(name_g, '\\b(SOLN|SOL)\\b', 'SOLUTIONS')      AS name_h
    FROM step7
),
step9 AS (
    SELECT *,
        REGEXP_REPLACE(name_h, '\\b(PTRS|PTR)\\b', 'PARTNERS')       AS name_i
    FROM step8
),
step10 AS (
    SELECT *,
        REGEXP_REPLACE(name_i, '\\b(HLDGS|HLDG)\\b', 'HOLDINGS')     AS name_j
    FROM step9
),
step11 AS (
    SELECT *,
        REGEXP_REPLACE(name_j, '\\bGRP\\b', 'GROUP')                 AS clean_name
    FROM step10
)

SELECT
    source_system,
    source_id,
    raw_name,
    clean_name,
    tax_id,
    city,
    contact,
    last_updated
FROM step11;

-- ============================================================
-- Verify the transformation
-- ============================================================

-- Row counts should match RAW exactly (405 + 320 = 725) — standardization
-- never drops or adds rows, only cleans values
SELECT source_system, COUNT(*) AS row_count, COUNT(DISTINCT clean_name) AS distinct_clean_names
FROM STAGING.suppliers_standardized
GROUP BY source_system;

-- Spot-check: rows where standardization actually changed something,
-- proving the transformation is doing real work
SELECT source_system, raw_name, clean_name
FROM STAGING.suppliers_standardized
WHERE raw_name != clean_name
LIMIT 20;

-- Bonus: the 2 duplicate ERP names profiling caught — see who they are
SELECT vendor_name, COUNT(*) AS occurrences
FROM RAW.erp_vendor_master
GROUP BY vendor_name
HAVING COUNT(*) > 1;
