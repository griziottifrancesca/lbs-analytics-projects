"""Filterable, server-paginated view of the avocado source data."""

from pathlib import Path

import pandas as pd
from dash import Input, Output, State, callback, dash_table, dcc, html, register_page
from dash.dash_table.Format import Format, Scheme


register_page(
    __name__, path="/raw-data", name="Raw Data",
    title="Raw Data | Avocado Insights", order=2, nav_icon="≡",
)


CSV_PATH = Path(__file__).resolve().parents[1] / "avocado.csv"
RAW_DATA = pd.read_csv(CSV_PATH)
RAW_DATA["_date"] = pd.to_datetime(RAW_DATA["date"], format="%d/%m/%Y")
REGIONS = sorted(RAW_DATA["region"].unique().tolist())
MIN_DATE = RAW_DATA["_date"].min().date()
MAX_DATE = RAW_DATA["_date"].max().date()
PRICE_MIN = float(RAW_DATA["average_price"].min())
PRICE_MAX = float(RAW_DATA["average_price"].max())

COLUMN_LABELS = {
    "date": "Date", "average_price": "Avg. Price",
    "total_volume": "Total Volume", "plu4046": "PLU 4046",
    "plu4225": "PLU 4225", "plu4770": "PLU 4770",
    "total_bags": "Total Bags", "smal_bags": "Small Bags",
    "large_bags": "Large Bags", "xlarge_bags": "XLarge Bags",
    "type": "Type", "region": "Region",
}
NUMERIC_COLUMNS = {
    "average_price", "total_volume", "plu4046", "plu4225", "plu4770",
    "total_bags", "smal_bags", "large_bags", "xlarge_bags",
}
TABLE_COLUMNS = [
    {
        "name": label,
        "id": column,
        "type": "numeric" if column in NUMERIC_COLUMNS else "text",
        **({"format": Format(precision=2, scheme=Scheme.fixed, group=True)}
           if column in NUMERIC_COLUMNS else {}),
    }
    for column, label in COLUMN_LABELS.items()
]


def _filter_data(price_range, avocado_types, regions, start_date, end_date):
    """Return rows matching the page's filter controls."""
    mask = pd.Series(True, index=RAW_DATA.index)
    if price_range:
        low, high = price_range
        mask &= RAW_DATA["average_price"].between(low, high)
    if avocado_types is not None:
        mask &= RAW_DATA["type"].isin(avocado_types)
    if regions:
        mask &= RAW_DATA["region"].isin(regions)
    if start_date:
        mask &= RAW_DATA["_date"] >= pd.Timestamp(start_date)
    if end_date:
        mask &= RAW_DATA["_date"] <= pd.Timestamp(end_date)
    return RAW_DATA.loc[mask]


