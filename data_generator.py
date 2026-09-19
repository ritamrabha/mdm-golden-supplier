"""
Data Generator for MDM Supplier Reconciliation Pipeline
Uses a built-in company list (no external API needed) to create
two divergent source systems with known ground truth.
"""

import os
import random
import csv
from datetime import datetime, timedelta

os.makedirs("data", exist_ok=True)

print("=" * 60)
print("STAGE 1: DATA GENERATION")
print("=" * 60)

# Built-in company seed list — 600 real-style US company names
# Covers manufacturing, logistics, tech, finance, healthcare, retail
SEED_COMPANIES = [
    "Apex Logistics Corporation", "BlueStar Manufacturing Inc", "Cardinal Health Systems LLC",
    "Delta Industrial Supply Co", "Eagle River Technologies", "Frontier Materials Group",
    "Global Packaging Solutions Inc", "Harvest Agricultural Services", "Iron Gate Security LLC",
    "Jade Software Consulting Inc", "Keystone Distribution Partners", "Liberty Freight Services",
    "Meridian Energy Resources LLC", "Nova Biomedical Corporation", "Olympus Precision Tools Inc",
    "Pacific Rim Trading Company", "Quantum Data Analytics LLC", "Redwood Forest Products Inc",
    "Summit Construction Group", "Titan Aerospace Components", "Union Pacific Suppliers LLC",
    "Vanguard Financial Services Inc", "Westfield Commercial Properties", "Xerxes Industrial LLC",
    "Yellowstone Environmental Group", "Zenith Electronics Corporation", "Anchor Bay Shipping Co",
    "Beacon Hill Consultants LLC", "Cascade Renewable Energy Inc", "Durable Goods Manufacturing",
    "Emerald Coast Distributors", "Falcon Ridge Systems Inc", "Gateway Medical Supplies LLC",
    "Harbor View Logistics Inc", "Inland Empire Transportation", "Jupiter Chemical Company",
    "Kings County Farm Bureau", "Lakeshore Data Services LLC", "Maple Grove Industries Inc",
    "Northern Plains Agriculture", "Oakwood Healthcare Partners", "Pinnacle Steel Works LLC",
    "Quorum Business Solutions Inc", "Riverside Paper Products Co", "Sierra Nevada Breweries",
    "Tundra Cold Storage LLC", "United Metals Corporation", "Valley Green Energy Inc",
    "Whitewater Consulting Group", "Xcaliber Precision Parts Inc", "York Industrial Fasteners",
    "Zenova Life Sciences LLC", "Absolute Power Solutions Inc", "Bridgewater Asset Management",
    "Cornerstone Building Materials", "Diamond Ridge Mining Corp", "Eastern Seaboard Trading LLC",
    "First Choice Staffing Solutions", "Granite State Insurance Group", "Hillside Medical Devices",
    "Interstate Commerce Partners", "Jasper Creek Holdings LLC", "Kirkland Industrial Services",
    "Lakewood Technology Solutions", "Midwest Grain Cooperative", "Northgate Capital Partners",
    "Ocean Blue Seafood Distributors", "Pelican Bay Resources LLC", "Queensbury Manufacturing Inc",
    "Ridgeline Construction Corp", "Southwestern Energy Partners", "Terracycle Environmental Inc",
    "Upland Agriculture Services LLC", "Venture Capital Group Inc", "Westwood Real Estate Partners",
    "Xtreme Performance Parts LLC", "Yellowhammer Industries Inc", "Zephyr Wind Energy Corp",
    "Allied Defense Systems LLC", "Breckenridge Ski Holdings Inc", "Centennial Resources Corp",
    "Dynamo Electric Supply Co", "Evergreen Timber Products LLC", "Foxwood Financial Services",
    "Greystone Capital Management", "Highpoint Medical Center LLC", "Ironwood Paper Mill Inc",
    "Juniper Networks Consulting", "Kelso Marine Services LLC", "Longview Fiber Company",
    "Mountainview Software Inc", "Nautical Systems Corporation", "Offshore Energy Partners LLC",
    "Plainview Dairy Cooperative", "Quicksilver Mining Corp", "Rocky Mountain Oil Company",
    "Sawtooth Lumber Products LLC", "Timberline Resources Inc", "Universal Supply Chain LLC",
    "Vineyard Energy Solutions Inc", "Watershed Environmental Corp", "Xcel Energy Services LLC",
    "Yorkshire Trading Company Inc", "Zion National Resources LLC", "Acadian Timber Corp",
    "Bayshore Industrial Partners", "Clearwater Paper Corporation", "Dockside Marine Supplies",
    "Empire State Properties LLC", "Firesteel Resources Inc", "Greenleaf Organics LLC",
    "Harborside Logistics Group", "Irongate Capital Partners LLC", "Jamestown Energy Corp",
    "Kestrel Defense Systems LLC", "Longhorn Cattle Company Inc", "Maplewood Dairy Farms LLC",
    "Nighthawk Oil and Gas Inc", "Outback Mining Corporation", "Peregrine Capital Group LLC",
    "Quartermaster Supply Inc", "Rawhide Energy Services LLC", "Stonewall Industries Corp",
    "Thunderbird Aviation LLC", "Underhill Construction Inc", "Vortex Energy Partners LLC",
    "Wildfire Technology Solutions", "Xanadu Resort Holdings LLC", "Yellowstone Capital Inc",
    "Zara Industrial Supplies LLC", "Adirondack Resources Corp", "Bluebell Healthcare LLC",
    "Cottonwood Energy Partners", "Dusty Trail Transport LLC", "Elderberry Farms Inc",
    "Fernwood Paper Products LLC", "Goldfinch Mining Corporation", "Hawthorne Industrial LLC",
    "Iceberg Cold Chain Solutions", "Juneau Marine Services Inc", "Kodiak Offshore Drilling",
    "Larkspur Biotech Corporation", "Magnolia Healthcare Systems", "Nightingale Medical LLC",
    "Orion Defense Contractors Inc", "Painted Hills Resources LLC", "Quail Run Properties Inc",
    "Rainier Brewing Company LLC", "Sequoia Capital Ventures", "Tidewater Marine Services",
    "Uplift Aviation Partners LLC", "Verdant Energy Solutions Inc", "Whitecap Resources Corp",
    "Xylem Water Technologies LLC", "Yarrow Medical Supplies Inc", "Zephyrhills Holdings LLC",
    "Ashland Chemical Company LLC", "Breakwater Marine Inc", "Crestline Holdings Corporation",
    "Deepwater Exploration LLC", "Elkhorn Industries Inc", "Flatrock Energy Services LLC",
    "Glencoe Capital Partners Inc", "Hillcrest Medical Supplies", "Ironbark Resources LLC",
    "Jackrabbit Transportation Inc", "Keystone Pipeline Services", "Lakeview Capital Group LLC",
    "Mesquite Energy Partners LLC", "Newpark Resources Inc", "Overland Transport Corp",
    "Pawnee Industrial Services LLC", "Quickstep Technologies Inc", "Redrock Capital Partners",
    "Sandstone Energy Resources", "Terracotta Building Materials", "Uranium Energy Corp LLC",
    "Valleybrook Consulting Inc", "Wicklow Industrial Holdings", "Xenon Scientific LLC",
    "Yucatan Resources Corp", "Zabar Food Distribution LLC", "Allegheny Energy Services",
    "Broadmoor Capital Group LLC", "Chestnut Hill Properties Inc", "Drummond Coal Company LLC",
    "Eastwood Construction Group", "Foxglove Pharmaceuticals Inc", "Graystone Financial LLC",
    "Hawthorn Medical Devices Inc", "Imperial Industries Corp", "Javelin Defense Systems LLC",
    "Kingfisher Oil Services Inc", "Limestone Resources Corp", "Mockingbird Media LLC",
    "Norwood Industrial Partners", "Osage Plains Agriculture LLC", "Platte River Energy Inc",
    "Quicken Financial Services LLC", "Redbud Capital Partners Inc", "Sunstone Hotel Management",
    "Trident Marine Corporation", "Underwood Paper Products LLC", "Viking Industrial Services",
    "Waterford Crystal Holdings LLC", "Xeriscape Landscaping Inc", "Yosemite Capital Partners",
    "Zirconia Materials Corp LLC", "Alder Creek Timber LLC", "Birchwood Properties Inc",
    "Copperleaf Energy Services", "Dogwood Environmental LLC", "Elderwood Capital Group Inc",
    "Fern Valley Farms LLC", "Goldenrod Agriculture Inc", "Hackberry Resources Corp",
    "Indigo Technology Partners LLC", "Juniper Ridge Holdings Inc", "Kinnickinnic River Corp",
    "Larimer County Resources LLC", "Mulberry Street Holdings Inc", "Nightshade Biotech LLC",
    "Osceola Resources Corporation", "Paintbrush Energy Solutions", "Quicksilver Resources LLC",
    "Redbark Timber Products Inc", "Servicemaster Holdings LLC", "Thornberry Capital Group",
    "Ultramar Diamond Shamrock LLC", "Verbena Holdings Corporation", "Wintergreen Energy LLC",
    "Xanthus Capital Partners Inc", "Yarrow Creek Holdings LLC", "Zinnia Medical Supplies Inc",
    "Armadillo Energy Services LLC", "Bluegrass Capital Partners Inc", "Catalina Resources Corp",
    "Driftwood Energy Partners LLC", "Elderberry Capital Group Inc", "Figtree Holdings LLC",
    "Galloway Industrial Services", "Hollybrook Capital LLC", "Inkberry Resources Corp",
    "Jacaranda Holdings LLC", "Kumquat Distribution Inc", "Lemongrass Holdings Corp",
    "Mangrove Capital Partners LLC", "Nasturtium Holdings Inc", "Olive Branch Holdings LLC",
    "Persimmon Capital Group Inc", "Quince Resources Corporation", "Rosewood Capital LLC",
    "Sagebrush Energy Partners Inc", "Tamarack Resources Corp", "Uvalde Energy Services LLC",
    "Verbena Capital Group Inc", "Wisteria Holdings LLC", "Xylosma Capital Partners Inc",
    "Yarrow Holdings Corporation", "Zoysia Resources LLC", "Acapulco Holdings Inc",
    "Bermuda Triangle Trading LLC", "Cancun Resort Holdings Inc", "Durango Mining Corp LLC",
    "El Paso Energy Partners LLC", "Fresno Agricultural Services", "Guadalupe Resources Corp",
    "Havana Trading Company LLC", "Iquique Maritime Services Inc", "Jalisco Holdings Corp",
    "Kingston Marine Services LLC", "Lima Capital Partners Inc", "Medellin Resources Corp",
    "Nassau Holdings Corporation", "Oaxaca Agricultural LLC", "Panama Canal Services Inc",
    "Quito Capital Group LLC", "Recife Trading Company Inc", "Santos Holdings Corp LLC",
    "Tijuana Industrial Services", "Uruapan Resources Corp LLC", "Valencia Holdings Inc",
    "Windward Islands Trading LLC", "Xalapa Resources Corporation", "Yucatan Holdings LLC",
    "Zacatecas Mining Corp LLC", "Aberdeen Industrial Services", "Belfast Marine Holdings LLC",
    "Cardiff Resources Corporation", "Dublin Capital Partners LLC", "Edinburgh Holdings Inc",
    "Falkirk Industrial Services LLC", "Glasgow Capital Group Inc", "Harrogate Holdings Corp",
    "Inverness Resources LLC", "Jersey Holdings Corporation", "Kilmarnock Services Inc",
    "Leeds Industrial Partners LLC", "Manchester Capital Group Inc", "Newcastle Holdings Corp",
    "Oxford Capital Partners LLC", "Perth Resources Corporation", "Quebec Holdings Inc LLC",
    "Rotterdam Trading Company", "Stockholm Capital Partners LLC", "Toulouse Holdings Corp",
    "Uppsala Resources Corporation", "Vienna Capital Group LLC", "Warsaw Holdings Inc",
    "Xian Resources Corporation LLC", "Yokohama Trading Company Inc", "Zagreb Holdings Corp",
    "Aalborg Industrial Services LLC", "Bergen Capital Partners Inc", "Copenhagen Holdings Corp",
    "Dusseldorf Resources LLC", "Eindhoven Industrial Inc", "Frankfurt Capital Group LLC",
    "Geneva Holdings Corporation", "Hamburg Resources Corp LLC", "Istanbul Capital Partners",
    "Jerusalem Holdings Inc LLC", "Krakow Industrial Services", "Lyon Capital Group LLC",
    "Munich Holdings Corporation", "Nuremberg Resources Corp", "Oslo Capital Partners LLC",
    "Prague Holdings Inc", "Rotterdam Capital Group LLC", "Salzburg Resources Corp",
    "Turin Holdings Corporation LLC", "Utrecht Capital Partners Inc", "Valletta Holdings Corp",
    "Wroclaw Resources LLC", "Xanthi Capital Group Inc", "Yerevan Holdings Corp LLC",
    "Zurich Capital Partners Inc", "Anchorage Capital Group LLC", "Boise Holdings Corporation",
    "Cheyenne Resources Corp LLC", "Denver Capital Partners Inc", "Eugene Holdings Corp",
    "Flagstaff Resources LLC", "Glendale Capital Group Inc", "Helena Holdings Corp LLC",
    "Idaho Falls Capital Partners", "Jackson Hole Holdings Inc", "Kalispell Resources Corp",
    "Laramie Capital Group LLC", "Missoula Holdings Corporation", "Nampa Resources Corp LLC",
    "Ogden Capital Partners Inc", "Pocatello Holdings Corp LLC", "Quincy Resources Inc",
    "Reno Capital Group LLC", "Spokane Holdings Corporation", "Tacoma Resources Corp LLC",
    "Utica Capital Partners Inc", "Vancouver Holdings Corp LLC", "Wenatchee Resources Inc",
    "Yakima Capital Group LLC", "Yuma Holdings Corporation", "Zion Resources Corp LLC",
    "Abilene Capital Partners Inc", "Beaumont Holdings Corp LLC", "Corpus Christi Resources",
    "Dallas Capital Group LLC", "El Paso Holdings Corporation", "Fort Worth Resources Corp",
    "Galveston Capital Partners LLC", "Houston Holdings Inc", "Irving Resources Corp LLC",
    "Jacksonville Capital Group", "Killeen Holdings Corp LLC", "Laredo Resources Inc",
    "McAllen Capital Partners LLC", "Nacogdoches Holdings Corp", "Orange County Resources LLC",
    "Pasadena Capital Group Inc", "Round Rock Holdings Corp LLC", "San Antonio Resources Inc",
    "Temple Capital Partners LLC", "Uvalde Holdings Corporation", "Victoria Resources Corp",
    "Waco Capital Group LLC", "Wichita Falls Holdings Inc", "Xenia Resources Corp LLC",
    "Yoakum Capital Partners Inc", "Zapata Holdings Corporation", "Abilene Resources LLC",
    "Brownsville Capital Group Inc", "Conroe Holdings Corp LLC", "Denton Resources Inc",
    "Edinburg Capital Partners LLC", "Frisco Holdings Corporation", "Garland Resources Corp",
    "Harlingen Capital Group LLC", "Irving Holdings Inc", "Jourdanton Resources Corp LLC",
    "Kerrville Capital Partners Inc", "Longview Holdings Corp LLC", "Midland Resources Inc",
    "New Braunfels Capital Group LLC", "Odessa Holdings Corporation", "Pampa Resources Corp",
    "Plainview Capital Partners LLC", "Richardson Holdings Corp", "Seguin Resources Inc LLC",
    "Texarkana Capital Group LLC", "Uvalde County Resources Corp", "Vernon Holdings Inc LLC",
    "Weatherford Capital Partners", "Xcel Holdings Corporation LLC", "Yorktown Resources Inc",
    "Zavala Capital Group LLC"
]

