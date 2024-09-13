from dash import Input, Output, callback, dash_table, html, register_page

register_page(
    __name__,
    path="/",
    name="Table",
    title="Telegram Table",
    description="Live table to monitor tg messages.",
)


columns = [
    {"name": "Message", "id": "Message"},
    {"name": "Date", "id": "Date"},
    {"name": "Chat Name", "id": "Chat_Name"},
    # {"name": "Message_ID", "id": "Message_ID"},
]

datatable = dash_table.DataTable(
    id="table",
    columns=columns,
    data=None,
    editable=False,
    cell_selectable=True,  # enables cell copying
    row_deletable=False,
    filter_action="native",
    filter_options={"case": "insensitive"},
    sort_action="native",
    sort_mode="multi",
    style_cell={
        "textAlign": "left",
        # "minWidth": "100px",
        # "width": "100px",
        # "maxWidth": "100px",
        "overflow": "hidden",
        "textOverflow": "ellipsis",
        "maxWidth": 0,
    },
    persistence=False,
    # column widths
    style_cell_conditional=[
        {"if": {"column_id": "Message"}, "width": "50%"},
        # {"if": {"column_id": "Date"}, "width": "20%"},
        # {"if": {"column_id": "Chat_Name"}, "width": "20%"},
        # {"if": {"column_id": "Message_ID"}, "width": "10%"},
    ],
    # vertical scrolling
    page_current=0,
    page_size=100,
    # style_table={
    #     "maxHeight": "500px",
    #     "overflowY": "scroll"
    # },
    # tooltips
    tooltip_delay=0,
    tooltip_duration=None,
    tooltip_data=None,
    css=[
        {
            "selector": ".dash-table-tooltip",
            # "rule": "backgound-color: white",
            "rule": """
        position: absolute;
        top: +0px;
        left: -50px;
        backgound-color: white
        """,
        }
    ],
)


layout = html.Div(
    [html.Div(id="table-div", children=[datatable]), html.Div(id="placeholder")]
)


@callback(
    Output("table", "data"),
    Output("table", "tooltip_data"),
    Input("data-store", "data"),
    prevent_initial_call=False,
)
def get_data(data):

    tooltip_data = [
        {
            column: {"value": str(value), "type": "markdown"}
            for column, value in row.items()
            if column == "Message"
        }
        for row in data
    ]

    return data, tooltip_data
