"""Application entry point for the Avocado dashboard."""
import os
from threading import Timer
import webbrowser
from dash import Dash, dcc, html, page_container, page_registry
app = Dash(
    __name__,
    use_pages=True,
    suppress_callback_exceptions=True,
    
    title="Avocado Insights",
    update_title="Loading…",
)
server = app.server
def build_navigation() -> html.Nav:
    """Build navigation from the pages registered in the pages directory."""
    pages = sorted(page_registry.values(), key=lambda page: page.get("order", 99))
    return html.Nav(
        [
            dcc.Link(
                [
                    html.Span(page["nav_icon"], className="nav-icon"),
                    html.Span(page["name"]),
                ],
                href=page["relative_path"],
                className="nav-link",
            )
            for page in pages
        ],
        className="navigation",
        **{"aria-label": "Primary navigation"},
    )
app.layout = html.Div(
    [
        html.Header(
            [
                html.Div(
                    [
                        html.Span(
                            "A",
                            className="brand-mark",
                            **{"aria-hidden": "true"},
                        ),
                        html.Div(
                            [
                                html.Div("Avocado", className="brand-name"),
                                html.Div("US Market Insights", className="brand-subtitle"),
                            ]
                        ),
                    ],
                    className="brand",
                ),
            ],
            className="app-header",
        ),
        html.Div(
            [
                html.Aside(
                    [
                        html.Div("Explore", className="nav-label"),
                        build_navigation(),
                        html.Div(
                            [
                                html.Div("Dataset", className="sidebar-note-title"),
                                html.P(
                                    "US weekly avocado sales",
                                    className="sidebar-note-text",
                                ),
                            ],
                            className="sidebar-note",
                        ),
                    ],
                    className="sidebar",
                ),
                html.Main(page_container, className="page-container"),
            ],
            className="app-body",
        ),
    ],
    className="app-shell",
)
if __name__ == "__main__":
    local_url = "http://127.0.0.1:8050"
    # Werkzeug starts a parent watcher and a child server process in reload mode.
    # Open the browser only from the watcher so each restart does not open a tab.
    if os.environ.get("WERKZEUG_RUN_MAIN") != "true":
        Timer(1.0, lambda: webbrowser.open(local_url)).start()
    app.run(debug=True, use_reloader=True)