print(f"\n[1/5] Using built-in company list...")
print(f"✓ {len(SEED_COMPANIES)} companies available")

# --- Corruption helpers ---

SUFFIX_VARIANTS = {
    " Inc": [" Inc.", " Incorporated", " INC", " inc"],
    " LLC": [" L.L.C.", " LLC.", " llc", " L.L.C"],
    " Corp": [" Corp.", " Corporation", " CORP", " corp"],
    " Co": [" Co.", " Company", " CO"],
    " Ltd": [" Ltd.", " Limited", " LTD"],
    " Group": [" Grp", " Grp.", " GROUP"],
    " Services": [" Svc", " Svcs", " Svc.", " SERVICES"],
    " Solutions": [" Sol", " Soln", " SOLUTIONS"],
    " Partners": [" Ptrs", " Ptr.", " PARTNERS"],
    " Holdings": [" Hldgs", " Hldg", " HOLDINGS"],
}

def corrupt_suffix(name):
    for suffix, variants in SUFFIX_VARIANTS.items():
        if suffix in name:
            if random.random() > 0.5:
                return name.replace(suffix, random.choice(variants), 1)
    return name

def corrupt_ampersand(name):
    if " & " in name and random.random() > 0.5:
        return name.replace(" & ", " and ")
    if " and " in name and random.random() > 0.5:
        return name.replace(" and ", " & ")
    return name

