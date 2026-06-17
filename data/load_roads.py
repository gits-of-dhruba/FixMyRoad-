"""
load_roads.py
=============
Loads bengaluru_roads_master.csv into the RoadWatch PostgreSQL database.

Usage
-----
    pip install psycopg2-binary pandas

    python load_roads.py \
        --csv  bengaluru_roads_master.csv \
        --host localhost \
        --port 5432 \
        --db   roadwatch \
        --user postgres \
        --password yourpassword

    # Or export PGPASSWORD and omit --password.

The script:
  1. Validates / cleans the CSV.
  2. Resolves foreign keys (road_types, bbmp_divisions).
  3. Bulk-inserts into roads with ON CONFLICT DO NOTHING (idempotent).
  4. Prints a summary row count on success.
"""

import argparse
import re
import sys

import pandas as pd
import psycopg2
import psycopg2.extras


# ---------------------------------------------------------------------------
# CLI args
# ---------------------------------------------------------------------------

def parse_args():
    p = argparse.ArgumentParser(description="Load roads CSV into PostgreSQL")
    p.add_argument("--csv",      default="bengaluru_roads_master.csv")
    p.add_argument("--host",     default="localhost")
    p.add_argument("--port",     type=int, default=5432)
    p.add_argument("--db",       default="roadwatch")
    p.add_argument("--user",     default="postgres")
    p.add_argument("--password", default="1234")
    return p.parse_args()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def parse_date(val):
    """Parse DD.MM.YYYY → YYYY-MM-DD string, or return None.

    Validates the result is a real calendar date (e.g. catches
    29 Feb on a non-leap year) and falls back to the nearest valid
    day rather than crashing the whole load on dirty source data.
    """
    import datetime

    if pd.isna(val) or str(val).strip() == "":
        return None
    val = str(val).strip()

    # Try DD.MM.YYYY
    m = re.match(r"^(\d{2})\.(\d{2})\.(\d{4})$", val)
    if m:
        d, mo, y = (int(x) for x in m.groups())
    else:
        # Try YYYY-MM-DD (already ISO)
        m = re.match(r"^(\d{4})-(\d{2})-(\d{2})$", val)
        if m:
            y, mo, d = (int(x) for x in m.groups())
        else:
            raise ValueError(f"Unrecognised date format: {val!r}")

    try:
        return datetime.date(y, mo, d).isoformat()
    except ValueError:
        # Invalid calendar date (e.g. 2014-02-29). Roll back one day
        # at a time until we hit a valid date in the same month.
        for fallback_day in range(d - 1, 0, -1):
            try:
                fixed = datetime.date(y, mo, fallback_day)
                print(f"  ⚠ Invalid date {val!r} → corrected to {fixed.isoformat()}")
                return fixed.isoformat()
            except ValueError:
                continue
        raise ValueError(f"Could not repair invalid date: {val!r}")


def normalise_dlp(val):
    """Normalise '3 years' / '3 Years' → '3 Years'."""
    if pd.isna(val):
        return None
    parts = str(val).strip().split()
    if len(parts) == 2:
        return f"{parts[0]} {parts[1].capitalize()}"
    return str(val).strip()


