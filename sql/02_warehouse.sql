-- ============================================================
-- 02_warehouse.sql
-- We create a Dimension (star scheme): data is divided into two types of tables: Dimensions (descriptions) and Facts (numbers and facts).
-- it's like creating an official dictionary of the diseases in your database
-- Imagine you have 400,000 studies. Instead of typing "Diabetes" 400,000 times (taking up a lot of space), you'll just type the number 10. When you want to know what 10 stands for, you'll look at this dim_conditions table.
-- ============================================================

-- ── DIMENSION: medical conditions──────────────────────────
--Create the final table, call it dim_ (short for Dimension) to indicate that it contains the disease descriptions.
--The staging contained one row for each study, DISTINCT tells the database to take each disease only once as we want a single catalog
-- create a surrogate key, We assign a progressive number to each disease in alphabetical order
-- for each number assigned to a disease, we add its definition,in how many studies it is,it's frequency ranking
CREATE TABLE IF NOT EXISTS dim_conditions AS
SELECT DISTINCT
    ROW_NUMBER() OVER (ORDER BY condition_norm) AS condition_id,
    condition_norm,
    trial_count,
    freq_rank
FROM stg_conditions;

-- ── DIMENSION: sponsor ──────────────────────────────────────
-- we do the same table dictionary but for sponsor
-- assigned each sponsor a number id, name, trial leading and ranking
CREATE TABLE IF NOT EXISTS dim_sponsors AS
SELECT DISTINCT
    ROW_NUMBER() OVER (ORDER BY sponsor_name) AS sponsor_id,
    sponsor_name,
    trials_led,
    sponsor_rank
FROM stg_sponsors;

-- ── DIMENSION: geography ────────────────────────────────────
-- same for countries in which studies are conducted
CREATE TABLE IF NOT EXISTS dim_geography AS
SELECT DISTINCT
    ROW_NUMBER() OVER (ORDER BY country) AS geo_id,
    country,
    country_trial_count
FROM stg_countries;

-- ── DIMENSION: clinical phase ─────────────────────────────────
CREATE TABLE IF NOT EXISTS dim_phase AS
SELECT DISTINCT
    ROW_NUMBER() OVER (ORDER BY phase_clean) AS phase_id,
    phase_clean,
    COUNT(*) OVER (PARTITION BY phase_clean) AS trials_in_phase
FROM stg_studies;

-- ── FACT TABLE ───────────────────────────────────────────────
-- dim_ tables are dictionaries, the Fact Table is the diary where you record everything that happens, using dictionary shortcuts.
-- one row = a clinical trial
-- Contains metrics + FK towards dimensions
CREATE TABLE IF NOT EXISTS fact_trials AS
SELECT
    s.nct_id,
    s.brief_title,
    s.status_bucket,
    s.enrollment_clean,
    s.duration_months,
    s.start_date_clean,
    s.completion_date_clean,
    p.phase_id,
    sp.sponsor_id,
    g.geo_id,
    CASE WHEN s.status_bucket = 'Completed' THEN 1 ELSE 0 END AS is_completed,
    CASE WHEN s.enrollment_clean > 0 THEN 1 ELSE 0 END AS has_enrollment
FROM stg_studies s
LEFT JOIN dim_phase p ON s.phase_clean = p.phase_clean
LEFT JOIN stg_sponsors ss ON s.nct_id = ss.nct_id
LEFT JOIN dim_sponsors sp ON ss.sponsor_name = sp.sponsor_name
LEFT JOIN stg_countries sc ON s.nct_id = sc.nct_id
LEFT JOIN dim_geography g ON sc.country = g.country;




