import os
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv("AACT_credenziali.env")

AACT_HOST = "aact-db.ctti-clinicaltrials.org"
AACT_PORT = 5432
AACT_DB   = "aact"

def get_engine(): #this f creates the URL to "communicate" with PostgreSQL database of ClinicalTrials.
    url = (
        f"postgresql+psycopg2://{os.getenv('AACT_USER')}:" #os.gtenv goes to my .env (where I keep my credential)
        f"{os.getenv('AACT_PASSWORD')}@{AACT_HOST}:{AACT_PORT}/{AACT_DB}"
    )
    return create_engine(url, connect_args={"connect_timeout": 10}) 

TABLES = {#define a dictionary where each key is the file name that will be create. the values is the sql query used to extract the data
    "studies":    "SELECT nct_id, brief_title, overall_status, phase, "
                  "start_date, completion_date, enrollment FROM studies LIMIT 10000",
    "conditions": "SELECT nct_id, name AS condition FROM conditions "
                  "WHERE nct_id IN (SELECT nct_id FROM studies LIMIT 10000)",
    "sponsors":   "SELECT nct_id, name AS sponsor, lead_or_collaborator FROM sponsors "
                  "WHERE nct_id IN (SELECT nct_id FROM studies LIMIT 10000)",
    "outcomes":   "SELECT nct_id, outcome_type, title AS outcome_title FROM outcomes "
                  "WHERE nct_id IN (SELECT nct_id FROM studies LIMIT 10000)",
    "countries":  "SELECT nct_id, name AS country, removed FROM countries "
                  "WHERE nct_id IN (SELECT nct_id FROM studies LIMIT 10000)",
}

def pull_tables(engine, output_dir="data/raw"):
    os.makedirs(output_dir, exist_ok=True) #it creates the folder data/raw, whether it already exists or not
    with engine.connect() as conn: #to communicate directly with database
        for table, query in TABLES.items(): #for each table in the dictionary
            print(f"Pulling {table}...")
            df = pd.read_sql(text(query), conn) #it follows the sql query and trasform the results into dataframe pandas
            df.to_parquet(f"{output_dir}/{table}.parquet", index=False) #saved into parquet (more efficient than cvs)
            print(f"  → {len(df):,} righe salvate")
 
 
if __name__ == "__main__": #only works if i run this
    engine = get_engine()
    pull_tables(engine)
    print("Done.")