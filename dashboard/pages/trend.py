import pandas as pd
import plotly.graph_objs as go

import dash
from dash import register_page, html, dcc, callback, Input, Output


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
        debounce=True,
        persistence=True,  # remember the choice when switching tabs
        persistence_type='memory'  # clears after refresh
        ),
    dcc.Graph(id='graph', figure={})
])


@callback(
    Output('graph', 'figure'),
    Input('input-field', 'value'),
    Input('data-store', 'data'),
    prevent_initial_call=False
)
def plot_trend(word, data):
    if word:
        df = pd.DataFrame(
            data,
            columns=['Message', 'Date', 'Chat_Name', 'Message_ID']
        )

        df['Date'] = pd.to_datetime(df['Date'])

        dff = (
            df['Message']
            .str.contains(str(word), case=False)
            .groupby(df['Date'].dt.floor('10min'))
            .agg(['sum'])
            .reset_index()
        )

        fig = go.Figure(
            data=go.Scatter(x=dff['Date'],
                            y=dff['sum'],
                            marker_color='indianred',
                            text='counts'
                            ))
        fig.update_layout({
            'title': 'Counts per time',
            'xaxis': {'title': 'Time'},
            'yaxis': {'title': 'Count'},
            'showlegend': False})

        return fig

    elif not word:
        raise dash.exceptions.PreventUpdate
