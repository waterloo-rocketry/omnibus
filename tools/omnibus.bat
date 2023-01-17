cd /d %USERPROFILE%
cd ./Documents/omnibus



:network_connection_check
netsh interface show interface name="Ethernet" | find "Connect state" | find "Connected" > nul
if %ERRORLEVEL% NEQ 0 (
	echo not connected to network... trying again...
	timeout /nobreak /t 1
	goto :network_connection_check
)
echo got ethernet connection!

start ./venv/Scripts/python.exe -m omnibus
timeout /nobreak /t 5
start ./venv/Scripts/python.exe sources/ni/main.py