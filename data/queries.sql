-- =============================================================
-- RoadWatch — Useful Queries
-- =============================================================

-- 1. All roads with type & division names (handy view)
-- -------------------------------------------------------------
CREATE OR REPLACE VIEW v_roads AS
SELECT
    r.sl_no,
    r.road_id,
    r.road_name,
    rt.code                         AS road_type,
    r.road_ref,
    r.length_km,
    bd.name                         AS bbmp_division,
    r.contractor_name,
    r.executive_engineer,
    r.completion_date,
    r.dlp_period,
    r.dlp_expiry_date,
    r.budget_sanctioned,
    r.budget_released,
    r.budget_spent,
    r.budget_unspent,
    ROUND(r.budget_spent * 100.0 / NULLIF(r.budget_sanctioned, 0), 1) AS pct_spent,
    r.health_score,
    r.last_complaint_date,
    r.open_complaints,
    r.geometry
FROM roads r
JOIN road_types rt    ON rt.id = r.road_type_id
JOIN bbmp_divisions bd ON bd.id = r.bbmp_division_id;


-- 2. Roads with poor health (score < 50)
-- -------------------------------------------------------------
SELECT road_id, road_name, bbmp_division_id, health_score
FROM roads
WHERE health_score < 50
ORDER BY health_score;


-- 3. Roads whose DLP has expired (potential accountability window)
-- -------------------------------------------------------------
SELECT road_id, road_name, dlp_expiry_date, open_complaints
FROM v_roads
WHERE dlp_expiry_date < CURRENT_DATE
ORDER BY dlp_expiry_date;


-- 4. Budget utilisation by BBMP division
-- -------------------------------------------------------------
SELECT
    bd.name                                                 AS division,
    COUNT(*)                                                AS road_count,
    SUM(r.budget_sanctioned)                                AS total_sanctioned,
    SUM(r.budget_spent)                                     AS total_spent,
    ROUND(SUM(r.budget_spent) * 100.0 /
          NULLIF(SUM(r.budget_sanctioned), 0), 1)           AS pct_utilised,
    SUM(r.budget_unspent)                                   AS unspent
FROM roads r
JOIN bbmp_divisions bd ON bd.id = r.bbmp_division_id
GROUP BY bd.name
ORDER BY pct_utilised DESC;


-- 5. Contractors with most open complaints
-- -------------------------------------------------------------
SELECT
    contractor_name,
    COUNT(*)                    AS road_count,
    SUM(open_complaints)        AS total_open_complaints,
    AVG(health_score)::NUMERIC(5,1) AS avg_health
FROM roads
GROUP BY contractor_name
ORDER BY total_open_complaints DESC;


-- 6. Roads with open complaints, ordered by severity
-- -------------------------------------------------------------
SELECT road_id, road_name, open_complaints, health_score, last_complaint_date
FROM roads
WHERE open_complaints > 0
ORDER BY open_complaints DESC, health_score ASC;


-- 7. Summary stats per road type
-- -------------------------------------------------------------
SELECT
    rt.code                          AS road_type,
    COUNT(*)                         AS count,
    ROUND(AVG(r.length_km), 2)       AS avg_length_km,
    ROUND(AVG(r.health_score), 1)    AS avg_health,
    SUM(r.open_complaints)           AS total_open_complaints
FROM roads r
JOIN road_types rt ON rt.id = r.road_type_id
GROUP BY rt.code
ORDER BY rt.code;


-- 8. Roads nearing or past DLP expiry with low health scores
-- (priority maintenance candidates)
-- -------------------------------------------------------------
SELECT road_id, road_name, health_score, dlp_expiry_date, open_complaints
FROM v_roads
WHERE dlp_expiry_date <= CURRENT_DATE + INTERVAL '6 months'
  AND health_score < 60
ORDER BY health_score ASC;
