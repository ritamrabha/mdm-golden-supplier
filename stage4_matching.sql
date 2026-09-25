
-- STAGE 4: BLOCKING + FUZZY MATCHING + THRESHOLD SWEEP


USE DATABASE mdm_golden_supplier;

-- ------------------------------------------------------------
-- 1. Candidate pairs (blocking + similarity scoring)


CREATE OR REPLACE TABLE STAGING.candidate_pairs AS

WITH erp AS (
    SELECT *,
        LEFT(REGEXP_REPLACE(clean_name, '[^A-Z0-9]', ''), 4) AS block_key
    FROM STAGING.suppliers_standardized
    WHERE source_system = 'ERP'
),

proc AS (
    SELECT *,
        LEFT(REGEXP_REPLACE(clean_name, '[^A-Z0-9]', ''), 4) AS block_key
    FROM STAGING.suppliers_standardized
    WHERE source_system = 'PROCUREMENT'
)

SELECT
    e.source_id                                        AS erp_id,
    p.source_id                                         AS proc_id,
    e.raw_name                                          AS erp_raw_name,
    p.raw_name                                          AS proc_raw_name,
    e.clean_name                                        AS erp_clean_name,
    p.clean_name                                        AS proc_clean_name,
    JAROWINKLER_SIMILARITY(e.clean_name, p.clean_name)  AS name_similarity,
    EDITDISTANCE(e.clean_name, p.clean_name)            AS edit_distance,
    IFF(e.tax_id IS NOT NULL AND e.tax_id = p.tax_id, TRUE, FALSE) AS tax_id_match
FROM erp e
JOIN proc p
  ON e.block_key = p.block_key;


-- Sanity check: how many candidate pairs did blocking generate,versus the full cross join it avoided?
SELECT
    (SELECT COUNT(*) FROM STAGING.candidate_pairs)                                    AS candidate_pairs,
    (SELECT COUNT(*) FROM RAW.erp_vendor_master) * (SELECT COUNT(*) FROM RAW.proc_supplier_export) AS full_cross_join_size;



-- 2. Threshold sweep: score precision / recall / F1 at each


CREATE OR REPLACE TABLE STAGING.match_tuning_report AS

WITH thresholds AS (
    SELECT column1 AS threshold FROM VALUES (70), (75), (80), (85), (90), (95)
),

scored AS (
    SELECT cp.*, t.threshold
    FROM STAGING.candidate_pairs cp
    CROSS JOIN thresholds t
),

-- Best candidate matchper ERP reco rd, per threshold — an ERP vendor resolves to at most one procurement supplier
predicted AS (
    SELECT threshold, erp_id, proc_id, name_similarity
    FROM scored
    WHERE name_similarity >= threshold
    QUALIFY ROW_NUMBER() OVER (PARTITION BY threshold, erp_id ORDER BY name_similarity DESC) = 1
),

truth_matches AS (
    SELECT erp_id, proc_id
    FROM RAW.match_truth
    WHERE match_type = 'genuine_match'
),

scored_predictions AS (
    SELECT
        p.threshold,
        p.erp_id,
        p.proc_id,
        IFF(t.erp_id IS NOT NULL, 1, 0) AS is_true_positive
    FROM predicted p
    LEFT JOIN truth_matches t
      ON p.erp_id = t.erp_id AND p.proc_id = t.proc_id
),

metrics AS (
    SELECT
        threshold,
        COUNT(*)                                            AS predicted_count,
        SUM(is_true_positive)                                AS true_positives,
        COUNT(*) - SUM(is_true_positive)                    AS false_positives,
        (SELECT COUNT(*) FROM truth_matches) - SUM(is_true_positive) AS false_negatives
    FROM scored_predictions
    GROUP BY threshold
),

rates AS (
    SELECT *,
        ROUND(true_positives / NULLIF(true_positives + false_positives, 0), 3) AS precision,
        ROUND(true_positives / NULLIF(true_positives + false_negatives, 0), 3) AS recall
    FROM metrics
)

SELECT
    threshold,
    predicted_count,
    true_positives,
    false_positives,
    false_negatives,
    precision,
    recall,
    ROUND(2 * precision * recall / NULLIF(precision + recall, 0), 3) AS f1_score
FROM rates
ORDER BY threshold;


-- Review sweep

SELECT * FROM STAGING.match_tuning_report ORDER BY threshold;
