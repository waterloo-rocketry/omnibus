import collections
import datetime
import time
import msgpack
import plotly
import numpy as np
import zmq

#context = zmq.Context()

#receiver = context.socket(zmq.SUB)
#receiver.connect("tcp://localhost:5560") # or whatever url the server is running on
#receiver.setsockopt(zmq.SUBSCRIBE, b"") # subscribe to all messages

#print("Connected to 0MQ server.")

import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import plotly.express as px

import pandas as pd

app = dash.Dash()
dt = [4, 1, 2, 2, 4, 5]
t = [1, 2, 3, 4, 5, 6]

df = pd.DataFrame(
    dict(time=t, data=dt)
)

fig = px.scatter(df, x=t, y=dt)

fig.update_layout(
    title="Test Layout",
    xaxis_title="Time",
    yaxis_title="Data"
)

app.layout = html.Div(children=[
    html.H1(children='Testing Data'),
    
    dcc.Graph(
        id='example-graph',
        figure=fig
    ),

    dcc.Interval(
        id='graph-update',
        interval=1*1000
    )]
)

@app.callback(
    Output('example-graph', component_property='figure'),
    Input('graph-update', 'n_intervals'))
def update_figure(n): 

    t.append(t[-1]+1)
    dt.append(dt[-1]+1)

    fig = px.scatter(df, x=t, y=dt)

    fig.update_layout(transition_duration=500)

    fig.update_layout(
        title="Test Layout",
        xaxis_title="Time",
        yaxis_title="Data"
    )

    return fig


if __name__ == '__main__':
    app.run_server(debug=True)