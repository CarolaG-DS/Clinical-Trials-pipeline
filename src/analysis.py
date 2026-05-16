import pandas as pd
import plotly.express as px #data visualization
import plotly.graph_objects as go
from sqlalchemy import create_engine

engine = create_engine("sqlite:///data/clinical_trials.db")

def load(query): #Custom function called load.
    return pd.read_sql(query, engine) #You give it a SQL command (query), it uses the bridge (engine) and returns the data ready to go in a Pandas table.

# ── 1. lenght for phase ─────────────────────────────────
#from Query SQL (data preparation) to Plot (data visualization).
def plot_duration_by_phase(): 
    df = load("""
        SELECT p.phase_clean, 
               ROUND(AVG(f.duration_months), 1) AS avg_duration, 
               COUNT(*) AS n_trials
        FROM fact_trials f
        JOIN dim_phase p USING (phase_id)
        WHERE f.duration_months > 0
          AND f.duration_months < 300
          AND p.phase_clean != 'Unknown'
        GROUP BY p.phase_clean
        ORDER BY avg_duration DESC
    """)
    fig = px.bar( #bar chart
        df, x="phase_clean", y="avg_duration",
        text="avg_duration",
        labels={"phase_clean": "Fase", "avg_duration": "Durata media (mesi)"},
        title="Durata media degli studi clinici per fase",
        color="avg_duration",
        color_continuous_scale="Blues"
    )
    fig.update_traces(textposition="outside")
    fig.write_html("data/plot_duration_by_phase.html")
    print("  → plot_duration_by_phase.html salvato")
# this bar chart It shows the overall trend of clinical research. It tells you, for example: "On average, regardless of the study, Phase 3 lasts twice as long as Phase 1."
# ── 2. COMPLETION RATE PER PHASE ──────────────────────────────
#At what stage of research do studies actually come to an end?
#Before is_completed was changed into 1 and 0. sum(f.iscompleted) is equivalent to counting only completed studies. it is diveded by the total (*) number of studies in that phase.
# n_trials>100 Show me only the phases that have at least 100 studies, to make it more reliable
def plot_completion_rate():
    df = load("""
        SELECT phase_clean,
               ROUND(100.0 * SUM(is_completed) / COUNT(*), 1) AS completion_rate,
               COUNT(*) AS n_trials
        FROM fact_trials
        WHERE phase_clean NOT IN ('Unknown', 'N/A')
        GROUP BY phase_clean
        HAVING n_trials > 10
        ORDER BY completion_rate DESC
    """)
    fig = px.bar(
        df, x="phase_clean", y="completion_rate",
        text="completion_rate",
        labels={"phase_clean": "Fase", "completion_rate": "% completati"},
        title="Completion rate per fase clinica",
        color="completion_rate",
        color_continuous_scale="Teal"
    )
    fig.update_traces(textposition="outside")
    fig.write_html("data/plot_completion_rate.html")
    print("  → plot_completion_rate.html salvato")
    
# ── 3. TOP 15 SPONSOR ────────────────────────────────────────
def plot_top_sponsors():
    df = load("""
        SELECT sponsor_name,
               trials_led AS n_trials,
               sponsor_rank
        FROM dim_sponsors
        WHERE sponsor_rank <= 15
        ORDER BY n_trials DESC
    """)
    fig = px.bar(
        df, x="n_trials", y="sponsor_name",
        orientation="h",
        labels={"n_trials": "N. trial condotti", "sponsor_name": "Sponsor"},
        title="Top 15 sponsor per numero di trial condotti",
        color="n_trials",
        color_continuous_scale="Blues"
    )
    fig.update_layout(yaxis={"categoryorder": "total ascending"})
    fig.write_html("data/plot_top_sponsors.html")
    print("  → plot_top_sponsors.html salvato")
    
    
# join It is used to retrieve the company name
#COUNT(DISTINCT f.nct_id) AS n_trials: Counts how many unique studies each sponsor has.
#ORDER BY n_trials DESC LIMIT 15: Takes only the "Top 15".   

#Top right: You'll find the "Super Sponsors": tons of studies, almost all of them completed.

#Bottom right: You'll find those who do tons of studies but leave many unfinished.

# ── 4. HEATMAP Geographic ────────────────────────────────────
def plot_geo():
    df = load("""
        SELECT country, country_trial_count AS n_trials
        FROM dim_geography
        WHERE country IS NOT NULL
        ORDER BY n_trials DESC
        LIMIT 50
    """)
    fig = px.bar(
        df, x="n_trials", y="country",
        orientation="h",
        title="Top 50 paesi per numero di studi clinici",
        labels={"n_trials": "N. studi", "country": "Paese"},
        color="n_trials",
        color_continuous_scale="Viridis"
    )
    fig.update_layout(yaxis={"categoryorder": "total ascending"}, height=1200)
    fig.write_html("data/plot_geo.html")
    print("  → plot_geo.html salvato")
# join Essential to transform the geographic ID into the country name
#count - Count how many unique studies have been conducted in that territory.
#WHERE country IS NOT NULL: Cleans the data by removing rows where the country is not recorded.
#px.choropleth. A choropleth map is a type of visualization where geographic areas (countries) are colored with different hues based on a numerical value.
   

# ── 5. Main Execution Block ──────────────────────────────────── 
def run_analysis(): #Orchestrator . decides who starts and in which order
    print("Generando grafici...")
    plot_duration_by_phase()
    plot_completion_rate()
    plot_top_sponsors()
    plot_geo()
    print("Analisi completata.")

if __name__ == "__main__": #Boilerplate del Main
    run_analysis()