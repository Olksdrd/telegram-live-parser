from dash import Dash, page_registry, page_container, html
import dash_bootstrap_components as dbc


app = Dash(
    __name__,
    use_pages=True,
    external_stylesheets=[dbc.themes.SPACELAB],
    suppress_callback_exceptions=True,
    meta_tags=[{
        'name': 'viewport',
        'content': 'width=device-width, initial-scale=1.0'
        }]
)


tabbar = dbc.Nav(
            [
                dbc.NavLink(
                    [
                        html.Div(page["name"], className="ms-2"),
                    ],
                    href=page["path"],
                    active="exact",
                )
                for page in page_registry.values()
            ],
            # vertical=False,
            horizontal='start',
            pills=True,
            className="bg-light",
)

app.layout = dbc.Container([
    dbc.Row([
        dbc.Col(tabbar)
    ]),

    html.Br(),

    dbc.Row([
        dbc.Col(page_container)
    ])
], fluid=True)


if __name__ == "__main__":
    app.run(
        host='127.0.0.1',
        port='8050',
        debug=True
    )
