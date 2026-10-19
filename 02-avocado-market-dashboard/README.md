# Avocado: US Market Insights Dashboard

Group project for the MSc in Analytics and Management at London Business School.

**Live dashboard:** https://avocado-dashboard-wwy4.onrender.com/
*(Hosted on Render's free tier: the first load can take up to a minute while the app wakes up.)*

## Overview
An interactive, multi-page web dashboard exploring US weekly avocado sales:
53,415 weekly records across 60 regions, January 2015 – December 2023.

## Pages
- **Dashboard:** volume-weighted average price for Organic vs Conventional avocados, the organic price premium (%) and sales volume over time. Filters for date range, region and weekly / monthly / quarterly grouping.
- **State Map:** US choropleth of volume-weighted average prices by state, with an Organic/Conventional toggle and a year slider. The colour scale is fixed across years so changes are comparable.
- **Raw Data:** searchable, sortable table with region, type and date filters, server-side pagination, and CSV export of the filtered rows.

## Key findings (TotalUS, 2015–2023)
- Organic avocados sold at a volume-weighted average of **$1.63** vs **$1.12** for Conventional, a **~46% organic premium**.
- Organic accounts for only **~3.7%** of total volume.

## Data handling decisions
- **Volume-weighted prices** throughout, so large markets count more than small ones.
- The source mixes national, macro-region, state and city rows. To avoid double counting, national charts use only `TotalUS` rows, and the map only uses markets that can be reliably assigned to one state (unassignable states stay grey).

## Tools
Python · Dash (multi-page) · Plotly · pandas · Gunicorn · deployed on Render

## My contribution
[Describe the part you personally built]

## Project structure
```text
├── app.py              # Dash entry point, shared layout and navigation
├── avocado.csv         # Source data
├── requirements.txt    # Python dependencies
├── assets/             # styles.css, dashboard.css
└── pages/
    ├── dashboard.py    # Price, premium and volume charts
    ├── state_map.py    # US state heat map
    └── raw_data.py     # Filterable data table with CSV export
```

## Run locally
```bash
pip install -r requirements.txt
python app.py
```
Then open http://127.0.0.1:8050
