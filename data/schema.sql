-- =============================================================
-- RoadWatch — PostgreSQL Schema
-- Table: roads
-- Source: bengaluru_roads_master.csv  (952 rows, 26 columns)
-- =============================================================

-- Enable PostGIS if you want native geometry support (optional).
-- If PostGIS is not available, geometry is stored as TEXT (WKT).
-- Uncomment the line below when PostGIS is installed:
-- CREATE EXTENSION IF NOT EXISTS postgis;

-- -------------------------------------------------------------
-- Lookup / reference tables  (normalise repeated strings)
-- -------------------------------------------------------------

CREATE TABLE road_types (
    id      SERIAL PRIMARY KEY,
    code    VARCHAR(10)  NOT NULL UNIQUE   -- 'NH', 'SH', 'MDR'
);

INSERT INTO road_types (code) VALUES ('NH'), ('SH'), ('MDR');

CREATE TABLE bbmp_divisions (
    id   SERIAL PRIMARY KEY,
    name VARCHAR(60) NOT NULL UNIQUE
);

INSERT INTO bbmp_divisions (name) VALUES
    ('West'), ('East'), ('Yelahanka'), ('RR Nagar'),
    ('South'), ('Dasarahalli'), ('Mahadevapura'), ('Bommanahalli');

-- -------------------------------------------------------------
-- Main roads table
-- -------------------------------------------------------------

CREATE TABLE roads (
    -- identity
    sl_no               INTEGER         PRIMARY KEY,
    road_id             VARCHAR(60)     NOT NULL UNIQUE,
    osm_id              TEXT,                           -- nullable (388 missing)

    -- road details
    road_name           VARCHAR(200)    NOT NULL,
    road_type_id        INTEGER         NOT NULL REFERENCES road_types(id),
    road_ref            VARCHAR(20),                    -- nullable (900 missing)
    length_km           NUMERIC(8,3)    NOT NULL,
    bbmp_division_id    INTEGER         NOT NULL REFERENCES bbmp_divisions(id),

    -- administration
    contractor_name     VARCHAR(150)    NOT NULL,
    executive_engineer  VARCHAR(100)    NOT NULL,
    ee_contact          BIGINT,                         -- nullable (24 missing)
    asst_exec_engineer  VARCHAR(100),                   -- nullable (8 missing)
    aee_contact         BIGINT,                         -- nullable (62 missing)
    asst_engineer       VARCHAR(100),                   -- nullable (2 missing)
    ae_contact          BIGINT,                         -- nullable (88 missing)

    -- dates & DLP
    completion_date     DATE            NOT NULL,
    dlp_period          VARCHAR(20)     NOT NULL,       -- '3 Years', '5 Years'
    dlp_expiry_date     DATE            NOT NULL,

    -- budget (in INR)
    budget_sanctioned   BIGINT          NOT NULL,
    budget_released     BIGINT          NOT NULL,
    budget_spent        BIGINT          NOT NULL,
    budget_unspent      BIGINT          NOT NULL,

    -- condition & complaints
    health_score        SMALLINT        NOT NULL CHECK (health_score BETWEEN 0 AND 100),
    last_complaint_date DATE            NOT NULL,
    open_complaints     INTEGER         NOT NULL DEFAULT 0,

    -- geometry (WKT LineString — use geometry type if PostGIS is enabled)
    geometry            TEXT                            -- nullable (388 missing)
    -- With PostGIS: geometry GEOMETRY(LINESTRING, 4326)
);

-- -------------------------------------------------------------
-- Indexes  (commonly queried / filtered columns)
-- -------------------------------------------------------------

CREATE INDEX idx_roads_type        ON roads (road_type_id);
CREATE INDEX idx_roads_division    ON roads (bbmp_division_id);
CREATE INDEX idx_roads_health      ON roads (health_score);
CREATE INDEX idx_roads_complaints  ON roads (open_complaints);
CREATE INDEX idx_roads_contractor  ON roads (contractor_name);
CREATE INDEX idx_roads_dlp_expiry  ON roads (dlp_expiry_date);

-- With PostGIS, replace the TEXT geometry column and use:
-- CREATE INDEX idx_roads_geom ON roads USING GIST (geometry);
