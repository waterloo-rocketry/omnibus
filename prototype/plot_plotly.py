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

import pandas as pd

app = dash.Dash()

dt = deque(np.zeros(6*100))
t = deque(np.arange(6*100))

df = pd.DataFrame(dict(time=t, data=dt))

fig = px.line(df, x=t, y=dt)

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
        interval=1*1000 #Millisecond
    )]
)

@app.callback(
    Output('example-graph', component_property='figure'),
    Input('graph-update', 'n_intervals'))
def update_figure(n): 

    #sent = time.time() + 1
    while receiver.poll(1): # Timeout of 1 ms checking for new data
        sent, new = msgpack.unpackb(receiver.recv())
        dt.append(new[0][0]) #new[1..16 sensors][0]    
        dt.popleft()
        #unbundle new

        #for channel, points, line in zip(data, new, lines):
            # Just plot the first data point. Since the server bulk reads 10 samples at
            # once this effectively downsamples to 100 samples/sec
        #    channel.popleft()
        #    channel.append(points[0])
        #    line.set_ydata(channel)
        #count += len(new[0])
        

    fig = px.line(df, x=t, y=dt)

    fig.update_layout(transition_duration=500)

    fig.update_layout(
        title="Test Layout",
        xaxis_title="Time",
        yaxis_title="Data"
    )

    return fig


if __name__ == '__main__':
    app.run_server(debug=True)