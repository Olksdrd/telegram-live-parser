import os
import sys

import dash_bootstrap_components as dbc
from dash import Dash, Input, Output, callback, dcc, html, page_container, page_registry

sys.path.insert(0, os.getcwd())
from utils.fetch_data import data_fetcher

app = Dash(
    __name__,
    use_pages=True,
    external_stylesheets=[dbc.themes.BOOTSTRAP, dbc.icons.BOOTSTRAP],
    suppress_callback_exceptions=True,
    meta_tags=[
        {"name": "viewport", "content": "width=device-width, initial-scale=1.0"}
    ],
)


tabbar = dbc.Nav(
    [
        dbc.NavLink(
            [
                html.Div(page["name"], className="me-1"),
            ],
            href=page["path"],
            active="exact",
        )
        for page in page_registry.values()
    ],
    # vertical=False,
    horizontal="start",
    pills=True,
    className="bg-light",
)

app.layout = dbc.Container(
    [
        dbc.Row(
            [
                dbc.Col(tabbar, width={"size": 2, "offset": 0}),
                dbc.Col(
                    dbc.Button(
                        [html.I(className="bi bi-arrow-clockwise me-2"), "Refresh"],
                        id="refresh-button",
                        n_clicks=0,
                        className="ms-2",
                        color="primary",
                        outline=True,
                        # active=True
                    ),
                    width={"size": 2, "offset": 0},
                ),
            ]
        ),
        html.Br(),
        dbc.Row([dbc.Col(page_container)]),
        dcc.Store(
            id="data-store", data=None, storage_type="memory", clear_data=True  # ?
        ),
    ],
    fluid=True,
)


@callback(
    Output("data-store", "data"),
    Input("refresh-button", "n_clicks"),
)
def get_data(n_clicks):
    print("Getting data from database")

    return repo.get_data()


if __name__ == "__main__":

    repo = data_fetcher(os.getenv("REPOSITORY_TYPE"))
    repo.connect()

    try:
        app.run(host="0.0.0.0", port="8050", debug=True)
    except KeyboardInterrupt:
        repo.client.close()
        pass
