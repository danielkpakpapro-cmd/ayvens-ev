# Ayvens — suivi de la proportion de véhicules électriques

Projet minimal, focalisé uniquement sur Ayvens (used-cars.ayvens.com).

## Installation

```bash
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt --break-system-packages
pip install -r requirements-scraping.txt --break-system-packages
playwright install chromium
```

## Utilisation

```bash
python scraper.py
```

Ajoute une ligne par (marque, modèle, type de financement) dans
`data/historique.csv`.

## Dashboard

```bash
streamlit run dashboard.py
```

## Comment ça marche

Contrairement à Aramisauto, Ayvens n'affiche pas de compteurs par marque
dans son panneau de filtres. Le scraper (`scraper.py`) utilise donc une
approche différente : il charge le catalogue complet (et sa version filtrée
sur "Électrique"), scrolle jusqu'à charger toutes les fiches véhicules
(chargement différé), puis lit l'attribut `aria-label` de chaque fiche
("View details for PEUGEOT 3008") pour compter automatiquement les
marques et modèles réellement présents sur le site.

**Avantage** : aucune liste de marques codée en dur — si Ayvens ajoute une
nouvelle marque ou un nouveau modèle, il apparaît automatiquement au
prochain scraping, sans modification du code.

Deux types de financement sont scrapés séparément : `leasing` (Location
Longue Durée) et `cash` (Achat comptant) — voir la colonne
`type_financement` dans le CSV.

## Déploiement en ligne (Streamlit Community Cloud + GitHub Actions)

Même procédure que le projet Aramisauto :
1. Crée un dépôt GitHub et pousse ce dossier.
2. Déploie `dashboard.py` sur https://share.streamlit.io.
3. Le fichier `.github/workflows/scraping.yml` fait tourner le scraping
   automatiquement chaque jour (7h UTC), sans dépendre de ta machine, et
   pousse les données mises à jour — ce qui redéploie le dashboard en ligne
   automatiquement.

## Limites connues

- Le scraping est plus long que pour Aramisauto (chargement différé sur
  ~600-650 fiches par catalogue × 2 types de financement × 2 filtres
  carburant) — prévoir quelques minutes d'exécution.
- Si Ayvens change sa structure HTML (attribut `aria-label` notamment), le
  scraper devra être ajusté — relance en mode visible
  (`SCRAPER_HEADLESS=0 python scraper.py`) pour observer ce qui bloque.
