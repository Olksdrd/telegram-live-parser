import os
import sys
import pandas as pd
from dash import register_page, dcc, html, Input, Output, dash_table, callback

sys.path.insert(0, os.getcwd())
from utils.db_helpers import connect_to_mongo  # noqa: E402


client, collection = connect_to_mongo()


register_page(__name__, path='/', name='Table')


layout = html.Div([

    html.Div(id='table', children=[]),

    # activated once/week or when page refreshed
    dcc.Interval(id='interval', interval=86400000 * 7, n_intervals=0),

    html.Div(id="placeholder")

])


@callback(
    Output('table', 'children'),
    Input('interval', 'n_intervals'))
def get_data(n_intervals):
    # print(n_intervals)

    df = (
        pd.DataFrame(list(collection.find()))
        .drop('_id', axis=1)
        .sort_values(by='Date', ascending=False)
        # [['Message', 'Date', 'Chat_Name', 'Message_ID']]
    )

    return [
        dash_table.DataTable(
            id='my-table',
            columns=[{
                'name': col,
                'id': col,
            } for col in df.columns],
            data=df.to_dict('records'),
            editable=False,
            row_deletable=True,
            filter_action="native",
            filter_options={"case": "insensitive"},
            sort_action="native",
            sort_mode="multi",
            page_current=0,
            page_size=12,
            style_cell={'textAlign': 'left', 'minWidth': '100px',
                        'width': '100px', 'maxWidth': '100px'},
        )
    ]
