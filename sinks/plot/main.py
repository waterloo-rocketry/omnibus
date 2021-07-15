import signal

from omnibus import Receiver
import config
from plot import Plotter

signal.signal(signal.SIGINT, signal.SIG_DFL)

config.setup()

receiver = Receiver("")
plotter = Plotter(receiver)

if __name__ == '__main__':
    plotter.exec()
