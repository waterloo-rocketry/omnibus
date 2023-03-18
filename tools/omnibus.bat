@echo off 

cd /d %USERPROFILE%
cd ./Documents/omnibus



:network_connection_check
cls
netsh interface show interface name="Ethernet" | find "Connect state" | find "Connected" > nul
if %ERRORLEVEL% NEQ 0 (
	echo not connected to network... trying again...
	timeout /nobreak /t 1
	goto :network_connection_check
)
for /f "tokens=2,3 delims={,}" %%a in ('"WMIC NICConfig where IPEnabled="True" get DefaultIPGateway /value | find "I" "') do set ip=%%~a
echo found ethernet connection, pinging router: %ip%
ping -n 1 %ip% | find "TTL"
if errorlevel 1 echo no response from router, trying again... && goto :network_connection_check
timeout /nobreak /t 2
for /f "tokens=2,3 delims={,}" %%a in ('"WMIC NICConfig where IPEnabled="True" get DefaultIPGateway /value | find "I" "') do set ip=%%~a
echo found ethernet connection, pinging router: %ip%
ping -n 1 %ip% | find "TTL"
if errorlevel 1 echo no response from router, trying again... && goto :network_connection_check
echo router response good... connected to ethernet!

start python -m omnibus
timeout /nobreak /t 5
start python sources\ni\main.py