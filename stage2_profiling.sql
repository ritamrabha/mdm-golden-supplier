

USE DATABASE mdm_golden_supplier;

-- creatin the profiling results table
CREATE OR REPLACE TABLE STAGING.profile_results (
    profiled_at   TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    source_table  STRING,
    column_name   STRING,
    metric_name   STRING,
    metric_value  STRING
);

-- Row counting
INSERT INTO STAGING.profile_results (source_table, column_name, metric_name, metric_value)
SELECT 'erp_vendor_master', '(all)', 'row_count', TO_VARCHAR(COUNT(*)) FROM RAW.erp_vendor_master
UNION ALL
SELECT 'proc_supplier_export', '(all)', 'row_count', TO_VARCHAR(COUNT(*)) FROM RAW.proc_supplier_export;

-- 3 null counts 
INSERT INTO STAGING.profile_results (source_table, column_name, metric_name, metric_value)
SELECT 'erp_vendor_master', 'tax_id', 'nulls_count_pct',
       TO_VARCHAR(COUNT_IF(tax_id IS NULL)) || ' of ' || TO_VARCHAR(COUNT(*)) || ' (' ||
       TO_VARCHAR(ROUND(100.0 * COUNT_IF(tax_id IS NULL) / COUNT(*), 1)) || '%)'
FROM RAW.erp_vendor_master
UNION ALL
SELECT 'erp_vendor_master', 'phone', 'nulls_count_pct',
       TO_VARCHAR(COUNT_IF(phone IS NULL)) || ' of ' || TO_VARCHAR(COUNT(*)) || ' (' ||
       TO_VARCHAR(ROUND(100.0 * COUNT_IF(phone IS NULL) / COUNT(*), 1)) || '%)'
FROM RAW.erp_vendor_master
UNION ALL
SELECT 'proc_supplier_export', 'tax_id', 'nulls_count_pct',
       TO_VARCHAR(COUNT_IF(tax_id IS NULL)) || ' of ' || TO_VARCHAR(COUNT(*)) || ' (' ||
       TO_VARCHAR(ROUND(100.0 * COUNT_IF(tax_id IS NULL) / COUNT(*), 1)) || '%)'
FROM RAW.proc_supplier_export
UNION ALL
SELECT 'proc_supplier_export', 'email', 'nulls_count_pct',
       TO_VARCHAR(COUNT_IF(email IS NULL)) || ' of ' || TO_VARCHAR(COUNT(*)) || ' (' ||
       TO_VARCHAR(ROUND(100.0 * COUNT_IF(email IS NULL) / COUNT(*), 1)) || '%)'
FROM RAW.proc_supplier_export;

-- distinct name count d
INSERT INTO STAGING.profile_results (source_table, column_name, metric_name, metric_value)
SELECT 'erp_vendor_master', 'vendor_name', 'distinct_count', TO_VARCHAR(COUNT(DISTINCT vendor_name))
FROM RAW.erp_vendor_master
UNION ALL
SELECT 'proc_supplier_export', 'supplier_name', 'distinct_count', TO_VARCHAR(COUNT(DISTINCT supplier_name))
FROM RAW.proc_supplier_export;

-- duplicate names 
INSERT INTO STAGING.profile_results (source_table, column_name, metric_name, metric_value)
SELECT 'erp_vendor_master', 'vendor_name', 'duplicate_name_rows', TO_VARCHAR(COUNT(*))
FROM (
    SELECT vendor_name FROM RAW.erp_vendor_master
    GROUP BY vendor_name
    HAVING COUNT(*) > 1
)
UNION ALL
SELECT 'proc_supplier_export', 'supplier_name', 'duplicate_name_rows', TO_VARCHAR(COUNT(*))
FROM (
    SELECT supplier_name FROM RAW.proc_supplier_export
    GROUP BY supplier_name
    HAVING COUNT(*) > 1
);

-- 6. Irregular whitespace (leading/trailing/double spaces) — 
INSERT INTO STAGING.profile_results (source_table, column_name, metric_name, metric_value)
SELECT 'erp_vendor_master', 'vendor_name', 'names_with_irregular_whitespace',
       TO_VARCHAR(COUNT_IF(vendor_name != REGEXP_REPLACE(TRIM(vendor_name), '\\s+', ' ')))
FROM RAW.erp_vendor_master
UNION ALL
SELECT 'proc_supplier_export', 'supplier_name', 'names_with_irregular_whitespace',
       TO_VARCHAR(COUNT_IF(supplier_name != REGEXP_REPLACE(TRIM(supplier_name), '\\s+', ' ')))
FROM RAW.proc_supplier_export;

-- casing inconsistency
INSERT INTO STAGING.profile_results (source_table, column_name, metric_name, metric_value)
SELECT 'erp_vendor_master', 'vendor_name', 'all_uppercase_names', TO_VARCHAR(COUNT_IF(vendor_name = UPPER(vendor_name)))
FROM RAW.erp_vendor_master
UNION ALL
SELECT 'erp_vendor_master', 'vendor_name', 'all_lowercase_names', TO_VARCHAR(COUNT_IF(vendor_name = LOWER(vendor_name)))
FROM RAW.erp_vendor_master
UNION ALL
SELECT 'proc_supplier_export', 'supplier_name', 'all_uppercase_names', TO_VARCHAR(COUNT_IF(supplier_name = UPPER(supplier_name)))
FROM RAW.proc_supplier_export
UNION ALL
SELECT 'proc_supplier_export', 'supplier_name', 'all_lowercase_names', TO_VARCHAR(COUNT_IF(supplier_name = LOWER(supplier_name)))
FROM RAW.proc_supplier_export;

-- oldest / newest last_updated
INSERT INTO STAGING.profile_results (source_table, column_name, metric_name, metric_value)
SELECT 'erp_vendor_master', 'last_updated', 'date_range',
       'min=' || MIN(last_updated) || ' max=' || MAX(last_updated)
FROM RAW.erp_vendor_master
UNION ALL
SELECT 'proc_supplier_export', 'last_updated', 'date_range',
       'min=' || MIN(last_updated) || ' max=' || MAX(last_updated)
FROM RAW.proc_supplier_export;

-- Review 
SELECT source_table, column_name, metric_name, metric_value
FROM STAGING.profile_results
ORDER BY source_table, metric_name;
