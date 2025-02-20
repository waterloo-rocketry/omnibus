@echo off
SETLOCAL ENABLEDELAYEDEXPANSION

REM Upgrade pip
echo.
echo ----- Upgrading pip -----
python -m pip install --upgrade pip
IF %ERRORLEVEL% NEQ 0 (
    echo Error upgrading pip.
    exit /b %ERRORLEVEL%
)

REM Install wheel
echo.
echo ----- Installing tools -----
pip install wheel
IF %ERRORLEVEL% NEQ 0 (
    echo Error installing wheel.
    exit /b %ERRORLEVEL%
)

REM Install global requirements
echo.
echo ----- Installing global requirements -----
pip install -r requirements.txt
IF %ERRORLEVEL% NEQ 0 (
    echo Error installing global requirements.
    exit /b %ERRORLEVEL%
)

REM Install NI source requirements
echo.
echo ----- Installing NI source requirements -----
pip install -r sources/ni/requirements.txt
IF %ERRORLEVEL% NEQ 0 (
    echo Error installing NI source requirements.
    exit /b %ERRORLEVEL%
)

REM Install Parsley source requirements
echo.
echo ----- Installing Parsley source requirements -----
pip install -r sources/parsley/requirements.txt
IF %ERRORLEVEL% NEQ 0 (
    echo Error installing Parsley source requirements.
    exit /b %ERRORLEVEL%
)

REM Install Dashboard sink requirements
echo.
echo ----- Installing Dashboard sink requirements -----
pip install -r sinks/dashboard/requirements.txt
IF %ERRORLEVEL% NEQ 0 (
    echo Error installing Dashboard sink requirements.
    exit /b %ERRORLEVEL%
)

REM Install Ineteramap sink requirements
echo.
echo ----- Installing Interamap sink requirements -----
pip install -r sinks/interamap/requirements.txt
python -m offline_folium || exit 1
IF %ERRORLEVEL% NEQ 0 (
    echo Error installing Interamap sink requirements.
    exit /b %ERRORLEVEL%
)

REM Install Omnibus library
echo.
echo ----- Installing Omnibus library -----
pip install -e .
IF %ERRORLEVEL% NEQ 0 (
    echo Error installing Omnibus library.
    exit /b %ERRORLEVEL%
)

REM Install Parsley library
echo.
echo ----- Initializing Git submodules -----
git submodule update --init --recursive
IF %ERRORLEVEL% NEQ 0 (
    echo Error initializing Git submodules.
    exit /b %ERRORLEVEL%
)

echo.
echo ----- Installing Parsley library -----
pip install -e ./parsley
IF %ERRORLEVEL% NEQ 0 (
    echo Error installing Parsley library.
    exit /b %ERRORLEVEL%
)

echo.
echo ----- Omnibus setup successfully -----
exit /b 0