def corrupt_casing(name):
    r = random.random()
    if r < 0.2:
        return name.upper()
    elif r < 0.35:
        return name.lower()
    return name

def add_whitespace(name):
    if random.random() < 0.15:
        words = name.split()
        if len(words) > 1:
            pos = random.randint(0, len(words)-1)
            words[pos] = "  " + words[pos]
        return " ".join(words)
    return name

def introduce_typo(text):
    if random.random() > 0.12:
        return text
    chars = list(text)
    i = random.randint(0, len(chars)-1)
    chars[i] = random.choice("abcdefghijklmnopqrstuvwxyz")
    return "".join(chars)

def corrupt_erp(name):
    """ERP style: formal but slightly stale, minor suffix/casing issues"""
    name = corrupt_suffix(name)
    name = corrupt_casing(name)
    return name

def corrupt_proc(name):
    """Procurement style: abbreviations, typos, ampersand swaps, whitespace"""
    name = corrupt_suffix(name)
    name = corrupt_ampersand(name)
    name = introduce_typo(name)
    name = add_whitespace(name)
    if random.random() < 0.3:
        name = corrupt_casing(name)
    return name

def random_phone():
    return f"({random.randint(200,999)}) {random.randint(200,999)}-{random.randint(1000,9999)}"

def random_tax_id():
    return f"TX{random.randint(10,99)}-{random.randint(1000000,9999999)}"

