"""Interactive US state-level avocado price heat map."""

from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
from dash import Input, Output, State, clientside_callback, dcc, html, register_page


register_page(
    __name__, path="/state-map", name="State Map",
    title="State Map | Avocado Insights", order=1, nav_icon="◇",
)


# The source mixes national, macro-region, state, and local-market rows. Only
# markets with a defensible primary-state assignment are used. California and
# South Carolina use their state-level rows to avoid local-market double counts.
REGION_TO_STATE = {
    "Albany": "NY", "Atlanta": "GA", "BaltimoreWashington": "MD",
    "BirminghamMontgomery": "AL", "Boise": "ID", "Boston": "MA",
    "BuffaloRochester": "NY", "California": "CA", "Charlotte": "NC",
    "Chicago": "IL", "CincinnatiDayton": "OH", "Columbus": "OH",
    "DallasFtWorth": "TX", "Denver": "CO", "Detroit": "MI",
    "GrandRapids": "MI", "HarrisburgScranton": "PA",
    "HartfordSpringfield": "CT", "Houston": "TX", "Indianapolis": "IN",
    "Jacksonville": "FL", "LasVegas": "NV", "Louisville": "KY",
    "Miami": "FL", "MiamiFtLauderdale": "FL", "Nashville": "TN",
    "NewOrleans": "LA", "NewYork": "NY", "Orlando": "FL",
    "PeoriaSpringfield": "IL", "Philadelphia": "PA",
    "PhoenixTucson": "AZ", "Pittsburgh": "PA", "Portland": "OR",
    "Providence": "RI", "RaleighGreensboro": "NC",
    "RichmondNorfolk": "VA", "Roanoke": "VA", "SouthCarolina": "SC",
    "Seattle": "WA", "Spokane": "WA", "StLouis": "MO",
    "Syracuse": "NY", "Tampa": "FL", "Toledo": "OH", "Wichita": "KS",
}

STATE_NAMES = {
    "AL": "Alabama", "AZ": "Arizona", "CA": "California",
    "CO": "Colorado", "CT": "Connecticut", "FL": "Florida",
    "GA": "Georgia", "ID": "Idaho", "IL": "Illinois", "IN": "Indiana",
    "KS": "Kansas", "KY": "Kentucky", "LA": "Louisiana",
    "MA": "Massachusetts", "MD": "Maryland", "MI": "Michigan",
    "MO": "Missouri", "NC": "North Carolina", "NV": "Nevada",
    "NY": "New York", "OH": "Ohio", "OR": "Oregon",
    "PA": "Pennsylvania", "RI": "Rhode Island", "SC": "South Carolina",
    "TN": "Tennessee", "TX": "Texas", "VA": "Virginia",
    "WA": "Washington",
}

AVOCADO_SCALE = [
    [0.00, "#edf5e7"], [0.22, "#d5e7c8"], [0.45, "#a9cc91"],
    [0.68, "#76aa6e"], [0.84, "#477a4f"], [1.00, "#294832"],
]


def _load_map_data() -> pd.DataFrame:
    """Load the page's required columns and prepare state-level fields."""
    csv_path = Path(__file__).resolve().parents[1] / "avocado.csv"
    data = pd.read_csv(
        csv_path,
        usecols=["date", "average_price", "total_volume", "type", "region"],
    )
    data["date"] = pd.to_datetime(data["date"], format="%d/%m/%Y")
    data["year"] = data["date"].dt.year
    data["state_code"] = data["region"].map(REGION_TO_STATE)
    data = data.dropna(subset=["state_code"]).copy()
    data["weighted_price"] = data["average_price"] * data["total_volume"]
    return data


MAP_DATA = _load_map_data()
AVAILABLE_YEARS = sorted(MAP_DATA["year"].unique().tolist())


def _prepare_client_data() -> dict:
    """Pre-aggregate the small dataset sent to the browser for local updates."""
    grouped = (
        MAP_DATA.groupby(["year", "state_code", "type"], as_index=False)
        .agg(
            weighted_price=("weighted_price", "sum"),
            total_volume=("total_volume", "sum"),
            markets=("region", lambda values: sorted(set(values))),
        )
        .sort_values(["year", "state_code", "type"])
    )
    records = [
        {
            "year": int(row.year),
            "state_code": row.state_code,
            "type": row.type,
            "weighted_price": float(row.weighted_price),
            "total_volume": float(row.total_volume),
            "markets": row.markets,
        }
        for row in grouped.itertuples(index=False)
    ]
    return {
        "records": records,
        "state_names": STATE_NAMES,
        "colorscale": AVOCADO_SCALE,
    }


CLIENT_MAP_DATA = _prepare_client_data()


