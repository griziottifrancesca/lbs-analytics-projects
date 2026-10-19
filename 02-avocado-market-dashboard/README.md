# Avocado Insights
 
This is a US avocado sales data visualization project built with Python and Dash, developed as a group project for the MSc in Analytics and Management at London Business School. The app has three pages: a dashboard of price and volume trends, a US state price heat map, and a searchable raw data table. It is built on 53,415 weekly records across 60 regions (January 2015 – December 2023).
 
**Live app:** https://avocado-dashboard-wwy4.onrender.com/
*(Hosted on Render's free tier: the first load can take up to a minute while the app wakes up.)*
 
## My Role
 
I **coordinated the team** and **built Page 2: US State Heat Map** (`pages/state_map.py`).
 
- **Coordination:** split the app into three pages, each with its own owner and file, on top of a shared app shell (`app.py`) and stylesheet, so team members could work in parallel. Aligned everyone on the same data file, the same volume-weighted price method and one visual theme, so the pages work as a single product.
- **State Map:** designed the market-to-state mapping, the price calculation, the interactive map and its controls. Full details are in the Page 2 section below.
## Run Locally
 
Run the following commands from the project root:
 
```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python app.py
```
 
On macOS / Linux, activate the environment with `source .venv/bin/activate` instead.
 
Once the application starts, the default browser opens `http://127.0.0.1:8050` automatically. You can also open this address manually if browser auto-launching is disabled in your environment.
 
## Project Structure
 
```text
Avocado/
├── app.py                  # Dash entry point, shared application shell, and navigation
├── avocado.csv             # Raw avocado sales data
├── requirements.txt        # Python dependencies (dash, pandas, plotly, gunicorn)
├── README.md               # Project documentation
├── assets/
│   ├── styles.css          # Global styles, avocado-green theme, map and table styles
│   └── dashboard.css       # Dashboard page layout
└── pages/
    ├── dashboard.py        # Page 1: Dashboard
    ├── state_map.py        # Page 2: US State Heat Map
    └── raw_data.py         # Page 3: Raw Data
```
 
### Application Entry Point and Shared Framework
 
`app.py` is the project entry point. It is responsible for:
 
- Creating the Dash application;
- Enabling Dash's multi-page functionality;
- Building the header and sidebar navigation;
- Loading the registered pages from the `pages/` directory;
- Exposing `server` for deployment with Render and Gunicorn.
Changes to the shared application shell or navigation should be made in `app.py`. Page-specific charts and business logic are kept in their own page files.
 
### Page 1: Dashboard
 
- File: `pages/dashboard.py`
- Route: `/`
- Page container ID: `dashboard-content`
- Features:
  - **Average price over time:** volume-weighted prices for Organic and Conventional avocados;
  - **Organic price premium:** the percentage paid for Organic above Conventional in the same period;
  - **Total volume over time:** separate panels for each type, because their volumes differ greatly in scale;
  - Filters for date range, region, and time grouping (weekly, monthly, quarterly).
National charts use only the `TotalUS` source rows. Selecting another region uses only that region, so overlapping geographic aggregates are never combined.
 
### Page 2: US State Heat Map *(built by me)*
 
- File: `pages/state_map.py`
- Route: `/state-map`
- Page container ID: `state-map-content`
- Features: a US state-level avocado price choropleth, Organic and Conventional multi-select controls, a year slider (2015–2023), and detailed hover information.
How it works:
 
1. **Market-to-state mapping.** The source mixes national, macro-region, state, and local-market records. A lookup table (`REGION_TO_STATE`) assigns **46 local markets to 29 US states**, keeping only markets with a clear primary state. Unassignable states remain grey. California and South Carolina use their state-level rows to avoid double counting their cities.
2. **Volume-weighted prices.** For each year, state, and avocado type, price is computed as `Σ(price × volume) / Σ(volume)`, so large markets carry more weight than small ones.
3. **Choropleth.** A Plotly map (Albers USA projection) with a custom green colour scale, where darker means more expensive. Hovering a state shows its name, average price, total volume, and the number of markets behind the figure.
4. **Stable colour scale.** The scale is fixed across all years, using the 2nd–98th percentile of state prices, so a change in colour between years reflects a real change in price.
5. **Client-side updates.** Data is pre-aggregated in Python (year × state × type) and stored once in the browser (`dcc.Store`). A JavaScript `clientside_callback` redraws the map when the slider or toggle changes, with no server round-trip, so the map stays responsive.
6. **Methodology note** under the map explains which markets are included and why some states are grey.
What the map shows (2015–2023, both types): the cheapest states are **Arizona (~$0.84)** and **Texas (~$0.86)**, and prices are highest in the Northeast, led by **Rhode Island (~$1.50)**, **Connecticut (~$1.41)** and **Massachusetts (~$1.39)**.
 
Shared map styling is under the `/* State map page */` section of `assets/styles.css`.
 
### Page 3: Raw Data
 
- File: `pages/raw_data.py`
- Route: `/raw-data`
- Page container ID: `raw-data-content`
- Features: a raw data table with free-text search, type, region and date filters, sortable columns, server-side pagination (20 rows per page), and a **Download filtered CSV** button.
Only the requested page of rows is sent to the browser, so the full dataset is never rendered at once.
 
## Key Findings
 
- Organic avocados sold at a volume-weighted average of **$1.63** vs **$1.12** for Conventional, a **~46% organic premium** (TotalUS, 2015–2023).
- Organic accounts for only **~3.7%** of total volume.
- Prices vary strongly by geography, from about **$0.84** in Arizona to **$1.50** in Rhode Island.
## Tools
 
Python · Dash (multi-page) · Plotly · pandas · JavaScript (client-side callback) · Gunicorn · Render
 
