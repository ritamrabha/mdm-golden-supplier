-- ============================================================
-- STAGE 5: SURVIVORSHIP + LINEAGE + STEWARD QUEUE
-- Turns matched candidate pairs into one golden record per
-- real-world supplier. Adds mutual-best (stable) matching on
-- top of Stage 4's threshold=90 decision, then applies
-- attribute-level survivorship rules with a lineage trail.
-- ============================================================

USE DATABASE mdm_golden_supplier;

-- ------------------------------------------------------------
-- 1. Mutual-best matching
--    A pair only counts as a genuine match if it's the best
--    candidate for BOTH sides — not just the ERP side, which is
--    all Stage 4's sweep checked (correct for measuring
--    precision/recall, not sufficient for a real 1:1 merge).
--    This guarantees no procurement record gets claimed by two
--    different ERP vendors.
-- ------------------------------------------------------------

CREATE OR REPLACE TABLE STAGING.mutual_best_pairs AS
WITH best_by_erp AS (
    SELECT *,
        ROW_NUMBER() OVER (PARTITION BY erp_id ORDER BY name_similarity DESC) AS erp_rank
    FROM STAGING.candidate_pairs
),
best_by_proc AS (
    SELECT *,
        ROW_NUMBER() OVER (PARTITION BY proc_id ORDER BY name_similarity DESC) AS proc_rank
    FROM STAGING.candidate_pairs
)
SELECT
    e.erp_id, e.proc_id, e.erp_raw_name, e.proc_raw_name,
    e.erp_clean_name, e.proc_clean_name,
    e.name_similarity, e.edit_distance, e.tax_id_match,
    CASE
        WHEN e.name_similarity >= 90 THEN 'AUTO_MERGE'
        WHEN e.name_similarity >= 80 THEN 'STEWARD_REVIEW'
        ELSE 'NO_MATCH'
    END AS match_status
FROM best_by_erp e
JOIN best_by_proc p
  ON e.erp_id = p.erp_id AND e.proc_id = p.proc_id
WHERE e.erp_rank = 1 AND p.proc_rank = 1
  AND e.name_similarity >= 80;  -- below 80 isn't worth carrying forward


-- ------------------------------------------------------------
-- 2. Steward queue — grey-zone pairs (80-89), pending human
--    review. NOT in golden_supplier yet — a human hasn't signed
--    off, so these don't get auto-merged.
-- ------------------------------------------------------------

CREATE OR REPLACE TABLE CURATED.steward_queue AS
SELECT
    erp_id, erp_raw_name, proc_id, proc_raw_name,
    name_similarity, edit_distance, tax_id_match,
    'Similarity in grey zone (80-89): above no-match floor, below auto-merge threshold' AS reason,
    'PENDING_REVIEW' AS review_status
FROM STAGING.mutual_best_pairs
WHERE match_status = 'STEWARD_REVIEW';


-- ------------------------------------------------------------
-- 3. Pull full attribute set for auto-merge pairs
-- ------------------------------------------------------------

CREATE OR REPLACE TABLE STAGING.merged_source AS
SELECT
    m.erp_id, m.proc_id, m.name_similarity,
    e.raw_name   AS erp_name,  e.tax_id AS erp_tax_id, e.city AS erp_city,
    e.contact    AS erp_phone, e.last_updated AS erp_last_updated,
    p.raw_name   AS proc_name, p.tax_id AS proc_tax_id, p.city AS proc_city,
    p.contact    AS proc_email, p.last_updated AS proc_last_updated
FROM STAGING.mutual_best_pairs m
JOIN STAGING.suppliers_standardized e
  ON m.erp_id = e.source_id AND e.source_system = 'ERP'
JOIN STAGING.suppliers_standardized p
  ON m.proc_id = p.source_id AND p.source_system = 'PROCUREMENT'
WHERE m.match_status = 'AUTO_MERGE';


-- ------------------------------------------------------------
-- 4. golden_supplier — one row per real-world supplier
--    Three ways a supplier gets in here:
--      MERGED             - auto-merged pair, survivorship applied
--      ERP_ONLY           - no acceptable match found
--      PROCUREMENT_ONLY   - no acceptable match found
--    Records sitting in steward_queue appear in NEITHER bucket
--    yet — they're pending, not resolved.
-- ------------------------------------------------------------

CREATE OR REPLACE TABLE CURATED.golden_supplier AS

WITH merged AS (
    SELECT
        erp_id || '_' || proc_id                                        AS golden_id,
        'MERGED'                                                        AS source_composition,
        erp_name                                                        AS supplier_name,
        COALESCE(erp_tax_id, proc_tax_id)                               AS tax_id,
        IFF(erp_last_updated >= proc_last_updated, erp_city, proc_city) AS city,
        erp_phone                                                       AS phone,
        proc_email                                                      AS email,
        GREATEST(erp_last_updated, proc_last_updated)                   AS last_updated,
        erp_id, proc_id
    FROM STAGING.merged_source
),

erp_only AS (
    SELECT
        source_id                                                       AS golden_id,
        'ERP_ONLY'                                                      AS source_composition,
        raw_name                                                        AS supplier_name,
        tax_id, city,
        contact                                                         AS phone,
        NULL                                                            AS email,
        last_updated,
        source_id                                                       AS erp_id,
        NULL                                                            AS proc_id
    FROM STAGING.suppliers_standardized
    WHERE source_system = 'ERP'
      AND source_id NOT IN (
          SELECT erp_id FROM STAGING.mutual_best_pairs
          WHERE match_status IN ('AUTO_MERGE', 'STEWARD_REVIEW')
      )
),

