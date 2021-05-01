# Omnibus

This is a prototype implementation of a data bus that reads data from a National Instruments DAQ device, sends it over ZeroMQ (serialized using msgpack), and displays it using a graphing library.

To run, you must first choose which data source and sink to use. If you have an NI box to use as a source, use `ni.py`. Otherwise, use `fakeni.py`. As a data sink, choose one of the `plot_*.py` files. Once you have your files, set the URLs in your source and sink to point to localhost with port 5559 and 5560 respectively. Then, separately run `server.py`, your source, and your sink. The order in which these are started/stopped does not matter and any of them can be stopped and restarted without interfering with the others (except for a loss of data).