def random_date(days_ago_min, days_ago_max):
    return (datetime.now() - timedelta(days=random.randint(days_ago_min, days_ago_max))).strftime("%Y-%m-%d")

CITIES = ["New York", "Chicago", "Houston", "Los Angeles", "Phoenix",
          "Philadelphia", "San Antonio", "Dallas", "San Diego", "Jacksonville"]

# ---- Build matched pairs (same entity in both systems) ----
print(f"\n[2/5] Selecting companies and generating ground truth...")

random.shuffle(SEED_COMPANIES)

MATCHED_COUNT = 300     # 300 entities appear in BOTH systems
ERP_ONLY_COUNT = 100    # 100 appear only in ERP
PROC_ONLY_COUNT = 100   # 100 appear only in Procurement

matched_seeds    = SEED_COMPANIES[:MATCHED_COUNT]
erp_only_seeds   = SEED_COMPANIES[MATCHED_COUNT:MATCHED_COUNT+ERP_ONLY_COUNT]
proc_only_seeds  = SEED_COMPANIES[MATCHED_COUNT+ERP_ONLY_COUNT:MATCHED_COUNT+ERP_ONLY_COUNT+PROC_ONLY_COUNT]

# Ground truth: matched pairs get explicit ERP+PROC IDs
ground_truth = []
erp_records  = []
proc_records = []

