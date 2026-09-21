# Supplier Master Data Reconciliation Pipeline

A Snowflake + SQL + Python pipeline that reconciles two disagreeing supplier
systems into a single trusted "golden record" — with matching accuracy that's
measured against ground truth, not asserted.

Built as a portfolio project for data-engineering / MDM interviews. Two
divergent source systems, an ERP vendor master and a Procurement/AP export,
describe the same real-world suppliers but disagree on name formatting,
completeness, and freshness. The pipeline profiles, standardizes, fuzzy-matches,
and merges them — and every design decision below is backed by a number, not
a guess.

## Headline result

**At similarity threshold 90 (chosen by sweeping 70–95 against a held-out
ground truth): 98.3% precision, 98.0% recall, F1 0.981.**

Zero of the 5 deliberately planted "hard negative" pairs (genuinely different
companies with deceptively similar names) were incorrectly auto-merged —
confirmed by direct query, not assumption.

## Architecture

```
RAW                          STAGING                         CURATED
─────────────────────────────────────────────────────────────────────────
erp_vendor_master    ┐
                      ├──→ profile_results (Stage 2: null %, dupes, ranges)
proc_supplier_export  ┘
                      │
                      ├──→ suppliers_standardized (Stage 3: clean_name,
                      │     normalized legal suffixes, both sources unioned)
                      │
                      ├──→ candidate_pairs (Stage 4: blocked on name prefix,
                      │     scored with JAROWINKLER_SIMILARITY + EDITDISTANCE)
                      │
                      ├──→ match_tuning_report (Stage 4: precision/recall/F1
                      │     swept across 6 thresholds against ground truth)
                      │
                      ├──→ mutual_best_pairs (Stage 5: stable/mutual-best
                      │     matching on top of the threshold decision)
                      │
match_truth ──────────┘     (ground truth, used only for scoring)
                      │
                      ├──→ golden_supplier ─────────────→ (Stage 5: one row
                      │     per real supplier, attribute-level survivorship)
                      │
                      ├──→ record_lineage ──────────────→ (Stage 5: which
                      │     source won each attribute, and why)
                      │
                      └──→ steward_queue ───────────────→ (Stage 5: grey-zone
                            matches, 80–89 similarity, pending human review)
```

## Results, stage by stage

**Stage 1 — Data:** 405 ERP records, 320 Procurement records (725 total),
seeded from 415 real US company names and corrupted realistically (suffix
variants, typos, whitespace, casing drift). 305 ground-truth pairs: 300
genuine matches + 5 hard negatives.

**Stage 2 — Profiling:** ERP tax_id null rate 7.7% vs. Procurement 44.4%
(confirms ERP as the trustworthy source for tax ID). ERP phone null 21% vs.
Procurement email null 39.1% (both sources meaningfully incomplete on contact
info). Irregular whitespace in 12.5% of Procurement names, 0% of ERP — matches
the corruption design exactly. Also surfaced 2 exact duplicate names inside
ERP itself, an unplanned finding.

**Stage 3 — Standardization:** Unioned both sources into one shape; built a
`clean_name` column via uppercase → strip punctuation → collapse whitespace →
canonicalize legal-suffix variants (`INCORPORATED`→`INC`, `SVCS`→`SERVICES`,
etc.) with word-boundary-safe `REGEXP_REPLACE`. Row count verified unchanged
(725) — standardization cleans values, never drops or duplicates rows.

**Stage 4 — Matching:** Blocked on the first 4 characters of the standardized
name rather than city — city-blocking would have excluded most hard negatives
from ever being compared, since their cities were randomized independently.
Swept thresholds 70/75/80/85/90/95 in one query; threshold 90 gave the best
F1 (0.981). At 95, precision barely moved but recall fell to 92.3% as
typo-corrupted genuine matches dropped below the cutoff.

**Stage 5 — Survivorship:** Added mutual-best (stable) matching on top of the
threshold, so no procurement record can be claimed by two different ERP
vendors. Result: 294 auto-merged pairs, 1 pair sent to steward review, 110
ERP and 25 Procurement records with no acceptable match. `golden_supplier`
has 429 rows, all distinct — zero duplicates. `record_lineage` has exactly
1,470 rows (294 × 5 attributes). Confirmed by direct query that all 5 hard
negatives were excluded before the auto-merge threshold even applied.

**Stage 6 — Data quality:** 9 automated pytest assertions covering identity
(no duplicate golden records), completeness (every source row accounted for
in exactly one outcome), required fields, lineage integrity, and matching
correctness against ground truth (zero hard negatives leaked into
auto-merge).

## Survivorship rules

| Attribute | Rule | Why |
|---|---|---|
| `supplier_name` | ERP always wins | ERP is the vendor master of record |
| `tax_id` | ERP first, fall back to Procurement | ERP's null rate (7.7%) is far lower (Stage 2 finding) |
| `phone` / `email` | Both kept, separately | Different fields collected by different systems — not a real conflict |
| `city` | Most recently-updated source wins | Recency matters more than "trust" for something that can simply change |
| `last_updated` | `GREATEST()` of both sources | Golden record reflects whichever source touched it last |

Grey zone (80–89 similarity) routes to `steward_queue` for human review
rather than auto-merging or discarding.

## Running it

```bash
pip install snowflake-connector-python pandas requests pytest

# Edit config.py with your Snowflake credentials, then:
python data_generator.py     # generates the two source CSVs + ground truth
python load_raw.py           # loads them into Snowflake RAW schema
```

Then run each stage's SQL file in order in Snowsight:
`stage2_profiling.sql` → `stage3_standardization.sql` →
`stage4_matching.sql` → `stage5_survivorship.sql`

Finally:

```bash
pytest test_data_quality.py -v
```

## Repo structure

```
mdm-golden-supplier/
├── README.md
├── config.py                     (Snowflake credentials — not committed)
├── data_generator.py             (Stage 1: source + ground-truth generation)
├── load_raw.py                   (Stage 1: load into RAW)
├── stage2_profiling.sql          (Stage 2)
├── stage3_standardization.sql    (Stage 3)
├── stage4_matching.sql           (Stage 4: blocking, matching, threshold sweep)
├── stage5_survivorship.sql       (Stage 5: golden record, lineage, steward queue)
├── test_data_quality.py          (Stage 6: automated DQ assertions)
└── data/                         (generated CSVs, not committed)
```

## What I'd do differently at production scale

Snowflake's native Data Metric Functions for scheduled profiling (Enterprise
edition only — this project deliberately stayed on Standard, so DMFs aren't
used here); partitioning the block-key scan so it doesn't degrade on tables
with millions of rows; Streams + Tasks so new supplier records get matched
incrementally instead of the whole pipeline re-running as a batch job.
