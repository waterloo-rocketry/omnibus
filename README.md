## Omnibus

Omnibus is a unified data bus which manages the connection of various data sources (such as DAQ, RLCS, and live telemetry) and sinks (such as plotting software and logging).

#### Requirements

Python 3.8 or newer is required.

Required Python packages can be installed using `pip install -r requirements.txt`.

#### Installation

The Omnibus library is required to run any of the sources or sinks. To install it:

1. Clone this repo.
    * If you have git configured with SSH, run `git clone git@github.com:waterloo-rocketry/omnibus.git`
    * If you don't have git configured with SSH (or you're not sure what that means), run `git clone https://github.com/waterloo-rocketry/omnibus.git`
2. Enter the newly-cloned repo with `cd omnibus`
3. Run `pip install wheel`, which will help install the rest of the packages more quickly.
4. Install Python dependencies with `pip install -r requirements.txt`. If you get a permissions error, try `pip install --user -r requirements.txt` instead.
5. Install the Omnibus library locally with `pip install -e .`. Don't forget the `.`! This allows the sources and sinks (and you) to import Omnibus.

#### Usage

Omnibus requires a server to connect the sources to the sinks. To run the server, run `python -m omnibus`. You may now independently start the sources and sinks by running something like `python sources/name/main.py`.

*Note:* Sources/sinks may have their own `requirements.txt`.
