# 30-Minute Setup Guide: Stage 0 + 1

**Objective:** Snowflake trial + data generation + load into RAW schema

**Total time:** ~30 minutes

---

## PART A: Snowflake Setup (8 minutes)

### Step 1: Sign Up (3 min)

1. Go to **https://signup.snowflake.com**
2. Fill in the form:
   - Email: your actual email
   - Name: your name
   - Company: "Personal"
   - Country: India
   - Edition: **Standard** (default)
   - Cloud: **AWS**
   - Region: **us-east-1**
3. Click **Create Account**
4. Check your email → click confirmation link
5. Set a password and remember it
6. You land in **Snowsight** (the Snowflake web UI)

### Step 2: Create Warehouse (2 min)

1. Left sidebar → **Admin** → **Compute**
2. Click **+ Warehouse**
3. Name: `COMPUTE_XS`
4. Size: `X-Small` (dropdown)
5. Auto Suspend: `1` minute (default)
6. Click **Create Warehouse**
7. Wait for status to show "Started" ✅

### Step 3: Create Database & Schemas (2 min)

1. Click the **Worksheets** tab (or query editor icon)
2. You're now in a blank SQL worksheet
3. **Run each of these one at a time** (Ctrl+Enter or click Run):

```sql
CREATE DATABASE mdm_golden_supplier;
```

Wait for ✅ (green checkmark).

```sql
CREATE SCHEMA mdm_golden_supplier.RAW;
CREATE SCHEMA mdm_golden_supplier.STAGING;
CREATE SCHEMA mdm_golden_supplier.CURATED;
```

Wait for ✅✅✅.

### Step 4: Save Connection Details (1 min)

1. Top-right corner → click your **username icon**
2. Click **Settings**
3. Copy these three things into a text file:
   - **Account Identifier** (e.g., `xy12345.us-east-1`)
   - **User** (your email)
   - **Password** (what you just set)

You'll paste these into Python in a moment.

---

## PART B: Python Setup & Execution (22 minutes)

### Step 5: Create Local Project (2 min)

Terminal or PowerShell:

```bash
mkdir mdm-golden-supplier
cd mdm-golden-supplier
git init
```

### Step 6: Save the Python Files

I've generated these files for you. Create them in the `mdm-golden-supplier` folder:

1. **`config.py`** — Edit it and paste your Snowflake credentials
2. **`data_generator.py`** — Fetches SEC data and creates CSVs
3. **`load_raw.py`** — Loads CSVs into Snowflake
4. **`.gitignore`** — Tells Git what not to commit
5. **`README.md`** — Full project documentation

(See file listings below)

### Step 7: Edit config.py

Open `config.py` in a text editor and replace:

```python
SNOWFLAKE_CONFIG = {
    "account": "YOUR_ACCOUNT_IDENTIFIER",  # ← Paste from Step 4
    "user": "YOUR_EMAIL",                   # ← Paste from Step 4
    "password": "YOUR_PASSWORD",            # ← Paste from Step 4
    "warehouse": "COMPUTE_XS",
    "database": "mdm_golden_supplier",
    "schema": "RAW"
}
```

**Save and close.**

### Step 8: Install Python Dependencies (2 min)

Terminal, in the `mdm-golden-supplier` folder:

```bash
pip install snowflake-connector-python pandas requests
```

Wait for it to finish.

### Step 9: Run Data Generator (5 min)

Terminal:

```bash
python data_generator.py
```

You'll see output like:

```
============================================================
STAGE 1: DATA GENERATION
============================================================

[1/5] Fetching company names from SEC EDGAR...
✓ Fetched 10000 companies from SEC

[2/5] Selecting 500 companies and generating ground truth...
  Adding hard negatives for precision tuning...
✓ Generated 208 ground truth pairs
  - Genuine matches: 180
  - Hard negatives: 5

[3/5] Creating divergent source systems with realistic corruption...
✓ Created 500 ERP records
✓ Created 500 Procurement records

[4/5] Writing CSV files...
  ✓ data/erp_vendor_master.csv (500 rows)
  ✓ data/proc_supplier_export.csv (500 rows)
  ✓ data/match_truth.csv (208 rows)

[5/5] Generation complete!
============================================================
```

This took ~2–3 minutes. Three CSV files now exist in your `data/` folder.

### Step 10: Load into Snowflake (5 min)

Terminal:

```bash
python load_raw.py
```

You'll see:

```
============================================================
LOADING RAW DATA INTO SNOWFLAKE
============================================================

[1/4] Connecting to Snowflake...
✓ Connected to Snowflake

[2/4] Loading ERP Vendor Master...
✓ Loaded 500/500 ERP records

[3/4] Loading Procurement Supplier Export...
✓ Loaded 500/500 Procurement records

[4/4] Loading Ground Truth (evaluation reference)...
✓ Loaded 208/208 Ground Truth pairs

============================================================
VERIFICATION
============================================================

erp_vendor_master:       500 rows
proc_supplier_export:    500 rows
match_truth:             208 rows

✓ All data loaded successfully!
```

### Step 11: Verify in Snowsight (3 min)

Back in Snowsight, run:

```sql
SELECT COUNT(*) FROM mdm_golden_supplier.RAW.erp_vendor_master;
SELECT COUNT(*) FROM mdm_golden_supplier.RAW.proc_supplier_export;
SELECT COUNT(*) FROM mdm_golden_supplier.RAW.match_truth;
```

You should see:
- 500
- 500
- 208

Spot-check a record:

```sql
SELECT * FROM mdm_golden_supplier.RAW.erp_vendor_master LIMIT 5;
```

You'll see messy, inconsistent names — exactly like real data.

---

## What You Now Have

✅ Snowflake trial account with a working warehouse  
✅ Three schemas: RAW, STAGING, CURATED  
✅ 500 ERP supplier records (formal, tax-ID-heavy, stale)  
✅ 500 Procurement supplier records (abbreviations, fresher, missing tax IDs)  
✅ 208 ground-truth matches (so you can measure matching accuracy)  
✅ Local Git repo tracking your code  

## What's Next

Run Stage 2 (Profiling SQL) to understand what makes the data messy. Then Stage 3–6 to build the matching, survivorship, and quality checks.

---

## Troubleshooting

| Problem | Solution |
|---|---|
| "Connection failed: Invalid account identifier" | Check the account ID format: `xy12345.us-east-1`. Copy it exactly from Snowflake settings. |
| "File not found: data_generator.py" | Make sure you're in the `mdm-golden-supplier` folder and the files are saved there. |
| "SEC data fetch failed" | `data_generator.py` falls back to sample data. Pipeline works identically. |
| Snowflake query is slow or times out | Restart your warehouse: Admin → Compute → COMPUTE_XS → Start. |
| Python says "no module named snowflake" | Run `pip install snowflake-connector-python pandas requests` again. |

---

## Git Commit This Stage

```bash
git add config.py .gitignore README.md SETUP_GUIDE.md data_generator.py load_raw.py
git commit -m "Stage 0-1: Snowflake setup + data generation + RAW load complete"
```

(Don't commit `data/` folder — it's in `.gitignore`)

---

**Time check:** You should be ~30 minutes in. Next: Stage 2 (Profiling).
