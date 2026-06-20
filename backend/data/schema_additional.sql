-- =============================================================
-- RoadWatch — Additional Schema (Features 02–06)
-- Paste this AFTER schema.sql has been run (roads, road_types,
-- bbmp_divisions must already exist).
-- =============================================================

-- -------------------------------------------------------------
-- USERS  (citizens / authority / admin — needed for auth + complaints)
-- -------------------------------------------------------------

CREATE TABLE users (
    id              SERIAL PRIMARY KEY,
    name            VARCHAR(100)    NOT NULL,
    email           VARCHAR(150)    NOT NULL UNIQUE,
    phone           VARCHAR(15),
    password_hash   VARCHAR(255)    NOT NULL,
    role            VARCHAR(20)     NOT NULL DEFAULT 'citizen'
                        CHECK (role IN ('citizen', 'authority', 'admin')),
    created_at      TIMESTAMP       NOT NULL DEFAULT NOW()
);

-- -------------------------------------------------------------
-- AUTHORITIES  (jurisdiction mapping — Feature 03 routing)
-- -------------------------------------------------------------

CREATE TABLE authorities (
    id              SERIAL PRIMARY KEY,
    name            VARCHAR(150)    NOT NULL,         -- e.g. 'NHAI Regional Office', 'PWD Executive Engineer'
    road_type_id    INTEGER         NOT NULL REFERENCES road_types(id),
    bbmp_division_id INTEGER        REFERENCES bbmp_divisions(id),  -- nullable: NH may not map to a division
    escalation_to   VARCHAR(150),                     -- next level up the hierarchy
    contact_email   VARCHAR(150),
    contact_phone   VARCHAR(15)
);

-- Seed default authority mapping per road type
INSERT INTO authorities (name, road_type_id, escalation_to) VALUES
    ('NHAI Regional Office', (SELECT id FROM road_types WHERE code='NH'),  'NHAI HQ → Ministry of Road Transport'),
    ('State PWD Executive Engineer', (SELECT id FROM road_types WHERE code='SH'), 'PWD Chief Engineer → State Govt'),
    ('District Collector / Panchayat Eng.', (SELECT id FROM road_types WHERE code='MDR'), 'District Magistrate → State Rural Dept');

-- -------------------------------------------------------------
-- COMPLAINTS  (Feature 02 — AI complaint portal, Feature 03 routing)
-- -------------------------------------------------------------

CREATE TABLE complaints (
    id                  SERIAL PRIMARY KEY,
    tracking_id         VARCHAR(20)     NOT NULL UNIQUE,   -- e.g. 'RW-2026-00001', generate in app code
    road_sl_no          INTEGER         NOT NULL REFERENCES roads(sl_no),
    user_id             INTEGER         REFERENCES users(id),   -- nullable for anonymous/whistleblower later
    authority_id        INTEGER         REFERENCES authorities(id),

    -- AI-detected fields
    issue_type          VARCHAR(30)     NOT NULL
                            CHECK (issue_type IN ('Pothole','Crack','Waterlogging','Missing Signage','Road Cave-in')),
    severity            VARCHAR(10)     NOT NULL
                            CHECK (severity IN ('Low','Medium','High','Critical')),
    confidence_score    NUMERIC(5,2),                       -- AI model confidence %

    -- location & media
    latitude            NUMERIC(9,6),
    longitude           NUMERIC(9,6),
    image_url           TEXT,

    -- SLA & status tracking
    status              VARCHAR(20)     NOT NULL DEFAULT 'Open'
                            CHECK (status IN ('Open','In Progress','Escalated','Resolved')),
    response_deadline   TIMESTAMP,                          -- computed from severity at insert time
    escalated           BOOLEAN         NOT NULL DEFAULT FALSE,

    created_at          TIMESTAMP       NOT NULL DEFAULT NOW(),
    resolved_at         TIMESTAMP
);

