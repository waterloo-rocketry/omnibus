# Omnibus

This is a prototype implementation of a data bus that reads data from a National Instruments DAQ device, sends it over ZeroMQ, and displays it using matplotlib.

To run, set the URLs in `ni.py` and `plot.py` to point to where you are running `server.py` and separately run all of `server.py`, `plot.py` and `ni.py`. The order in which these are started/stopped does not matter and any of them can be stopped and restarted without interfering with the others (except for a loss of data).
