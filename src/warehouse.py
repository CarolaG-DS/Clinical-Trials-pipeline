from sqlalchemy import create_engine, text

def build_warehouse(db_path="data/clinical_trials.db"):
    engine = create_engine(f"sqlite:///{db_path}")
    
    with engine.connect() as conn:
        # Dimensioni
        stmts = [
            "CREATE TABLE IF NOT EXISTS dim_phase AS SELECT DISTINCT ROW_NUMBER() OVER (ORDER BY phase_clean) AS phase_id, phase_clean, COUNT(*) OVER (PARTITION BY phase_clean) AS trials_in_phase FROM stg_studies",
            "CREATE TABLE IF NOT EXISTS dim_sponsors AS SELECT DISTINCT ROW_NUMBER() OVER (ORDER BY sponsor_name) AS sponsor_id, sponsor_name, trials_led, sponsor_rank FROM stg_sponsors",
            "CREATE TABLE IF NOT EXISTS dim_geography AS SELECT DISTINCT ROW_NUMBER() OVER (ORDER BY country) AS geo_id, country, country_trial_count FROM stg_countries",
            "CREATE TABLE IF NOT EXISTS dim_conditions AS SELECT DISTINCT ROW_NUMBER() OVER (ORDER BY condition_norm) AS condition_id, condition_norm, trial_count, freq_rank FROM stg_conditions",
        ]
        for i, stmt in enumerate(stmts):
            try:
                conn.execute(text(stmt))
                print(f"  ✓ dim table {i+1} creata")
            except Exception as e:
                print(f"  ✗ ERRORE: {e}")
        conn.commit()

    # fact_trials: una riga per studio, niente moltiplicazioni
    print("  Costruendo fact_trials...")
    with engine.connect() as conn:
        conn.execute(text("DROP TABLE IF EXISTS fact_trials"))
        conn.execute(text("""
            CREATE TABLE fact_trials AS
            SELECT
                s.nct_id,
                s.brief_title,
                s.status_bucket,
                s.enrollment_clean,
                s.duration_months,
                s.start_date_clean,
                s.completion_date_clean,
                p.phase_id,
                p.phase_clean,
                CASE WHEN s.status_bucket = 'Completed' THEN 1 ELSE 0 END AS is_completed,
                CASE WHEN s.enrollment_clean > 0 THEN 1 ELSE 0 END AS has_enrollment
            FROM stg_studies s
            LEFT JOIN dim_phase p ON s.phase_clean = p.phase_clean
        """))
        conn.commit()
    print("  ✓ fact_trials creata")
    print("Warehouse completato.")

if __name__ == "__main__":
    build_warehouse()