from dash import Dash, page_registry, page_container, html, dcc


app = Dash(__name__, use_pages=True)


app.layout = html.Div(
    [
        html.Div([
            dcc.Link(page['name']+"  |  ", href=page['path'])
            for page in page_registry.values()
        ]),
        html.Hr(),

        # content of each page
        page_container
    ]
)


if __name__ == "__main__":
    app.run(debug=True)