# --- Matched entities ---
for i, company in enumerate(matched_seeds):
    erp_id   = f"ERP{i+1:05d}"
    proc_id  = f"PROC{i+1:05d}"
    city     = random.choice(CITIES)

    # ERP record
    erp_records.append({
        "vendor_id":    erp_id,
        "vendor_name":  corrupt_erp(company),
        "tax_id":       random_tax_id() if random.random() > 0.08 else None,
        "city":         city,
        "phone":        random_phone() if random.random() > 0.2 else None,
        "last_updated": random_date(60, 730),
        "source_system": "ERP"
    })

    # Proc record — same city, different corruption
    proc_records.append({
        "supplier_id":   proc_id,
        "supplier_name": corrupt_proc(company),
        "tax_id":        random_tax_id() if random.random() > 0.45 else None,
        "city":          city,
        "email":         f"ap@{company.lower().replace(' ','').replace('.','')[:12]}.com" if random.random() > 0.35 else None,
        "last_updated":  random_date(0, 90),
        "source_system": "PROCUREMENT"
    })

    ground_truth.append({
        "pair_id":      i+1,
        "erp_id":       erp_id,
        "proc_id":      proc_id,
        "clean_name":   company,
        "match_type":   "genuine_match"
    })

erp_offset  = MATCHED_COUNT
proc_offset = MATCHED_COUNT

# --- ERP-only records ---
for i, company in enumerate(erp_only_seeds):
    erp_records.append({
        "vendor_id":    f"ERP{erp_offset+i+1:05d}",
        "vendor_name":  corrupt_erp(company),
        "tax_id":       random_tax_id() if random.random() > 0.08 else None,
        "city":         random.choice(CITIES),
        "phone":        random_phone() if random.random() > 0.2 else None,
        "last_updated": random_date(60, 730),
        "source_system": "ERP"
    })

