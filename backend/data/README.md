# Database

PostgreSQL database for RoadWatch's road metadata — stores road details, contractor/engineer info, DLP (Defect Liability Period) tracking, budget utilisation, and complaint/health data for roads across Bengaluru's BBMP divisions.

## Structure

```
backend/data/
├── schema.sql        # Table definitions, lookup tables, indexes
├── load_roads.py      # CSV → PostgreSQL loader script
├── queries.sql        # Reference queries (health, budget, complaints, DLP)
└── bengaluru_roads_master.csv   # Source data (952 roads, 26 columns)
```

## Schema Overview

- **`roads`** — main table, one row per road (`sl_no` as primary key)
- **`road_types`** — lookup table (NH, SH, MDR)
- **`bbmp_divisions`** — lookup table (West, East, Yelahanka, etc.)
- **`v_roads`** — view joining the above for convenient querying

Key fields: road name/type/length, contractor and engineer contacts, completion date, DLP period and expiry, budget (sanctioned/released/spent/unspent), health score, complaint counts, and road geometry (WKT LineString).

## Setup

### 1. Install PostgreSQL
Download from [postgresql.org/download](https://www.postgresql.org/download/) and complete the installer, noting the password you set for the `postgres` user.

### 2. Create the database
```bash
psql -U postgres
```
```sql
CREATE DATABASE roadwatch;
\q
```

### 3. Apply the schema
```bash
psql -U postgres -d roadwatch -f backend/data/schema.sql
```

### 4. Load the data
```bash
pip install psycopg2-binary pandas
python backend/data/load_roads.py --db roadwatch --user postgres --password yourpassword
```

### 5. Verify
```bash
psql -U postgres -d roadwatch
```
```sql
SELECT COUNT(*) FROM roads;   -- should return 952
```

## Loader Notes

`load_roads.py` cleans known data quality issues in the source CSV automatically:
- Normalises mixed-case DLP periods (`3 years` → `3 Years`)
- Parses `DD.MM.YYYY` dates into ISO format
- Auto-corrects invalid calendar dates (e.g. `29.02.2014`, a non-leap year) by rolling back to the nearest valid day, with a printed warning
- Handles nullable fields (contact numbers, `osm_id`, `geometry`, `road_ref`)
- Upserts on `sl_no` conflict, so the script can be safely re-run

Run with stdout redirected to a log file to review any warnings:
```bash
python backend/data/load_roads.py --db roadwatch --user postgres --password yourpassword > load.log 2>&1
```

## Common Queries

See `queries.sql` for ready-to-use queries, including:
- Roads with low health scores
- Roads past DLP expiry
- Budget utilisation by division
- Contractors with the most open complaints
- Priority maintenance candidates (low health + expiring DLP)

## Connecting from the App

Backend services connect using `DATABASE_URL` in `backend/.env`:

```
DATABASE_URL=postgresql://postgres:yourpassword@localhost:5432/roadwatch
```
