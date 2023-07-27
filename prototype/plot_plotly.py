import collections
from collections import deque
import datetime
import time
import msgpack
import plotly
import numpy as np
import zmq

context = zmq.Context()

receiver = context.socket(zmq.SUB)
receiver.connect("tcp://localhost:5560") # or whatever url the server is running on
receiver.setsockopt(zmq.SUBSCRIBE, b"") # subscribe to all messages

print("Connected to 0MQ server.")

import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

import pandas as pd

app = dash.Dash()

dt = [np.zeros(6) for _ in range(16)]

t = [1,2,3,4,5,6]


fig = make_subplots(
    rows=4, cols=4
)

fig.update_layout(
    title="Test Layout",
    xaxis_title="Time",
    yaxis_title="Data"
)

graph_index = 0
for r in range (1,5):
    for c in range (1,5):
        fig.add_trace(go.Line(x=np.array(t), y=np.array(dt[graph_index])), row=r, col=c)
        graph_index += 1

app.layout = html.Div(children=[
    html.H1(children='Testing Data'),
    
    dcc.Graph(
        id='example-graph',
        figure=fig
    ),

    dcc.Interval(
        id='graph-update',
        interval=1*1000 #Millisecond
    )]
)

@app.callback(
    Output('example-graph', component_property='figure'),
    Input('graph-update', 'n_intervals'))
def update_figure(n): 

    while receiver.poll(1): # Timeout of 1 ms checking for new data
        sent, new = msgpack.unpackb(receiver.recv())
        for i in range (16):
            dt[i] = np.delete(dt[i], 0)
            dt[i] = np.append(dt[i], new[i][0]) #new[1..16 sensors][0] is data  

    graph_number = 0
    for r in range (1,5):
        for c in range (1,5):
            fig.update_traces(go.Line(x=np.array(t), y=np.array(dt[graph_number])), row=r, col=c)
            graph_number += 1
    # can run fig.update_layout here if needed
    return fig


if __name__ == '__main__':
    app.run_server(debug=True)