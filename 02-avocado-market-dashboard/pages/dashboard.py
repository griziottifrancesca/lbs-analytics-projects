"""Price, volume, organic-premium, and top-markets dashboard."""

from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from dash import Input, Output, callback, ctx, dcc, html, register_page


register_page(
    __name__, path="/", name="Dashboard",
    title="Dashboard | Avocado Insights", order=0, nav_icon="▦",
)

DATA_PATH = Path(__file__).resolve().parents[1] / "avocado.csv"
DATA = pd.read_csv(DATA_PATH)
DATA["date_value"] = pd.to_datetime(DATA["date"], format="%d/%m/%Y")
DATA["weighted_price"] = DATA["average_price"] * DATA["total_volume"]
MIN_DATE = DATA["date_value"].min().date()
MAX_DATE = DATA["date_value"].max().date()
REGIONS = sorted(DATA["region"].unique())
YEARS = sorted(DATA["date_value"].dt.year.unique().tolist())

# The source mixes national rows (TotalUS), macro-region aggregates (West,
# Northeast, Southeast, SouthCentral, Midsouth, GreatLakes, Plains), and real
# city/state markets. Ranking across mixed levels lets an aggregate outrank
# the individual markets it's made of, so Top Markets uses the same
# defensible, non-overlapping market list as the State Map page.
REAL_MARKETS = {
    "Albany", "Atlanta", "BaltimoreWashington", "BirminghamMontgomery", "Boise",
    "Boston", "BuffaloRochester", "California", "Charlotte", "Chicago",
    "CincinnatiDayton", "Columbus", "DallasFtWorth", "Denver", "Detroit",
    "GrandRapids", "HarrisburgScranton", "HartfordSpringfield", "Houston",
    "Indianapolis", "Jacksonville", "LasVegas", "Louisville", "Miami",
    "MiamiFtLauderdale", "Nashville", "NewOrleans", "NewYork", "Orlando",
    "PeoriaSpringfield", "Philadelphia", "PhoenixTucson", "Pittsburgh",
    "Portland", "Providence", "RaleighGreensboro", "RichmondNorfolk",
    "Roanoke", "SouthCarolina", "Seattle", "Spokane", "StLouis", "Syracuse",
    "Tampa", "Toledo", "Wichita",
}
MARKET_REGIONS = [region for region in REGIONS if region in REAL_MARKETS]

TYPE_COLORS = {"conventional": "#9fc58d", "organic": "#35613f"}
TYPE_LABELS = {"conventional": "Conventional", "organic": "Organic"}
METRIC_LABELS = {"total_volume": "Total Volume", "average_price": "Avg. Price"}
GRID_COLOR = "#e7ece5"
MUTED = "#68726a"


def _aggregate(source: pd.DataFrame, frequency: str) -> pd.DataFrame:
    """Aggregate each type independently using volume-weighted prices."""
    result = (
        source.groupby([pd.Grouper(key="date_value", freq=frequency), "type"],
                       as_index=False)
        .agg(weighted_price=("weighted_price", "sum"),
             total_volume=("total_volume", "sum"))
    )
    result = result.loc[result["total_volume"] > 0].copy()
    result["average_price"] = result["weighted_price"] / result["total_volume"]
    return result


def _base_figure(figure: go.Figure, height: int = 370) -> go.Figure:
    figure.update_layout(
        height=height, margin={"l": 60, "r": 25, "t": 32, "b": 68},
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font={"family": "Inter, sans-serif", "color": "#253028", "size": 12},
        hovermode="x unified",
        hoverlabel={"bgcolor": "#ffffff", "bordercolor": "#d5e7c8"},
        legend={"orientation": "h", "x": 0, "y": 1.12, "font": {"size": 11}},
        uirevision="dashboard-charts",
    )
    figure.update_xaxes(
        title_text="Date", showgrid=False, showline=True,
        linecolor="#bfc8c0", linewidth=1, ticks="outside", ticklen=5,
        tickcolor="#bfc8c0", showticklabels=True, automargin=True,
        tickfont={"color": MUTED, "size": 11}, title_font={"color": MUTED, "size": 11},
    )
    figure.update_yaxes(
        gridcolor=GRID_COLOR, zeroline=False, automargin=True,
        tickfont={"color": MUTED},
    )
    return figure


