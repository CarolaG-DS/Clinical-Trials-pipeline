-- ============================================================
-- 01_staging.sql
-- Aim: Clean and Normalize Raw Data from AACT 
-- Skills: CTE, window functions, CASE, date handling, dedup
-- ============================================================


-- ── 1. Data Deduplication (identify and remove duplicates) ──────────────────────────────────
-- Deduplication keeps only one version (usually the most complete one), eliminating the "noise" that could distort the statistics.
-- PARTITION by nct_id: The database virtually groups all rows with the same ID (nct_id).
-- ORDER BY enrollment DESC: Within each group of duplicates, the database places the row with the highest number of participants (enrollment) at the top. The idea is to keep the one with more data."
-- ROW_NUMBER(): Assigns a number (1, 2, 3, etc.) to each row in the group. The "best" row receives a 1.
-- WHERE rn = 1: Finally, the script saves only the rows with a 1, discarding all others.


CREATE TABLE IF NOT EXISTS stg_studies AS
WITH deduped AS (
    SELECT *, 
           ROW_NUMBER() OVER (
               PARTITION BY nct_id
               ORDER BY enrollment DESC NULLS LAST
           ) AS rn
    FROM studies
)
SELECT
    nct_id,
    brief_title,
    overall_status,

    -- ── 2. NORMALIZATION ─────────────────────────────
    -- Raw values are not consistent, these are written in different way: "Phase 1", "PHASE1", "phase1/2" ecc.
    CASE
        WHEN UPPER(phase) LIKE '%EARLY%'   THEN 'Early Phase 1'
        WHEN UPPER(phase) LIKE '%1/2%'     THEN 'Phase 1/2'
        WHEN UPPER(phase) LIKE '%2/3%'     THEN 'Phase 2/3'
        WHEN UPPER(phase) LIKE '%1%'       THEN 'Phase 1'
        WHEN UPPER(phase) LIKE '%2%'       THEN 'Phase 2'
        WHEN UPPER(phase) LIKE '%3%'       THEN 'Phase 3'
        WHEN UPPER(phase) LIKE '%4%'       THEN 'Phase 4'
        WHEN UPPER(phase) = 'N/A'          THEN 'N/A'
        ELSE 'Unknown'
    END AS phase_clean,

    -- ── 3. DATE HANDLING ────────────────────────────────────
    -- date are reported as string str 'YYYY-MM-DD' o 'Month YYYY'
    CASE
        WHEN LENGTH(start_date) = 10 THEN DATE(start_date)
        WHEN LENGTH(start_date) = 7  THEN DATE(start_date || '-01')
        ELSE NULL
    END AS start_date_clean,

    CASE
        WHEN LENGTH(completion_date) = 10 THEN DATE(completion_date)
        WHEN LENGTH(completion_date) = 7  THEN DATE(completion_date || '-01')
        ELSE NULL
    END AS completion_date_clean,

    -- ── 4. Calculation of the LENGHT of the study ──────────────────────────────────
    CAST(
        JULIANDAY(
            CASE WHEN LENGTH(completion_date)=10 THEN completion_date
                 WHEN LENGTH(completion_date)=7  THEN completion_date||'-01'
            END
        ) -
        JULIANDAY(
            CASE WHEN LENGTH(start_date)=10 THEN start_date
                 WHEN LENGTH(start_date)=7  THEN start_date||'-01'
            END
        ) AS INTEGER
    ) / 30 AS duration_months,

    -- ── 5. STATUS BUCKET / SEMPLIFICATION OF TERMS ────────────────────────────────────
    CASE
        WHEN overall_status IN ('COMPLETED', 'Completed')                                    THEN 'Completed'
        WHEN overall_status IN ('RECRUITING', 'NOT_YET_RECRUITING', 'ENROLLING_BY_INVITATION',
                                'ACTIVE_NOT_RECRUITING',
                                'Recruiting','Not yet recruiting','Enrolling by invitation') THEN 'Active'
        WHEN overall_status IN ('TERMINATED','WITHDRAWN','SUSPENDED',
                                'Terminated','Withdrawn','Suspended')                        THEN 'Stopped'
        ELSE 'Other'
    END AS status_bucket,

    COALESCE(CAST(enrollment AS INTEGER), 0) AS enrollment_clean

FROM deduped
WHERE rn = 1;


-- ── 6. STAGING CONDITIONS (with frequency ranking) ──────────
-- This code block moves from the studies table to the pathologies table (the "conditions"). 
-- Here, the goal is to understand which diseases are the most studied and create a ranking.
CREATE TABLE IF NOT EXISTS stg_conditions AS
WITH condition_counts AS (
    SELECT
        LOWER(TRIM(condition)) AS condition_norm, -- ← fix: 'name' → 'condition'
        COUNT(DISTINCT nct_id) AS trial_count
    FROM conditions
    GROUP BY LOWER(TRIM(condition))
),
ranked AS (
    SELECT *,
           RANK() OVER (ORDER BY trial_count DESC) AS freq_rank
    FROM condition_counts
)
SELECT
    c.nct_id,
    LOWER(TRIM(c.condition)) AS condition_norm, -- ← fix: 'name' → 'condition'
    r.trial_count,
    r.freq_rank
FROM conditions c
JOIN ranked r ON LOWER(TRIM(c.condition)) = r.condition_norm; -- ← fix: 'name' → 'condition'


-- ── 7. STAGING SPONSORS (lead sponsor only + rank) ──────────
-- This block helps us understand who the main players in clinical research are (pharmaceutical companies, universities, or hospitals) 
-- it creates a ranking based on the number of studies they manage.
CREATE TABLE IF NOT EXISTS stg_sponsors AS
WITH lead_only AS (
    SELECT nct_id, sponsor AS sponsor_name -- ← fix: 'name' → 'sponsor'
    FROM sponsors
    WHERE LOWER(lead_or_collaborator) = 'lead'
),
sponsor_volume AS (
    SELECT
        sponsor_name,
        COUNT(DISTINCT nct_id) AS trials_led,
        RANK() OVER (ORDER BY COUNT(DISTINCT nct_id) DESC) AS sponsor_rank
    FROM lead_only
    GROUP BY sponsor_name
)
SELECT
    l.nct_id,
    l.sponsor_name,
    sv.trials_led,
    sv.sponsor_rank
FROM lead_only l
JOIN sponsor_volume sv USING (sponsor_name);


-- ── 8. STAGING COUNTRIES ──────────────────
-- here we map where clinical trials are being conducted in the world. 
CREATE TABLE IF NOT EXISTS stg_countries AS
SELECT
    nct_id,
    TRIM(country) AS country, -- ← fix: 'name' → 'country'
    COUNT(*) OVER (PARTITION BY TRIM(country)) AS country_trial_count
FROM countries
WHERE LOWER(removed) != 'true'
  AND country IS NOT NULL; -- ← fix: 'name' → 'country'