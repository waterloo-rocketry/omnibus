import signal

from plot import Plotter
import config

signal.signal(signal.SIGINT, signal.SIG_DFL)

plotter = Plotter()

if __name__ == '__main__':
    plotter.exec()