def _empty_figure(message: str, height: int = 370) -> go.Figure:
    figure = go.Figure()
    figure.add_annotation(
        text=message, x=0.5, y=0.5, xref="paper", yref="paper",
        showarrow=False, font={"color": MUTED, "size": 13},
    )
    return _base_figure(figure, height)


def _card(title, description, graph_id, wide=False, height=370):
    classes = "chart-dashboard-card chart-dashboard-card-wide" if wide else "chart-dashboard-card"
    return html.Div([
        html.H2(title), html.P(description),
        dcc.Graph(
            id=graph_id,
            figure=_empty_figure("Loading chart…", height),
            config={"displayModeBar": False, "responsive": True},
            className="chart-dashboard-graph",
            style={"height": f"{height}px", "minHeight": f"{height}px"},
        ),
    ], className=classes)


layout = html.Section([
    html.Div([
        html.P("OVERVIEW", className="page-eyebrow"),
        html.H1("Dashboard", className="page-title"),
        html.P(
            "Explore price, volume, and the organic premium over time.",
            className="page-description",
        ),
    ], className="page-heading"),
    html.Div([
        html.Div([
            html.Label("DATE RANGE", className="control-label"),
            dcc.DatePickerRange(
                id="dashboard-date-range", min_date_allowed=MIN_DATE,
                max_date_allowed=MAX_DATE, start_date=MIN_DATE, end_date=MAX_DATE,
                display_format="DD MMM YYYY", className="chart-dashboard-date",
            ),
        ], className="chart-dashboard-filter"),
        html.Div([
            html.Label("REGION", className="control-label"),
            dcc.Dropdown(
                id="dashboard-region", options=[{"label": r, "value": r} for r in REGIONS],
                value="TotalUS", clearable=False, className="chart-dashboard-dropdown",
            ),
        ], className="chart-dashboard-filter"),
        html.Div([
            html.Label("TIME GROUPING", className="control-label"),
            dcc.Dropdown(
                id="dashboard-frequency",
                options=[{"label": "Weekly", "value": "W-SUN"},
                         {"label": "Monthly", "value": "MS"},
                         {"label": "Quarterly", "value": "QS"}],
                value="MS", clearable=False, searchable=False,
                className="chart-dashboard-dropdown",
            ),
        ], className="chart-dashboard-filter"),
    ], className="chart-dashboard-filter-bar"),
    html.Div([
        _card("Average price over time",
              "Volume-weighted prices for Organic and Conventional avocados.",
              "dashboard-price-chart"),
        _card("Organic price premium",
              "The percentage paid above Conventional in the same period.",
              "dashboard-premium-chart"),
        _card("Total volume over time",
              "Separate panels preserve visibility despite the large difference in scale.",
              "dashboard-volume-chart", wide=True, height=440),
    ], className="chart-dashboard-grid"),
    html.P(
        "National charts use only the TotalUS source rows. Selecting another region "
        "uses only that region, so overlapping geographic aggregates are never combined.",
        className="chart-dashboard-method",
    ),
    html.Div([
        html.Div([
            html.Label("YEAR", className="control-label"),
            dcc.Dropdown(
                id="top-markets-year",
                options=[{"label": str(year), "value": year} for year in YEARS],
                value=YEARS[-1], clearable=False, className="chart-dashboard-dropdown",
            ),
        ], className="chart-dashboard-filter"),
        html.Div([
            html.Label("RANK BY", className="control-label"),
            dcc.RadioItems(
                id="top-markets-metric",
                options=[{"label": "Total Volume", "value": "total_volume"},
                         {"label": "Avg. Price", "value": "average_price"}],
                value="total_volume", inline=True,
                className="type-toggle", inputClassName="type-toggle-input",
                labelClassName="type-toggle-option",
            ),
        ], className="chart-dashboard-filter"),
        html.Div([
            html.Label("TOP N", className="control-label"),
            html.Div([
                dcc.Input(
                    id="top-markets-n-input", type="number", min=1, max=15,
                    step=1, value=5, className="top-markets-n-input",
                ),
                dcc.Slider(
                    id="top-markets-n", min=1, max=15, step=1, value=5,
                    marks={n: str(n) for n in (1, 5, 10, 15)},
                    included=False, updatemode="drag",
                    tooltip={"placement": "top", "always_visible": False},
                ),
            ], className="top-markets-n-row"),
        ], className="chart-dashboard-filter top-markets-n-control"),
    ], className="chart-dashboard-filter-bar"),
    html.Div([
        _card("Top markets",
              "Ranked non-overlapping city/state markets for the selected year. "
              "Conventional and Organic are shown on separate scales.",
              "top-markets-chart", wide=True, height=520),
    ], className="chart-dashboard-grid"),
], id="dashboard-content", className="page chart-dashboard-page")


