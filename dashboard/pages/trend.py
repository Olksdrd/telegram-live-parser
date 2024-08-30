import os
import sys
import pandas as pd
import plotly.graph_objs as go

from dash import register_page, html, dcc, callback, Input, Output

sys.path.insert(0, os.getcwd())
from utils.db_helpers import connect_to_mongo  # noqa: E402


client, collection = connect_to_mongo()

df = pd.DataFrame(list(collection.find()))

register_page(
    __name__,
    path='/trend',
    name='Trend',
    title='Word Trends',
    description='Investigate words trend over time.'
)


layout = html.Div([
    dcc.Input(
        id='input-field',
        type='text',
        placeholder='',
        persistence=True,  # remember the choice when switching tabs
        persistence_type='memory'  # clears after refresh
        ),
    dcc.Graph(id='graph', figure={})
])


@callback(
    Output('graph', 'figure'),
    Input('input-field', 'value'))
def plot_trend(word):
    dff = (
        df['Message']
        .str.contains(str(word))
        .groupby(df['Date'].dt.floor('10min'))
        .agg(['sum'])
        # .count()
        .reset_index()
    )

    fig = go.Figure(
        data=go.Scatter(x=dff['Date'],
                        y=dff['sum'],
                        marker_color='indianred',
                        text="counts"
                        ))
    fig.update_layout({
        "title": 'Counts per time',
        "xaxis": {"title": "Time"},
        "yaxis": {"title": "Count"},
        "showlegend": False})

    return fig