def nullable_int(val):
    """Convert NaN / float to None or int."""
    if pd.isna(val):
        return None
    return int(val)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    args = parse_args()

    # --- 1. Load CSV ---
    print(f"Reading {args.csv} …")
    df = pd.read_csv(args.csv, dtype=str)   # read everything as str first

    # --- 2. Clean ---
    df["length_km"]         = pd.to_numeric(df["length_km"],         errors="coerce")
    df["budget_sanctioned"] = pd.to_numeric(df["budget_sanctioned"], errors="coerce")
    df["budget_released"]   = pd.to_numeric(df["budget_released"],   errors="coerce")
    df["budget_spent"]      = pd.to_numeric(df["budget_spent"],      errors="coerce")
    df["budget_unspent"]    = pd.to_numeric(df["budget_unspent"],     errors="coerce")
    df["health_score"]      = pd.to_numeric(df["health_score"],       errors="coerce")
    df["open_complaints"]   = pd.to_numeric(df["open_complaints"],    errors="coerce")
    df["sl_no"]             = pd.to_numeric(df["sl_no"],              errors="coerce")
    df["dlp_period"]        = df["dlp_period"].apply(normalise_dlp)

    print(f"  Loaded {len(df):,} rows, {len(df.columns)} columns.")

    # --- 3. Connect ---
    print(f"Connecting to PostgreSQL {args.host}:{args.port}/{args.db} …")
    conn = psycopg2.connect(
        host=args.host,
        port=args.port,
        dbname=args.db,
        user=args.user,
        password=args.password,
    )
    conn.autocommit = False
    cur = conn.cursor()

    # --- 4. Resolve foreign keys ---
    cur.execute("SELECT id, code FROM road_types")
    road_type_map = {row[1]: row[0] for row in cur.fetchall()}

    cur.execute("SELECT id, name FROM bbmp_divisions")
    division_map = {row[1]: row[0] for row in cur.fetchall()}

    # --- 5. Build rows ---
    rows = []
    errors = []

    for i, r in df.iterrows():
        row_num = i + 2  # 1-indexed, header is row 1
        try:
            road_type_id  = road_type_map[r["road_type"].strip()]
            division_id   = division_map[r["bbmp_division"].strip()]
            comp_date     = parse_date(r.get("completion_date"))
            dlp_exp_date  = parse_date(r.get("dlp_expiry_date"))
            last_complaint = parse_date(r.get("last_complaint_date"))

            rows.append((
                int(r["sl_no"]),
                r["road_id"].strip(),
                r["osm_id"] if pd.notna(r.get("osm_id")) else None,
                r["road_name"].strip(),
                road_type_id,
                r["road_ref"] if pd.notna(r.get("road_ref")) else None,
                float(r["length_km"]),
                division_id,
                r["contractor_name"].strip(),
                r["executive_engineer"].strip(),
                nullable_int(r.get("ee_contact")),
                r["asst_exec_engineer"] if pd.notna(r.get("asst_exec_engineer")) else None,
                nullable_int(r.get("aee_contact")),
                r["asst_engineer"] if pd.notna(r.get("asst_engineer")) else None,
                nullable_int(r.get("ae_contact")),
                comp_date,
                normalise_dlp(r.get("dlp_period")),
                dlp_exp_date,
                int(r["budget_sanctioned"]),
                int(r["budget_released"]),
                int(r["budget_spent"]),
                int(r["budget_unspent"]),
                int(r["health_score"]),
                last_complaint,
                int(r["open_complaints"]),
                r["geometry"] if pd.notna(r.get("geometry")) else None,
            ))
        except Exception as e:
            errors.append(f"  Row {row_num} skipped — {e}")

    if errors:
        print(f"\n⚠  {len(errors)} rows had errors and were skipped:")
        for err in errors[:10]:
            print(err)
        if len(errors) > 10:
            print(f"  … and {len(errors)-10} more.")

    # --- 6. Insert ---
    INSERT_SQL = """
        INSERT INTO roads (
            sl_no, road_id, osm_id,
            road_name, road_type_id, road_ref, length_km, bbmp_division_id,
            contractor_name, executive_engineer, ee_contact,
            asst_exec_engineer, aee_contact, asst_engineer, ae_contact,
            completion_date, dlp_period, dlp_expiry_date,
            budget_sanctioned, budget_released, budget_spent, budget_unspent,
            health_score, last_complaint_date, open_complaints,
            geometry
        )
        VALUES %s
        ON CONFLICT (sl_no) DO UPDATE SET
            road_id = EXCLUDED.road_id,
            road_name = EXCLUDED.road_name,
            health_score = EXCLUDED.health_score,
            open_complaints = EXCLUDED.open_complaints,
            budget_spent = EXCLUDED.budget_spent,
            budget_unspent = EXCLUDED.budget_unspent
    """

    print(f"\nInserting {len(rows):,} rows …")
    psycopg2.extras.execute_values(cur, INSERT_SQL, rows, page_size=200)
    conn.commit()

    cur.execute("SELECT COUNT(*) FROM roads")
    total = cur.fetchone()[0]
    print(f"✓ Done. roads table now has {total:,} rows.")

    cur.close()
    conn.close()


if __name__ == "__main__":
    main()