def _base_layout(figure: go.Figure) -> go.Figure:
    figure.update_geos(
        scope="usa", projection_type="albers usa", bgcolor="rgba(0,0,0,0)",
        showland=True, landcolor="#eef1ec", showlakes=True, lakecolor="#ffffff",
        showsubunits=True, subunitcolor="#ffffff", subunitwidth=1,
    )
    figure.update_layout(
        margin={"l": 0, "r": 12, "t": 8, "b": 0},
        uirevision="state-map",
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        hoverlabel={"bgcolor": "#ffffff", "bordercolor": "#d5e7c8",
                    "font": {"color": "#253028", "size": 13}},
    )
    return figure


def _empty_figure(message: str) -> go.Figure:
    figure = go.Figure()
    figure.add_annotation(
        text=message, x=0.5, y=0.52, xref="paper", yref="paper",
        showarrow=False, font={"size": 15, "color": "#68726a"},
    )
    return _base_layout(figure)


def _build_map(year: int, avocado_types: list[str]) -> go.Figure:
    """Build the choropleth using volume-weighted average prices."""
    if not avocado_types:
        return _empty_figure("Select Organic, Conventional, or both to view prices.")

    selected = MAP_DATA.loc[
        (MAP_DATA["year"] == year) & MAP_DATA["type"].isin(avocado_types)
    ]
    if selected.empty:
        return _empty_figure("No mapped state data is available for this selection.")

    state_data = (
        selected.groupby("state_code", as_index=False)
        .agg(weighted_price=("weighted_price", "sum"),
             total_volume=("total_volume", "sum"),
             market_count=("region", "nunique"))
        .assign(
            average_price=lambda frame: frame.weighted_price / frame.total_volume,
            state_name=lambda frame: frame.state_code.map(STATE_NAMES),
        )
        .sort_values("state_code")
    )

    # A stable scale across years makes year-to-year colour changes comparable.
    scale_data = MAP_DATA.loc[MAP_DATA["type"].isin(avocado_types)]
    scale_prices = scale_data.groupby(["year", "state_code"]).agg(
        weighted_price=("weighted_price", "sum"),
        total_volume=("total_volume", "sum"),
    )
    scale_prices = scale_prices.weighted_price / scale_prices.total_volume

    figure = go.Figure(go.Choropleth(
        locations=state_data.state_code,
        z=state_data.average_price,
        locationmode="USA-states",
        colorscale=AVOCADO_SCALE,
        zmin=float(scale_prices.quantile(0.02)),
        zmax=float(scale_prices.quantile(0.98)),
        marker_line_color="#ffffff",
        marker_line_width=1.2,
        colorbar={
            "title": {"text": "Avg. price ($)", "side": "right"},
            "thickness": 13, "len": 0.72, "outlinewidth": 0,
            "tickprefix": "$", "tickformat": ".2f",
            "tickfont": {"color": "#68726a", "size": 11},
        },
        customdata=state_data[["state_name", "total_volume", "market_count"]],
        hovertemplate=(
            "<b>%{customdata[0]}</b><br>Average price: $%{z:.2f}<br>"
            "Total volume: %{customdata[1]:,.0f}<br>"
            "Mapped markets: %{customdata[2]}<extra></extra>"
        ),
    ))
    return _base_layout(figure)


layout = html.Section([
    dcc.Store(id="map-client-data", data=CLIENT_MAP_DATA),
    html.Div([
        html.P("GEOGRAPHY", className="page-eyebrow"),
        html.H1("US Avocado Price Heat Map", className="page-title"),
        html.P("Compare volume-weighted avocado prices across mapped US states.",
               className="page-description"),
    ], className="page-heading"),
    html.Div([
        html.Div([
            html.Div([
                html.H2("Average price by state", className="map-card-title"),
                html.P("Darker green indicates a higher average price.",
                       className="map-card-subtitle"),
            ]),
            html.Div([
                html.Div("AVOCADO TYPE", className="control-label"),
                dcc.Checklist(
                    id="map-type-selector",
                    options=[{"label": "Organic", "value": "organic"},
                             {"label": "Conventional", "value": "conventional"}],
                    value=["organic", "conventional"], inline=True,
                    className="type-toggle", inputClassName="type-toggle-input",
                    labelClassName="type-toggle-option",
                ),
            ], className="map-type-control"),
        ], className="map-card-header"),
        html.Div([
            html.Div([
                html.Div("YEAR", className="control-label"),
                html.Output(str(AVAILABLE_YEARS[-1]), id="selected-year-label",
                            className="selected-year"),
            ], className="year-control-heading"),
            dcc.Slider(
                id="map-year-slider", min=AVAILABLE_YEARS[0],
                max=AVAILABLE_YEARS[-1], step=1, value=AVAILABLE_YEARS[-1],
                marks={year: str(year) for year in AVAILABLE_YEARS},
                included=False, updatemode="drag",
                tooltip={"placement": "top", "always_visible": False},
            ),
        ], className="year-control"),
        dcc.Graph(
            id="avocado-state-map",
            figure=_build_map(AVAILABLE_YEARS[-1], ["organic", "conventional"]),
            config={"displayModeBar": False, "responsive": True},
            className="state-map-graph",
        ),
        html.P(
            "State values use mapped local markets; grey states do not have a "
            "reliably assignable source region. California and South Carolina "
            "use their state-level source records.",
            className="map-method-note",
        ),
    ], id="state-map-content", className="map-card"),
], className="page")