@callback(
    Output("dashboard-price-chart", "figure"),
    Output("dashboard-volume-chart", "figure"),
    Output("dashboard-premium-chart", "figure"),
    Input("dashboard-date-range", "start_date"),
    Input("dashboard-date-range", "end_date"),
    Input("dashboard-region", "value"),
    Input("dashboard-frequency", "value"),
)
def update_charts(start_date, end_date, region, frequency):
    """Build all charts from one consistently filtered and aggregated dataset."""
    if not start_date or not end_date or not region:
        empty = _empty_figure("Choose a date range and region to view the data.")
        return empty, empty, empty

    selected = DATA.loc[
        DATA["date_value"].between(pd.Timestamp(start_date), pd.Timestamp(end_date))
        & DATA["region"].eq(region)
    ]
    summary = _aggregate(selected, frequency or "MS")
    if summary.empty:
        empty = _empty_figure("No data is available for this selection.")
        return empty, empty, empty

    price = go.Figure()
    for avocado_type in ("conventional", "organic"):
        series = summary.loc[summary["type"].eq(avocado_type)]
        price.add_trace(go.Scatter(
            x=series["date_value"], y=series["average_price"], mode="lines",
            name=TYPE_LABELS[avocado_type],
            line={"color": TYPE_COLORS[avocado_type], "width": 2.5},
            hovertemplate=f"{TYPE_LABELS[avocado_type]}: $%{{y:.2f}}<extra></extra>",
        ))
    _base_figure(price)
    price.update_yaxes(title="Weighted average price", tickprefix="$", tickformat=".2f")

    volume = make_subplots(
        rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.13,
        subplot_titles=("Conventional", "Organic"),
    )
    for row, avocado_type in enumerate(("conventional", "organic"), start=1):
        series = summary.loc[summary["type"].eq(avocado_type)]
        volume.add_trace(go.Scatter(
            x=series["date_value"], y=series["total_volume"], mode="lines",
            fill="tozeroy", name=TYPE_LABELS[avocado_type], showlegend=False,
            line={"color": TYPE_COLORS[avocado_type], "width": 1.8},
            fillcolor=("rgba(159,197,141,0.40)" if avocado_type == "conventional"
                       else "rgba(53,97,63,0.25)"),
            hovertemplate="Volume: %{y:,.0f}<extra></extra>",
        ), row=row, col=1)
    _base_figure(volume, 440)
    volume.update_xaxes(title_text=None, showticklabels=False, row=1, col=1)
    volume.update_xaxes(title_text="Date", showticklabels=True, row=2, col=1)
    volume.update_yaxes(title="Volume", tickformat="~s", row=1, col=1)
    volume.update_yaxes(title="Volume", tickformat="~s", row=2, col=1)

    aligned = summary.pivot(
        index="date_value", columns="type", values="average_price"
    ).dropna(subset=["organic", "conventional"])
    if aligned.empty:
        premium = _empty_figure("Both avocado types are required to calculate premium.")
    else:
        aligned["premium"] = (
            aligned["organic"] / aligned["conventional"] - 1
        ) * 100
        premium = go.Figure(go.Scatter(
            x=aligned.index, y=aligned["premium"], mode="lines",
            line={"color": TYPE_COLORS["organic"], "width": 2.5},
            fill="tozeroy", fillcolor="rgba(71,122,79,0.14)",
            customdata=aligned[["organic", "conventional"]],
            hovertemplate=("Premium: %{y:.1f}%<br>Organic: $%{customdata[0]:.2f}"
                           "<br>Conventional: $%{customdata[1]:.2f}<extra></extra>"),
        ))
        premium.add_hline(y=0, line_color="#aeb7b0", line_width=1)
        _base_figure(premium)
        premium.update_layout(showlegend=False)
        premium.update_yaxes(title="Organic premium", ticksuffix="%", tickformat=".0f")

    return price, volume, premium