proc_only AS (
    SELECT
        source_id                                                       AS golden_id,
        'PROCUREMENT_ONLY'                                              AS source_composition,
        raw_name                                                        AS supplier_name,
        tax_id, city,
        NULL                                                            AS phone,
        contact                                                         AS email,
        last_updated,
        NULL                                                            AS erp_id,
        source_id                                                       AS proc_id
    FROM STAGING.suppliers_standardized
    WHERE source_system = 'PROCUREMENT'
      AND source_id NOT IN (
          SELECT proc_id FROM STAGING.mutual_best_pairs
          WHERE match_status IN ('AUTO_MERGE', 'STEWARD_REVIEW')
      )
)

SELECT * FROM merged
UNION ALL
SELECT * FROM erp_only
UNION ALL
SELECT * FROM proc_only;


-- ------------------------------------------------------------
-- 5. record_lineage — for merged rows only: which attribute,
--    which source won, and the rule that decided it.
-- ------------------------------------------------------------

CREATE OR REPLACE TABLE CURATED.record_lineage AS

SELECT erp_id || '_' || proc_id AS golden_id, 'supplier_name' AS attribute,
       'ERP' AS winning_source,
       'erp_is_system_of_record_for_legal_name' AS rule
FROM STAGING.merged_source

UNION ALL

SELECT erp_id || '_' || proc_id, 'tax_id',
       IFF(erp_tax_id IS NOT NULL, 'ERP', 'PROCUREMENT'),
       IFF(erp_tax_id IS NOT NULL, 'erp_preferred_lower_null_rate', 'fallback_proc_had_value_erp_did_not')
FROM STAGING.merged_source

UNION ALL

SELECT erp_id || '_' || proc_id, 'city',
       IFF(erp_last_updated >= proc_last_updated, 'ERP', 'PROCUREMENT'),
       'most_recently_updated_source_wins'
FROM STAGING.merged_source

UNION ALL

SELECT erp_id || '_' || proc_id, 'phone', 'ERP', 'field_only_collected_by_erp'
FROM STAGING.merged_source

UNION ALL

SELECT erp_id || '_' || proc_id, 'email', 'PROCUREMENT', 'field_only_collected_by_procurement'
FROM STAGING.merged_source;


-- ============================================================
-- 6. Verify
-- ============================================================

-- Headline counts
SELECT 'auto_merged_pairs' AS metric, COUNT(*)::STRING AS value
FROM STAGING.mutual_best_pairs WHERE match_status = 'AUTO_MERGE'
UNION ALL
SELECT 'steward_review_pairs', COUNT(*)::STRING
FROM STAGING.mutual_best_pairs WHERE match_status = 'STEWARD_REVIEW'
UNION ALL
SELECT 'golden_supplier_rows', COUNT(*)::STRING FROM CURATED.golden_supplier
UNION ALL
SELECT 'golden_supplier_distinct_ids', COUNT(DISTINCT golden_id)::STRING FROM CURATED.golden_supplier
UNION ALL
SELECT 'lineage_rows', COUNT(*)::STRING FROM CURATED.record_lineage
UNION ALL
SELECT 'steward_queue_rows', COUNT(*)::STRING FROM CURATED.steward_queue;

-- Reconciliation: every ERP row accounted for in exactly one outcome
SELECT
    (SELECT COUNT(*) FROM RAW.erp_vendor_master) AS total_erp,
    (SELECT COUNT(*) FROM STAGING.mutual_best_pairs WHERE match_status = 'AUTO_MERGE') AS erp_merged,
    (SELECT COUNT(*) FROM STAGING.mutual_best_pairs WHERE match_status = 'STEWARD_REVIEW') AS erp_pending_review,
    (SELECT COUNT(*) FROM CURATED.golden_supplier WHERE source_composition = 'ERP_ONLY') AS erp_standalone;

-- Reconciliation: every Procurement row accounted for in exactly one outcome
SELECT
    (SELECT COUNT(*) FROM RAW.proc_supplier_export) AS total_proc,
    (SELECT COUNT(*) FROM STAGING.mutual_best_pairs WHERE match_status = 'AUTO_MERGE') AS proc_merged,
    (SELECT COUNT(*) FROM STAGING.mutual_best_pairs WHERE match_status = 'STEWARD_REVIEW') AS proc_pending_review,
    (SELECT COUNT(*) FROM CURATED.golden_supplier WHERE source_composition = 'PROCUREMENT_ONLY') AS proc_standalone;

-- Spot-check a few merged golden records with their lineage
SELECT g.golden_id, g.supplier_name, g.tax_id, g.city, g.phone, g.email, g.last_updated
FROM CURATED.golden_supplier g
WHERE g.source_composition = 'MERGED'
LIMIT 10;

SELECT * FROM CURATED.record_lineage
WHERE golden_id IN (SELECT golden_id FROM CURATED.golden_supplier WHERE source_composition = 'MERGED' LIMIT 2)
ORDER BY golden_id, attribute;

-- Steward queue — what a human reviewer would actually see
SELECT * FROM CURATED.steward_queue ORDER BY name_similarity DESC;
