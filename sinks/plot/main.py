from omnibus import Receiver
import config
from series import Series
from plot import Plotter

config.setup()  # set up the series we want to plot

receiver = Receiver("")  # subscribe to all channels


def update():  # gets called every frame
    # read all the messages in the queue and no more (zero timeout)
    while msg := receiver.recv_message(0):
        # update whatever series subscribed to this channel
        Series.parse(msg.channel, msg.payload)


plotter = Plotter(Series.series, update)
plotter.exec()