@callback(
    Output("top-markets-n", "value"),
    Output("top-markets-n-input", "value"),
    Input("top-markets-n", "value"),
    Input("top-markets-n-input", "value"),
    prevent_initial_call=True,
)
def sync_top_n_controls(slider_value, input_value):
    """Keep the slider and the number box showing the same value.

    Whichever control the user just touched wins; the other one is updated
    to match, clamped to the 3-15 range.
    """
    trigger = ctx.triggered_id
    raw_value = input_value if trigger == "top-markets-n-input" else slider_value
    if raw_value is None:
        raw_value = slider_value if slider_value is not None else 5
    clamped = max(1, min(15, int(raw_value)))
    return clamped, clamped


@callback(
    Output("top-markets-chart", "figure"),
    Input("top-markets-year", "value"),
    Input("top-markets-metric", "value"),
    Input("top-markets-n", "value"),
)
def update_top_markets(year, metric, top_n):
    """Rank markets for the selected year and metric, split by avocado type."""
    if not year or not metric or not top_n:
        return _empty_figure("Choose a year, metric, and N to view rankings.", 520)

    year_data = DATA.loc[
        (DATA["date_value"].dt.year == year) & DATA["region"].isin(MARKET_REGIONS)
    ]
    if year_data.empty:
        return _empty_figure("No data is available for this year.", 520)

    # Region-level totals decide the ranking: summed volume, or a single
    # volume-weighted price per region (never a sum of per-type averages).
    region_totals = (
        year_data.groupby("region", as_index=False)
        .agg(weighted_price=("weighted_price", "sum"),
             total_volume=("total_volume", "sum"))
    )
    region_totals["average_price"] = (
        region_totals["weighted_price"] / region_totals["total_volume"]
    )
    ranking = region_totals.set_index("region")[metric].sort_values(ascending=False)
    top_regions = ranking.head(int(top_n)).index.tolist()
    if not top_regions:
        return _empty_figure("No ranked markets are available for this selection.", 520)

    # Per-type breakdown for just the top regions, in ranked order.
    by_type = (
        year_data.loc[year_data["region"].isin(top_regions)]
        .groupby(["region", "type"], as_index=False)
        .agg(weighted_price=("weighted_price", "sum"),
             total_volume=("total_volume", "sum"))
    )
    by_type["average_price"] = by_type["weighted_price"] / by_type["total_volume"]
    by_type["region"] = pd.Categorical(by_type["region"], categories=top_regions, ordered=True)
    by_type = by_type.sort_values("region")

    # Conventional volume dwarfs organic volume, so each type gets its own
    # panel and y-axis scale rather than sharing one axis where organic bars
    # would be barely visible next to conventional ones.
    figure = make_subplots(
        rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.16,
        subplot_titles=("Conventional", "Organic"),
    )
    hover_value = ("$%{y:.2f}<extra></extra>" if metric == "average_price"
                   else "%{y:,.0f}<extra></extra>")
    for row, avocado_type in enumerate(("conventional", "organic"), start=1):
        series = by_type.loc[by_type["type"].eq(avocado_type)]
        figure.add_trace(go.Bar(
            x=series["region"], y=series[metric], name=TYPE_LABELS[avocado_type],
            marker_color=TYPE_COLORS[avocado_type], showlegend=False,
            hovertemplate=f"{TYPE_LABELS[avocado_type]}: {hover_value}",
        ), row=row, col=1)
    _base_figure(figure, 520)
    figure.update_xaxes(title_text=None, row=1, col=1)
    figure.update_xaxes(title_text="Region", row=2, col=1)
    axis_title = "Weighted average price" if metric == "average_price" else "Total volume"
    axis_kwargs = ({"tickprefix": "$", "tickformat": ".2f"} if metric == "average_price"
                    else {"tickformat": "~s"})
    figure.update_yaxes(title=axis_title, row=1, col=1, **axis_kwargs)
    figure.update_yaxes(title=axis_title, row=2, col=1, **axis_kwargs)
    return figure