layout = html.Section([
    html.Div([
        html.P("DATA", className="page-eyebrow"),
        html.H1("Raw Data", className="page-title"),
        html.P(
            "Filter and export the complete weekly avocado sales dataset.",
            className="page-description",
        ),
    ], className="page-heading raw-data-heading"),
    html.Div([
        html.Div([
            html.Div([
                html.Label("PRICE RANGE", htmlFor="raw-price-filter",
                           className="control-label"),
                dcc.RangeSlider(
                    id="raw-price-filter",
                    min=PRICE_MIN, max=PRICE_MAX, step=0.01,
                    value=[PRICE_MIN, PRICE_MAX],
                    marks={
                        round(PRICE_MIN, 2): f"${PRICE_MIN:.2f}",
                        round(PRICE_MAX, 2): f"${PRICE_MAX:.2f}",
                    },
                    tooltip={"placement": "bottom", "always_visible": False},
                    allowCross=False, updatemode="mouseup",
                    className="raw-price-slider",
                ),
            ], className="raw-filter raw-price-filter"),
            html.Div([
                html.Label("TYPE", className="control-label"),
                dcc.Checklist(
                    id="raw-type-filter",
                    options=[{"label": "Organic", "value": "organic"},
                             {"label": "Conventional", "value": "conventional"}],
                    value=["organic", "conventional"], inline=True,
                    className="raw-type-options", inputClassName="raw-checkbox-input",
                    labelClassName="raw-checkbox-label",
                ),
            ], className="raw-filter"),
            html.Div([
                html.Label("REGION", className="control-label"),
                dcc.Dropdown(
                    id="raw-region-filter",
                    options=[{"label": region, "value": region} for region in REGIONS],
                    multi=True, placeholder="All regions", className="raw-region-dropdown",
                ),
            ], className="raw-filter"),
            html.Div([
                html.Label("DATE RANGE", className="control-label"),
                dcc.DatePickerRange(
                    id="raw-date-filter", min_date_allowed=MIN_DATE,
                    max_date_allowed=MAX_DATE, start_date=MIN_DATE, end_date=MAX_DATE,
                    display_format="DD MMM YYYY", className="raw-date-picker",
                ),
            ], className="raw-filter"),
        ], className="raw-filter-grid"),
        html.Div([
            html.Div([
                html.Span(f"{len(RAW_DATA):,}", id="raw-result-count",
                          className="result-number"),
                html.Span(" rows", className="result-label"),
            ], **{"aria-live": "polite"}),
            html.Button("Download filtered CSV", id="raw-download-button",
                        className="download-button"),
            dcc.Download(id="raw-download"),
        ], className="raw-table-toolbar"),
        dash_table.DataTable(
            id="raw-data-table", columns=TABLE_COLUMNS, data=[],
            page_action="custom", page_current=0, page_size=20, page_count=1,
            sort_action="custom", sort_mode="single", sort_by=[],
            fixed_rows={"headers": True}, style_table={"overflowX": "auto"},
            style_cell={
                "minWidth": "118px", "width": "135px", "maxWidth": "190px",
                "padding": "12px 14px", "fontFamily": "inherit", "fontSize": "12px",
                "textAlign": "right", "border": "0",
                "borderBottom": "1px solid #edf1eb", "whiteSpace": "nowrap",
            },
            style_cell_conditional=[
                {"if": {"column_id": "date"}, "textAlign": "left", "minWidth": "108px"},
                {"if": {"column_id": "type"}, "textAlign": "left", "minWidth": "110px"},
                {"if": {"column_id": "region"}, "textAlign": "left", "minWidth": "170px"},
            ],
            style_header={
                "padding": "13px 14px", "backgroundColor": "#f7faf3",
                "color": "#294832", "fontWeight": "700", "fontSize": "11px",
                "textTransform": "uppercase", "letterSpacing": "0.04em",
                "border": "0", "borderBottom": "1px solid #dfe7dc",
            },
            style_data_conditional=[
                {"if": {"row_index": "odd"}, "backgroundColor": "#fbfcfa"},
                {"if": {"state": "active"}, "backgroundColor": "#edf5e7", "border": "0"},
            ],
            css=[
                {"selector": ".dash-spreadsheet-container",
                 "rule": "border-radius: 0 0 14px 14px;"},
                {"selector": ".previous-next-container",
                 "rule": "padding: 18px 8px 8px !important;"},
            ],
        ),
    ], id="raw-data-content", className="raw-data-card"),
], className="page")


@callback(
    Output("raw-data-table", "page_current"),
    Input("raw-price-filter", "value"), Input("raw-type-filter", "value"),
    Input("raw-region-filter", "value"), Input("raw-date-filter", "start_date"),
    Input("raw-date-filter", "end_date"), prevent_initial_call=True,
)
def reset_page(*_filters):
    """Return to the first page whenever filters change."""
    return 0


@callback(
    Output("raw-data-table", "data"), Output("raw-data-table", "page_count"),
    Output("raw-result-count", "children"),
    Input("raw-data-table", "page_current"), Input("raw-data-table", "page_size"),
    Input("raw-data-table", "sort_by"), Input("raw-price-filter", "value"),
    Input("raw-type-filter", "value"), Input("raw-region-filter", "value"),
    Input("raw-date-filter", "start_date"), Input("raw-date-filter", "end_date"),
)
def update_table(page_current, page_size, sort_by, price_range, types, regions, start, end):
    """Filter, sort, and return only the requested table page."""
    filtered = _filter_data(price_range, types, regions, start, end)
    if sort_by:
        sort = sort_by[0]
        filtered = filtered.sort_values(
            sort["column_id"], ascending=sort["direction"] == "asc", kind="stable"
        )
    page_count = max(1, (len(filtered) + page_size - 1) // page_size)
    start_row = page_current * page_size
    page = filtered.iloc[start_row:start_row + page_size]
    return page[list(COLUMN_LABELS)].to_dict("records"), page_count, f"{len(filtered):,}"


@callback(
    Output("raw-download", "data"), Input("raw-download-button", "n_clicks"),
    State("raw-price-filter", "value"), State("raw-type-filter", "value"),
    State("raw-region-filter", "value"), State("raw-date-filter", "start_date"),
    State("raw-date-filter", "end_date"), prevent_initial_call=True,
)
def download_filtered_data(_clicks, price_range, types, regions, start, end):
    """Download every row matching the active filters."""
    filtered = _filter_data(price_range, types, regions, start, end)
    return dcc.send_data_frame(
        filtered[list(COLUMN_LABELS)].to_csv, "avocado-filtered.csv", index=False
    )