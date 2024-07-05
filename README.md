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
5. Run the setup script
   - For osx/linux: `source setup.sh`
   - For windows: `setup.bat` 

## Usage

Omnibus works by running sources (to send data), sinks (to receive data) and a server to connect them together.
The easiest way to run Omnibus is through the launcher script `python launcher.py`. This will open a GUI (or prompt by text if you pass in the `--text` flag) where you can select the sources and sinks to run. You can also manually run the different components of Omnibus using the commands described below.

Known limitation of the launcher script: currently, CLI flags can't be passed to a source/sink so one requiring them (such as `parsley`) need to be run manually.

### Server

Start the Omnibus server by activating your `venv`, then running `python -m omnibus`.

### Sources/Sinks

Depending on your configuration, you'll need to run one or more sources or sinks. Each one is started independently in the same way: `python <sources-or-sinks>/<name>/main.py`. For example, you can start the Dashboard by running `python sinks/dashboard/main.py`.