clientside_callback(
    """
    function(year, avocadoTypes, mapData, currentFigure) {
        const selectedTypes = new Set(avocadoTypes || []);
        const layout = {
            ...(currentFigure?.layout || {}),
            annotations: [],
            uirevision: "state-map"
        };

        const emptyFigure = (message) => ({
            data: [],
            layout: {
                ...layout,
                annotations: [{
                    text: message, x: 0.5, y: 0.52,
                    xref: "paper", yref: "paper", showarrow: false,
                    font: {size: 15, color: "#68726a"}
                }]
            }
        });

        if (!selectedTypes.size) {
            return [
                emptyFigure("Select Organic, Conventional, or both to view prices."),
                String(year)
            ];
        }

        const aggregate = (records) => {
            const states = new Map();
            records.forEach((record) => {
                const state = states.get(record.state_code) || {
                    weightedPrice: 0, totalVolume: 0, markets: new Set()
                };
                state.weightedPrice += record.weighted_price;
                state.totalVolume += record.total_volume;
                record.markets.forEach((market) => state.markets.add(market));
                states.set(record.state_code, state);
            });
            return states;
        };

        const chosenRecords = mapData.records.filter(
            (record) => selectedTypes.has(record.type)
        );
        const yearStates = aggregate(
            chosenRecords.filter((record) => record.year === year)
        );
        if (!yearStates.size) {
            return [
                emptyFigure("No mapped state data is available for this selection."),
                String(year)
            ];
        }

        // Keep the colour range stable while moving between years.
        const scaleGroups = new Map();
        chosenRecords.forEach((record) => {
            const key = `${record.year}|${record.state_code}`;
            const value = scaleGroups.get(key) || {weightedPrice: 0, totalVolume: 0};
            value.weightedPrice += record.weighted_price;
            value.totalVolume += record.total_volume;
            scaleGroups.set(key, value);
        });
        const scalePrices = Array.from(scaleGroups.values())
            .map((value) => value.weightedPrice / value.totalVolume)
            .sort((a, b) => a - b);
        const quantile = (values, q) => {
            const position = (values.length - 1) * q;
            const lower = Math.floor(position);
            const fraction = position - lower;
            return values[lower] + (values[lower + 1] - values[lower]) * fraction
                || values[lower];
        };

        const stateCodes = Array.from(yearStates.keys()).sort();
        const prices = stateCodes.map((code) => {
            const state = yearStates.get(code);
            return state.weightedPrice / state.totalVolume;
        });
        const customdata = stateCodes.map((code) => {
            const state = yearStates.get(code);
            return [mapData.state_names[code], state.totalVolume, state.markets.size];
        });
        const trace = {
            type: "choropleth",
            locations: stateCodes,
            z: prices,
            locationmode: "USA-states",
            colorscale: mapData.colorscale,
            zmin: quantile(scalePrices, 0.02),
            zmax: quantile(scalePrices, 0.98),
            marker: {line: {color: "#ffffff", width: 1.2}},
            colorbar: {
                title: {text: "Avg. price ($)", side: "right"},
                thickness: 13, len: 0.72, outlinewidth: 0,
                tickprefix: "$", tickformat: ".2f",
                tickfont: {color: "#68726a", size: 11}
            },
            customdata: customdata,
            hovertemplate: "<b>%{customdata[0]}</b><br>Average price: $%{z:.2f}<br>" +
                "Total volume: %{customdata[1]:,.0f}<br>" +
                "Mapped markets: %{customdata[2]}<extra></extra>"
        };
        return [{data: [trace], layout: layout}, String(year)];
    }
    """,
    Output("avocado-state-map", "figure"),
    Output("selected-year-label", "children"),
    Input("map-year-slider", "value"),
    Input("map-type-selector", "value"),
    State("map-client-data", "data"),
    State("avocado-state-map", "figure"),
)
