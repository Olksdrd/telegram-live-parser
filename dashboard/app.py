import os
import sys
import pandas as pd

from dash import (Dash, html, dcc,
                  callback, Input, Output,
                  page_registry, page_container)
import dash_bootstrap_components as dbc

sys.path.insert(0, os.getcwd())
from utils.db_helpers import connect_to_mongo  # noqa: E402


client, collection = connect_to_mongo()


app = Dash(
    __name__,
    use_pages=True,
    external_stylesheets=[dbc.themes.BOOTSTRAP, dbc.icons.BOOTSTRAP],
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
                        html.Div(page['name'], className='me-1'),
                    ],
                    href=page['path'],
                    active='exact',
                )
                for page in page_registry.values()
            ],
            # vertical=False,
            horizontal='start',
            pills=True,
            className='bg-light',
)

app.layout = dbc.Container([
    dbc.Row([
        dbc.Col(
            tabbar,
            width={'size': 2, 'offset': 0}
        ),

        dbc.Col(
            dbc.Button(
                [html.I(className='bi bi-arrow-clockwise me-2'), 'Refresh'],
                id='refresh-button',
                n_clicks=0,
                className='ms-2',
                color='primary',
                outline=True,
                # active=True
            ),
            width={'size': 2, 'offset': 0}
        )
    ]),

    html.Br(),

    dbc.Row([
        dbc.Col(page_container)
    ]),


    dcc.Store(
        id='data-store',
        data=None,
        storage_type='memory',
        clear_data=True  # ?
    )

], fluid=True)


@callback(
    Output('data-store', 'data'),
    Input('refresh-button', 'n_clicks'),
)
def get_data(n_clicks):
    print('Getting data from database')

    df = (
        pd.DataFrame(list(collection.find()))
        .drop('_id', axis=1)
        .sort_values(by='Date', ascending=False)
        # [['Message', 'Date', 'Chat_Name', 'Message_ID']]
    )

    return df.to_dict('records')


if __name__ == '__main__':
    app.run(
        host='127.0.0.1',
        port='8050',
        debug=True
    )
