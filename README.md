# Omnibus

## Omni-what?

Omnibus is a unified data bus which manages the connection of various data sources (such as DAQ, RLCS, and live telemetry) and sinks (such as plotting software and logging). Basically, it allows us to take data input from a bunch of different sensors, broadcast it over Wi-Fi, and then display/store it in different formats on the receiving end. This is extremely useful during testing (such as cold flows and static fires) when we need real-time data updates from our test rig while being a safe distance away.

![High-level Omnibus data-flow diagram](omnibus-abstract.svg)

## Setup

### Requirements

Python 3.11 is required exact to run Omnibus. For Linux users, a python package with C headers (such as `python3-dev`) is necessary. For Windows users, it's recommended to install and run Omnibus through [Git Bash](https://git-scm.com/download/win) for a smoother Unix-like experience.

Note that the production build of Omnibus targets **Python 3.11**. All code contributions must be compatible with that version. See `CONTRIBUTING.md` for more info.

### Installation

1. Clone this repo
   - If you have git configured with SSH, run `git clone git@github.com:waterloo-rocketry/omnibus.git`
   - If you don't have git configured with SSH (or you're not sure what that means), run `git clone https://github.com/waterloo-rocketry/omnibus.git`
2. Enter the newly-cloned repo with `cd omnibus`
3. Create a virtual environment:
   - First install the virtualenv library: `pip install virtualenv`
   - Create the venv: `python -m venv venv`
4. Activate the virtual environment:
   - For Mac/Linux: `source venv/bin/activate`
   - For Windows using Git Bash: `source venv/Scripts/activate`
5. There are two ways to install Omnibus. The setup script is the easiest method, but if it doesn't work you can manually install the required packages
   1. Setup script:
      - For Mac/Linux or Windows Git Bash: `source setup.sh`
   2. Manual installation:
      - Upgrade pip version: `pip install --upgrade pip`
      - Run `pip install wheel`, which will help install the rest of the packages more quickly
      - Install Python dependencies with `pip install -r requirements.txt`. You'll also need to run that command in each of the following folders:
        - `sources/ni/`
        - `sources/parsley/`
        - `sinks/dashboard/`
        - If you get a permission error, try `pip install --user -r requirements.txt` instead.
      - Install the Omnibus library locally with `pip install -e .`
        - Don't forget the `.`! This allows the sources and sinks (and you) to import Omnibus
      - Initialize the `Parsley` submodule with `git submodule update --init --recursive` and install the library locally with `pip install -e ./parsley`

## Usage

Omnibus works by running sources (to send data), sinks (to receive data) and a server to connect them together.
The easiest way to run Omnibus is through the launcher script `python launcher.py`. This will open a GUI (or prompt by text if you pass in the `--text` flag) where you can select the sources and sinks to run. You can also manually run the different components of Omnibus using the commands described below.

Known limitation of the launcher script: currently, CLI flags can't be passed to a source/sink so one requiring them (such as `parsley`) need to be run manually.

### Server

Start the Omnibus server by activating your `venv`, then running `python -m omnibus`.

### Sources/Sinks

Depending on your configuration, you'll need to run one or more sources or sinks. Each one is started independently in the same way: `python <sources-or-sinks>/<name>/main.py`. For example, you can start the Dashboard by running `python sinks/dashboard/main.py`.

### Theme

Omnibus uses the same theme as your operating system's default theme (light or dark). If you would like to switch themes, consider changing the theme of your system accordingly.