# --- Proc-only records ---
for i, company in enumerate(proc_only_seeds):
    proc_records.append({
        "supplier_id":   f"PROC{proc_offset+i+1:05d}",
        "supplier_name": corrupt_proc(company),
        "tax_id":        random_tax_id() if random.random() > 0.45 else None,
        "city":          random.choice(CITIES),
        "email":         f"ap@{company.lower().replace(' ','').replace('.','')[:12]}.com" if random.random() > 0.35 else None,
        "last_updated":  random_date(0, 90),
        "source_system": "PROCUREMENT"
    })

# --- Hard negatives (similar names, genuinely different companies) ---
HARD_NEGATIVES = [
    ("Apex Logistics Corporation",    "Apex Logistic Systems LLC"),
    ("Global Packaging Solutions Inc","Global Package Services Inc"),
    ("Summit Construction Group",     "Summit Constructors LLC"),
    ("Delta Industrial Supply Co",    "Delta Industries Supply LLC"),
    ("United Metals Corporation",     "United Metal Works Corp"),
]

hn_erp_start  = len(erp_records)
hn_proc_start = len(proc_records)

for j, (name_a, name_b) in enumerate(HARD_NEGATIVES):
    hn_erp_id  = f"ERP_HN{j+1:03d}"
    hn_proc_id = f"PROC_HN{j+1:03d}"

    erp_records.append({
        "vendor_id":    hn_erp_id,
        "vendor_name":  name_a,
        "tax_id":       random_tax_id(),
        "city":         random.choice(CITIES),
        "phone":        random_phone(),
        "last_updated": random_date(30, 200),
        "source_system": "ERP"
    })
    proc_records.append({
        "supplier_id":   hn_proc_id,
        "supplier_name": name_b,
        "tax_id":        random_tax_id(),
        "city":          random.choice(CITIES),
        "email":         None,
        "last_updated":  random_date(0, 60),
        "source_system": "PROCUREMENT"
    })
    ground_truth.append({
        "pair_id":    MATCHED_COUNT + j + 1,
        "erp_id":     hn_erp_id,
        "proc_id":    hn_proc_id,
        "clean_name": f"{name_a} vs {name_b}",
        "match_type": "hard_negative"
    })

print(f"✓ Generated {len(ground_truth)} ground truth pairs")
print(f"  - Genuine matches: {sum(1 for p in ground_truth if p['match_type']=='genuine_match')}")
print(f"  - Hard negatives:  {sum(1 for p in ground_truth if p['match_type']=='hard_negative')}")

print(f"\n[3/5] Creating divergent source records...")
print(f"✓ ERP records:          {len(erp_records)}")
print(f"✓ Procurement records:  {len(proc_records)}")

# ---- Write CSVs ----
print("\n[4/5] Writing CSV files...")

with open("data/erp_vendor_master.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=list(erp_records[0].keys()))
    writer.writeheader(); writer.writerows(erp_records)
print(f"  ✓ data/erp_vendor_master.csv  ({len(erp_records)} rows)")

with open("data/proc_supplier_export.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=list(proc_records[0].keys()))
    writer.writeheader(); writer.writerows(proc_records)
print(f"  ✓ data/proc_supplier_export.csv ({len(proc_records)} rows)")

with open("data/match_truth.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=list(ground_truth[0].keys()))
    writer.writeheader(); writer.writerows(ground_truth)
print(f"  ✓ data/match_truth.csv          ({len(ground_truth)} rows)")

print("\n[5/5] Generation complete!")
print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)
print(f"ERP Vendor Master:       {len(erp_records)} records")
print(f"  - With tax ID:         {sum(1 for r in erp_records if r['tax_id'])}")
print(f"  - With phone:          {sum(1 for r in erp_records if r['phone'])}")
print(f"\nProcurement Export:      {len(proc_records)} records")
print(f"  - With tax ID:         {sum(1 for r in proc_records if r['tax_id'])}")
print(f"  - With email:          {sum(1 for r in proc_records if r['email'])}")
print(f"\nGround Truth:            {len(ground_truth)} pairs")
print(f"  - Genuine matches:     {sum(1 for p in ground_truth if p['match_type']=='genuine_match')}")
print(f"  - Hard negatives:      {sum(1 for p in ground_truth if p['match_type']=='hard_negative')}")
print("\nNext step: python load_raw.py")
print("=" * 60)