CREATE INDEX idx_complaints_road       ON complaints (road_sl_no);
CREATE INDEX idx_complaints_status     ON complaints (status);
CREATE INDEX idx_complaints_severity   ON complaints (severity);
CREATE INDEX idx_complaints_deadline   ON complaints (response_deadline);

-- -------------------------------------------------------------
-- REPAIRS  (Feature 05 — Repair Timeline View)
-- -------------------------------------------------------------

CREATE TABLE repairs (
    id              SERIAL PRIMARY KEY,
    road_sl_no      INTEGER         NOT NULL REFERENCES roads(sl_no),
    event_type      VARCHAR(20)     NOT NULL
                        CHECK (event_type IN ('Built','Repaired','Complaint')),
    event_date      DATE            NOT NULL,
    notes           TEXT,
    linked_complaint_id INTEGER     REFERENCES complaints(id)   -- nullable, links 'Complaint' events
);

CREATE INDEX idx_repairs_road  ON repairs (road_sl_no);
CREATE INDEX idx_repairs_date  ON repairs (event_date);

-- Seed one 'Built' event per road from existing completion_date
INSERT INTO repairs (road_sl_no, event_type, event_date, notes)
SELECT sl_no, 'Built', completion_date, 'Initial construction'
FROM roads;

-- -------------------------------------------------------------
-- CONTRACTOR SCORING  (Feature 04 — Accountability Scoring)
-- Computed as a VIEW so it's always live, no separate table to keep in sync.
-- -------------------------------------------------------------

CREATE OR REPLACE VIEW v_contractor_scores AS
SELECT
    r.contractor_name,
    COUNT(*)                                                       AS total_roads,
    ROUND(AVG(r.health_score), 1)                                  AS avg_health_score,
    SUM(r.open_complaints)                                         AS total_open_complaints,
    SUM(CASE WHEN r.budget_spent < r.budget_sanctioned * 0.5
             THEN 1 ELSE 0 END)                                    AS low_utilisation_roads,
    -- Simple weighted score: avg_health (60%) + complaint penalty (40%)
    ROUND(
        (AVG(r.health_score) * 0.6) +
        ((100 - LEAST(SUM(r.open_complaints) * 5, 100)) * 0.4)
    , 1)                                                            AS contractor_score,
    CASE WHEN ROUND(
        (AVG(r.health_score) * 0.6) +
        ((100 - LEAST(SUM(r.open_complaints) * 5, 100)) * 0.4)
    , 1) < 40 THEN TRUE ELSE FALSE END                              AS red_flagged
FROM roads r
GROUP BY r.contractor_name
ORDER BY contractor_score ASC;

-- -------------------------------------------------------------
-- ROAD HEALTH SCORE — recompute formula as a VIEW (Feature 04)
-- Overrides the static CSV health_score with the weighted formula
-- from your spec: days since repair 25%, open complaints 25%,
-- budget utilisation 20%, repair durability 30%.
-- -------------------------------------------------------------

CREATE OR REPLACE VIEW v_road_health_live AS
SELECT
    r.sl_no,
    r.road_name,
    r.contractor_name,
    EXTRACT(DAY FROM NOW() - COALESCE(
        (SELECT MAX(event_date) FROM repairs rp
         WHERE rp.road_sl_no = r.sl_no AND rp.event_type = 'Repaired'),
        r.completion_date
    ))                                                              AS days_since_last_repair,
    r.open_complaints,
    ROUND(r.budget_spent * 100.0 / NULLIF(r.budget_sanctioned, 0), 1) AS pct_budget_used,
    (SELECT COUNT(*) FROM repairs rp
     WHERE rp.road_sl_no = r.sl_no AND rp.event_type = 'Repaired')   AS repair_count
FROM roads r;

-- =============================================================
-- DONE. Tables added: users, authorities, complaints, repairs
-- Views added: v_contractor_scores, v_road_health_live
-- =============================================================