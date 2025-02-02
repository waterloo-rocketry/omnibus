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

for /f "tokens=*" %%g in ('"wmic path win32_serialport get DeviceID | find "COM" "') do set com=%%g
echo found USB debug at %com%

@REM start python -m omnibus
@REM timeout /nobreak /t 5
@REM start python sources\ni\main.py
@REM start python sources\parsley\main.py --format usb %com%
wsl.exe -- tmux new -d -s "OmnibusServer"
wsl.exe -- tmux send-keys -t "OmnibusServer" "python.exe -m omnibus" C-m
timeout /nobreak /t 5
wsl.exe -- tmux new -d -s "NI" "python.exe sources/ni/main.py || sh"
wsl.exe -- tmux new -d -s "Parsley" "python.exe sources/parsley/main.py --format usb %com% || sh"

echo Omnibus Started! If there are any messages stating 'duplicate session', omnibus is already running...
echo To access omnibus output over ssh, login and run 'wsl tmux a -t [name]', where [name] is 'OmnibusServer', 'NI', or 'Parsley'
echo Note that closing these windows will not close omnibus! Run the kill-omnibus.bat script or 'wsl tmux kill-server'!
pause
echo Spawning interactive shells if in remote desktop...
start cmd /c wsl -- tmux a -t "OmnibusServer"
start cmd /c wsl -- tmux a -t "NI"
start cmd /c wsl -- tmux a -t "Parsley"
