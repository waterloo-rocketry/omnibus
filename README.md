# Omnibus

## Omni-what?

Omnibus is a unified data bus which manages the connection of various data sources (such as DAQ, RLCS, and live telemetry) and sinks (such as plotting software and logging). Basically, it allows us to take data input from a bunch of different sensors, broadcast it over Wi-Fi, and then display/store it in different formats on the receiving end. This is extremely useful during testing (such as cold flows and static fires) when we need real-time data updates from our test rig while being a safe distance away.

## Setup

### Requirements

Python 3.10 or newer is required. For Linux users, a python package with C headers (such as `python3-dev`) is necessary. 

### Installation

1. Clone this repo.
   - If you have git configured with SSH, run `git clone git@github.com:waterloo-rocketry/omnibus.git`
   - If you don't have git configured with SSH (or you're not sure what that means), run `git clone https://github.com/waterloo-rocketry/omnibus.git`
2. Enter the newly-cloned repo with `cd omnibus`
3. Create a virtual environment:
   - First install the virtualenv library: `pip install virtualenv`
   - Create the venv: `python -m venv venv`
4. Activate the virtual environment:
   - For osx/linux: `source venv/bin/activate`
   - For windows: `venv\Scripts\activate`
5. Upgrade pip version: `pip install --upgrade pip`
6. Run `pip install wheel`, which will help install the rest of the packages more quickly
7. Install Python dependencies with `pip install -r requirements.txt`. You'll also need to run that command in each of the following folders:
   - `sources/ni/`
   - `sources/parsley/`
   - `sinks/dashboard/`
   - If you get a permission error, try `pip install --user -r requirements.txt` instead.
8. Install the Omnibus library locally with `pip install -e .`
   - Don't forget the `.`! This allows the sources and sinks (and you) to import Omnibus
9. Initialize the `Parsley` submodule with `git submodule update --init --recursive` and install the library locally with `pip install -e ./parsley`

## Usage

Omnibus works by running sources (to send data), sinks (to receive data) and a server to connect them together.

### Server

Start the Omnibus server by activating your `venv`, then running `python -m omnibus`.

### Sources/Sinks

Depending on your configuration, you'll need to run one or more sources or sinks. Each one is started independently in the same way: `python sources-or-sinks/name/main.py`. For example, you can start the Dashboard by running `python sinks/dashboard/main.py`.

