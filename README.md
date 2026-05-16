# Clinical Trials Intelligence Pipeline

> End-to-end data engineering and analysis pipeline on 10,000 real clinical studies from ClinicalTrials.gov (AACT database).

![Python](https://img.shields.io/badge/Python-3.14-blue?logo=python)
![SQL](https://img.shields.io/badge/SQL-SQLite-lightblue?logo=sqlite)
![pandas](https://img.shields.io/badge/pandas-2.0-purple?logo=pandas)
![plotly](https://img.shields.io/badge/plotly-interactive-green?logo=plotly)

---

## Objective

Build a production-style data pipeline that ingests raw clinical trial data, transforms it into a clean analytical warehouse, and extracts actionable insights on trial duration, completion rates, and sponsor activity.

---

## Key Findings

| Finding | Value |
|---------|-------|
| Phase 2 trials last the longest | ~41 months average |
| Phase 1 has the highest completion rate | 65.9% |
| Early Phase 1 has the lowest completion rate | 35.3% |
| Top sponsor by volume | NIAID (National Institute of Allergy and Infectious Diseases) |
| Most active country | United States (8,180 studies) |

---

## Pipeline Architecture

ClinicalTrials.gov (AACT PostgreSQL)
↓
ingestion.py        → data/raw/*.parquet
↓
transform.py        → stg_studies, stg_conditions, stg_sponsors, stg_countries
↓
warehouse.py        → dim_phase, dim_sponsors, dim_geography, fact_trials
↓
analysis.py         → 4 interactive HTML charts

---

## Project Structure

clinical-trials-pipeline/
├── src/
│   ├── ingestion.py       # pulls data from AACT public DB
│   ├── transform.py       # staging: dedup, normalize, clean
│   ├── warehouse.py       # star schema: fact + dim tables
│   ├── analysis.py        # 4 plotly visualizations
│   └── pipeline.py        # runs the full pipeline end-to-end
├── sql/
│   ├── 01_staging.sql     # SQL logic for staging layer
│   └── 02_warehouse.sql   # star schema documentation
├── notebooks/
│   └── clinical_trials_analysis.ipynb  # full narrative analysis
├── data/                  # gitignored
├── .env.example
├── requirements.txt
└── README.md

---

## How to Run

### 1. Clone the repo and install dependencies

```bash
git clone https://github.com/YOUR_USERNAME/clinical-trials-pipeline.git
cd clinical-trials-pipeline
pip install -r requirements.txt
```

### 2. Set up credentials

```bash
cp .env.example .env
# Edit .env and add your AACT credentials
# Register for free at: https://aact.ctti-clinicaltrials.org/users/sign_up
```

### 3. Run the full pipeline

```bash
python src/pipeline.py
```

Or run each module individually:

```bash
python src/ingestion.py    # ~2 min — pulls data from AACT
python src/transform.py    # ~1 min — staging and cleaning
python src/warehouse.py    # ~30 sec — builds star schema
python src/analysis.py     # ~1 min — generates charts
```

### 4. Open the notebook

```bash
jupyter notebook notebooks/clinical_trials_analysis.ipynb
```

---

## Data Source

**AACT (Aggregate Analysis of ClinicalTrials.gov)**  
Maintained by the Clinical Trials Transformation Initiative (CTTI).  
Public access at [aact.ctti-clinicaltrials.org](https://aact.ctti-clinicaltrials.org) — free registration required.

This project uses a subset of 10,000 studies to ensure reproducibility on standard hardware.

---

## Technical Notes

**Why SQLite instead of PostgreSQL?**  
Zero configuration, single file, fully reproducible on any machine.

**Why pandas for the fact table JOIN?**  
Staging tables (~15k rows each) caused SQLite memory overflow during JOIN operations. pandas `merge()` handles this efficiently in-memory.

**Why keep `sql/02_warehouse.sql` if Python builds the warehouse?**  
The SQL file documents the intended schema. The Python file implements it efficiently.

---

## Stack

- **Python 3.14** — pipeline orchestration
- **SQLAlchemy + SQLite** — data storage
- **pandas** — data transformation and heavy JOINs
- **plotly** — interactive visualizations
- **AACT PostgreSQL** — data source