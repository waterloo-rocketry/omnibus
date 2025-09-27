# Omnibus

[![Release](https://img.shields.io/github/v/release/waterloo-rocketry/omnibus)](https://github.com/waterloo-rocketry/omnibus/releases)
[![License](https://img.shields.io/github/license/waterloo-rocketry/omnibus)](LICENSE)
[![Python Version](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads/release/python-3110/)
[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/waterloo-rocketry/omnibus)

## Omni-what?

Omnibus is a unified data bus which manages the connection of various data sources (such as DAQ, RLCS, and live telemetry) and sinks (such as plotting software and logging). Basically, it allows us to take data input from a bunch of different sensors, broadcast it over Wi-Fi, and then display/store it in different formats on the receiving end. This is extremely useful during testing (such as cold flows and static fires) when we need real-time data updates from our test rig while being a safe distance away.

## Setup

### Requirements

**You must have the `uv` Python package manager and builder installed. Visit https://docs.astral.sh/uv/getting-started/installation/ to get started. If you don't know otherwise, choose the "Standalone Installer".**

### Installation

1. Clone this repo
2. Enter the newly-cloned repo with `cd omnibus`
3. In a terminal, run `uv python install`
4. Run `uv sync --locked --all-packages`

### Update

1. Run `git pull`
2. Run `uv sync --locked --all-packages`

## Usage

To use Omnibus typically, you'll need at minimum a server and the dashboard running. You will probably also want to connect it to one or many data sources. Run each in a separate terminal window.

Run the following commands at the base of the omnibus folder.

### Server

`uv run omnibus-server`

### Dashboard

`uv run src/dashboard/main.py`

### Logging

`uv run src/globallog/main.py`

### Other Sources/Sinks

`uv run src/[sources|sinks]/[sink_name]/main.py [args]`

All data sources are located under `src/sources`. The main ones you're going to use are `parsley` for data from onboard avionics boards and `rlcsv3` for connecting to RLCS clientside.

Some additional data sinks are available under `src/sinks`, including `interamap` for mapping GPS data.

## Development Instructions

Follow all of the above setup instructions.
Note that the production build of Omnibus targets **Python 3.11**. All code contributions must be compatible with that version. See `CONTRIBUTING.md` for more info.

1. Make sure you have CPython 3.11 installed either through your system or by running `uv python install`
2. Run `uv sync --all-packages` (this is different from the locked version)
3. To source the venv:
   - MacOS / Linux / Git Bash on Windows: `source .venv/bin/activate`
   - Windows Powershell: `.venv/Scripts/Activate.ps1`
4. Recommended dev environment: VSCode + Python extension. Your venv should be sourced automatically.

Look at the DeepWiki link to get an understanding of the architecture. See `CONTRIBUTING.md` for more info about contributing.
