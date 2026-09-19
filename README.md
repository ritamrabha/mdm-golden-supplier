# MDM Golden Supplier Reconciliation Pipeline

**A data engineering portfolio project** that demonstrates master data management through a supplier reconciliation pipeline with measured match tuning and survivorship rules.

## What's Built (Stage 0 + 1)

### The Problem
Two enterprise systems hold supplier records that represent the same real-world entities but disagree on names, formats, and even presence/absence of tax IDs. The pipeline reconciles them into a single trusted "golden record" and quantifies matching accuracy.

### The Data

Three tables in Snowflake's `RAW` schema:

| Table | Source | Rows | Purpose |
|---|---|---|---|
| `erp_vendor_master` | ERP system | ~500 | Formal, tax-ID-heavy, stale |
| `proc_supplier_export` | Procurement/AP | ~500 | Trade names, abbreviations, fresher |
| `match_truth` | Generated ground truth | ~200 pairs | Answer key for scoring matches |

**Why this matters:** You can measure whether your matching rules work. Most student projects just fuzzy-match and guess at a threshold. This one scores precision and recall so you can defend your choices in an interview.

### Why Supplier Data

Infoverity's MDM JD specifically names supplier onboarding as a workflow. Using their domain reads as contextual awareness.

Hard negatives (pairs of genuinely different companies with deceptively similar names) are baked in, so your precision score won't trivialize to 100%.

## Running It Yourself

### Prerequisites
- Python 3.8+
- Snowflake trial account (free, 30 days, $400 credits)
- pip

### Quick Start (30 min)

1. **Sign up for Snowflake trial** (https://signup.snowflake.com)
   - Standard edition, AWS, us-east-1
   - Note your account ID, email, and password

2. **In Snowsight (web UI):**
   - Create warehouse `COMPUTE_XS` (X-Small, auto-suspend 1 min)
   - Run:
     ```sql
     CREATE DATABASE mdm_golden_supplier;
     CREATE SCHEMA mdm_golden_supplier.RAW;
     CREATE SCHEMA mdm_golden_supplier.STAGING;
     CREATE SCHEMA mdm_golden_supplier.CURATED;
     ```

3. **Locally:**
   ```bash
   git clone <this repo>
   cd mdm-golden-supplier
   pip install snowflake-connector-python pandas requests
   
   # Edit config.py with your Snowflake credentials
   python data_generator.py    # ~2 min: fetches SEC data, creates corrupted CSVs
   python load_raw.py          # ~5 min: loads into Snowflake
   ```

4. **Verify in Snowsight:**
   ```sql
   SELECT COUNT(*) FROM mdm_golden_supplier.RAW.erp_vendor_master;
   SELECT * FROM mdm_golden_supplier.RAW.erp_vendor_master LIMIT 3;
   ```

## What's Next: The Full Pipeline

This is **Stage 1 of 6**. You now have:
- ✅ Snowflake database + schemas
- ✅ Two messy source systems loaded
- ✅ Ground truth for evaluation

### Coming stages:
- **Stage 2:** Profiling SQL (null %, duplicates, range checks)
- **Stage 3:** Standardization (STAGING schema)
- **Stage 4:** Fuzzy matching + threshold sweep (core of the project)
- **Stage 5:** Survivorship rules + attribute lineage
- **Stage 6:** Data quality tests + README with results

By **Stage 4**, you'll have a chart showing precision/recall at each threshold (75/80/85/90/95) so you can defend your match threshold choice with data, not a guess. That's the differentiator.

## Project Structure

```
mdm-golden-supplier/
├── README.md                    (this file)
├── .gitignore                   (never commit data or credentials)
├── config.py                    (your Snowflake connection — edit before running)
├── data_generator.py            (fetches SEC data, creates corrupted sources)
├── load_raw.py                  (loads CSVs into Snowflake RAW schema)
├── data/                        (generated CSVs, local only, never commit)
└── (future stages)
    ├── profiling_sql.sql        (Stage 2)
    ├── staging_sql.sql          (Stage 3)
    ├── matching_sql.sql         (Stage 4)
    ├── survivorship_sql.sql     (Stage 5)
    └── dq_tests.py              (Stage 6)
```

## Interview Talking Points

When asked about this project in an interview:

**"I built a supplier master reconciliation pipeline in Snowflake that demonstrates real MDM thinking."**

- **Data profiling first:** Before matching, I profiled the raw sources to understand null %, duplicates, and format variance.
- **Measured matching:** I swept thresholds (75-95%) against a held-out ground truth to score precision and recall, so I could defend my threshold choice with a chart, not a guess.
- **Attribute-level survivorship:** Not just "which record wins," but "phone came from ERP because it's more trusted; address came from procurement because it's fresher." Every win is logged in a lineage table.
- **Grey-zone handling:** Records with similarity in the 80-90 range go into a steward queue for human review, which is exactly what MDM platforms do.
- **Automated quality checks:** Python test suite asserts no duplicate golden records, no nulls in critical fields, and every source row accounted for.

**Why it matters:** This shows you understand that MDM isn't just fuzzy matching — it's data *governance* with measured trade-offs, not luck.

## Architecture Diagram

```
RAW                      STAGING              CURATED
─────────────────────────────────────────────────────────

erp_vendor_master    ┐
                     ├──→ Profiling ───→ profile_results
proc_supplier_export ┘
                     
                     ┐
                     ├──→ Standardize ───→ suppliers_standardized
                     ┘
                     
                     ┐
                     ├──→ Block & Match ──→ candidate_pairs
                     │   (Jaro-Winkler)   (+ scores)
                     ├──→ Sweep Threshold ──→ match_tuning_report
                     │   (precision/recall)   (chart data)
                     ┘
                     
match_truth (for scoring, not in workflow)
                     
                     ┐
                     ├──→ Survivorship ──→ golden_supplier
                     │    (window functions) (1 row/entity)
                     │
                     ├──→ Lineage ──────→ record_lineage
                     │    (which source won each attribute)
                     │
                     └──→ Steward Queue ─→ steward_queue
                          (grey zone matches) (for manual review)
```

## Key Skills Demonstrated

- **SQL:** Window functions (ROW_NUMBER), CTEs, blocking with WHERE conditions
- **Python:** Data generation, Snowflake connector, test assertions
- **Snowflake:** Database/schema design, COPY INTO, CREATE OR REPLACE TABLE
- **Data Engineering:** Profiling, standardization, entity resolution, data quality checks
- **Communication:** This README itself, plus the match tuning chart in Stage 4

## Troubleshooting

### "Connection failed: Invalid account identifier"
- Make sure you copied your account ID correctly from Snowflake UI
- Format is usually `xy12345.us-east-1`

### "File not found: data_generator.py"
- Make sure you're in the `mdm-golden-supplier` folder when running Python commands

### "SEC data fetch failed"
- If SEC EDGAR is down, `data_generator.py` falls back to a small sample dataset
- The pipeline works identically with sample data, just fewer records

### Snowflake queries are slow
- Make sure warehouse is running (it auto-suspends after 1 min of inactivity)
- Restart it in Snowsight: Admin → Compute → COMPUTE_XS → Start

## Next: Stage 2 (Profiling)

Once you've verified the RAW data loads, run the profiling SQL (to be provided next) to get an inventory of data quality issues. This sets up the case for why standardization matters.

---

**Questions?** Check the Snowflake docs or ask in the next stage guidance.

**Ready to move forward?** Next: Profiling SQL.
