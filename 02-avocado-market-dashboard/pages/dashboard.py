"""Price, volume, and organic-premium dashboard."""

from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from dash import Input, Output, callback, dcc, html, register_page


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

TYPE_COLORS = {"conventional": "#9fc58d", "organic": "#35613f"}
TYPE_LABELS = {"conventional": "Conventional", "organic": "Organic"}
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
