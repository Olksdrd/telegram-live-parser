from dash import register_page, dcc, html, Input, Output, dash_table, callback


register_page(
    __name__,
    path='/',
    name='Table',
    title='Telegram Table',
    description='Live table to monitor tg messages.'
)


layout = html.Div([

    html.Div(id='table', children=[]),

    # activated once a week or when the page is refreshed
    dcc.Interval(id='interval', interval=86400000 * 7, n_intervals=0),

    html.Div(id="placeholder")

])


@callback(
    Output('table', 'children'),
    Input('data-store', 'data'),
    prevent_initial_call=True)
def get_data(data):

    columns = [
        {'name': 'Message', 'id': 'Message'},
        {'name': 'Date', 'id': 'Date'},
        {'name': 'Chat_Name', 'id': 'Chat_Name'},
        {'name': 'Message_ID', 'id': 'Message_ID'},
    ]

    return [
        dash_table.DataTable(
            id='my-table',
            columns=columns,
            data=data,
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
