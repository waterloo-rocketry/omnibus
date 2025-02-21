#!/bin/bash

echo "\n----- Upgrading pip -----"
pip install --upgrade pip || exit 1
echo "\n----- Installing tools -----"
pip install wheel || exit 1

# Install requirements
echo "\n----- Installing global requirements -----"
pip install -r requirements.txt || exit 1
echo "\n----- Installing NI source requirements -----"
pip install -r sources/ni/requirements.txt || exit 1
echo "\n----- Installing Parsley source requirements -----"
pip install -r sources/parsley/requirements.txt || exit 1
echo "\n----- Installing Dashboard sink requirements -----"
pip install -r sinks/dashboard/requirements.txt || exit 1
echo "\n----- Installing Interamap sink requirements -----"
pip install -r sinks/interamap/requirements.txt || exit 1
python -m offline_folium || exit 1

# Install local libraries
echo "\n----- Installing Omnibus library -----"
pip install -e . || exit 1
echo "\n----- Installing Parsley library -----"
git submodule update --init --recursive || exit 1
pip install -e ./parsley || exit 1

echo "\n----- Omnibus setup successfully -----"
