#LOAD 
import os
import pandas as pd
from sqlalchemy import create_engine, text


def load_raw_to_db(raw_dir="data/raw", db_path="data/clinical_trials.db"): #move data from parquet to db
    os.makedirs("data", exist_ok=True) #makes sure there's a folder named data
    engine = create_engine(f"sqlite:///{db_path}") #creates a sqlite db (a single file in my computer)
    tables = ["studies", "conditions", "sponsors", "outcomes", "countries"] # a list that contains the name of files we downloaded before 
    for t in tables:
        df = pd.read_parquet(f"{raw_dir}/{t}.parquet") #Read Parquet file that was created before 
        df.to_sql(t, engine, if_exists="replace", index=False) #takes data and write it into sql. if it exists already, it will create again from 0
        print(f"  → {t}: {len(df):,} righe caricate")
    return engine

def run_staging(db_path="data/clinical_trials.db"):
    engine = create_engine(f"sqlite:///{db_path}")
    with open("sql/01_staging.sql") as f:
        sql = f.read()
    # rimuovi i commenti e splitta
    statements = []
    for s in sql.split(";"):
        s = s.strip()
        # rimuovi righe che iniziano con --
        lines = [l for l in s.splitlines() if not l.strip().startswith("--")]
        s = "\n".join(lines).strip()
        if s:
            statements.append(s)
    with engine.connect() as conn:
        for i, stmt in enumerate(statements):
            try:
                conn.execute(text(stmt))
                print(f"  ✓ statement {i+1} eseguito")
            except Exception as e:
                print(f"  ✗ statement {i+1} ERRORE: {e}")
        conn.commit()
    print("Staging completato.")

if __name__ == "__main__":
    load_raw_to_db()
    run_staging()




