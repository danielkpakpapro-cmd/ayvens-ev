"""
dashboard.py — Ayvens
========================
Lit data/historique.csv (généré automatiquement chaque jour par GitHub
Actions, voir .github/workflows/scraping.yml) et affiche :
  - la proportion électrique par marque et par modèle,
  - filtrable par type de financement (leasing / cash),
  - l'évolution dans le temps.

Lancement :
    pip install streamlit pandas plotly --break-system-packages
    streamlit run dashboard.py
"""

import os

import pandas as pd
import plotly.express as px
import streamlit as st

CSV_PATH = "data/historique.csv"

st.set_page_config(page_title="Ayvens — proportion électrique", layout="wide")
st.title("🔋 Ayvens — proportion de véhicules électriques")

if not os.path.exists(CSV_PATH):
    st.warning(f"Aucune donnée trouvée ({CSV_PATH} n'existe pas encore). "
               f"Lance d'abord `python scraper.py` pour générer un premier relevé.")
    st.stop()

df = pd.read_csv(CSV_PATH, sep=None, engine="python")

df["date_releve"] = pd.to_datetime(df["date_releve"], errors="coerce")
n_invalid = df["date_releve"].isna().sum()
if n_invalid:
    st.warning(f"{n_invalid} ligne(s) ignorée(s) (date illisible).")
    df = df.dropna(subset=["date_releve"])
if df.empty:
    st.warning("Le fichier de données est vide.")
    st.stop()

last_date = df["date_releve"].max()
st.caption(f"Dernier relevé : {last_date.strftime('%d/%m/%Y %H:%M')}")

latest = df[df["date_releve"] == last_date].copy()
latest = latest[latest["nb_total"] > 0]

# --- Filtre type de financement ---
finance_types = sorted(latest["type_financement"].unique())
selected_finance = st.multiselect(
    "Type de financement", finance_types, default=finance_types,
    help="Location Longue Durée (leasing) et/ou Achat comptant (cash)"
)
latest_f = latest[latest["type_financement"].isin(selected_finance)] if selected_finance else latest

# --- Agrégation par marque (somme leasing+cash si les deux sélectionnés) ---
by_brand = (
    latest_f.groupby("marque")[["nb_total", "nb_electrique"]]
    .sum()
    .reset_index()
)
by_brand["proportion_electrique"] = by_brand["nb_electrique"] / by_brand["nb_total"]
by_brand = by_brand.sort_values("nb_total", ascending=False)

# --- KPI ---
col1, col2, col3 = st.columns(3)
total_vehicules = by_brand["nb_total"].sum()
total_electriques = by_brand["nb_electrique"].sum()
prop_globale = (total_electriques / total_vehicules) if total_vehicules else 0
col1.metric("Véhicules (vue filtrée)", f"{total_vehicules:,}".replace(",", " "))
col2.metric("Dont électriques", f"{total_electriques:,}".replace(",", " "))
col3.metric("Proportion électrique", f"{prop_globale:.1%}")

st.divider()

st.subheader("Proportion électrique par marque")
fig = px.bar(
    by_brand, x="marque", y="proportion_electrique",
    hover_data=["nb_total", "nb_electrique"],
    labels={"proportion_electrique": "% électrique", "marque": "Marque"},
    text="nb_electrique",
)
fig.update_traces(texttemplate="%{text}", textposition="outside")
fig.update_yaxes(tickformat=".0%")
st.plotly_chart(fig, use_container_width=True)

st.divider()

# --- Détail par marque et modèle ---
st.subheader("Détail par marque et modèle")

col_f1, col_f2 = st.columns([2, 1])
marques_dispo = sorted(latest_f["marque"].unique())
selected_marques = col_f1.multiselect("Filtrer par marque", marques_dispo, default=[])
only_electric = col_f2.checkbox("Uniquement modèles avec ≥1 électrique")

detail = (
    latest_f.groupby(["marque", "modele"])[["nb_total", "nb_electrique"]]
    .sum()
    .reset_index()
)
detail["proportion_electrique"] = detail["nb_electrique"] / detail["nb_total"]
detail = detail[detail["nb_total"] > 0]

if selected_marques:
    detail = detail[detail["marque"].isin(selected_marques)]
if only_electric:
    detail = detail[detail["nb_electrique"] > 0]

detail = detail.sort_values(["marque", "nb_total"], ascending=[True, False])

st.dataframe(
    detail.rename(columns={
        "marque": "Marque", "modele": "Modèle", "nb_total": "Total",
        "nb_electrique": "Électrique", "proportion_electrique": "% Électrique",
    }).style
        .format({"% Électrique": "{:.1%}"}),
    use_container_width=True,
    hide_index=True,
    height=500,
)

st.divider()

# --- Évolution dans le temps ---
st.subheader("Évolution dans le temps")
if df["date_releve"].nunique() <= 1:
    st.info("Un seul relevé pour l'instant — l'historique s'enrichira à chaque exécution automatique.")
else:
    df_f = df[df["type_financement"].isin(selected_finance)] if selected_finance else df
    evo = df_f.groupby(["date_releve", "marque"])[["nb_total", "nb_electrique"]].sum().reset_index()
    evo["proportion_electrique"] = evo["nb_electrique"] / evo["nb_total"]

    marques_evo = sorted(evo.loc[evo["nb_total"] > 0, "marque"].unique())
    selected_evo = st.multiselect("Marques à afficher (évolution)", marques_evo, default=marques_evo[:5])
    evo_sel = evo[evo["marque"].isin(selected_evo)] if selected_evo else evo

    fig_evo = px.line(evo_sel, x="date_releve", y="proportion_electrique", color="marque", markers=True)
    fig_evo.update_yaxes(tickformat=".0%")
    st.plotly_chart(fig_evo, use_container_width=True)

st.divider()
st.caption("💡 Les données sont mises à jour automatiquement une fois par jour (GitHub Actions).")