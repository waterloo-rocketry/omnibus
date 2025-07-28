@echo off
cd /d %USERPROFILE%
cd ./Documents/omnibus

wsl.exe -- tmux new -d -s "Logging" "python.exe sinks/globallog/main.py || sh"
echo Logging Started! Please ensure that log file size is increasing steadily.
echo To access globallog CLI, run 'wsl.exe tmux a -t Logging'
pause
echo Spawning interactive shell if in remote desktop...
start cmd /c wsl -- tmux a -t "Logging"
echo If you want to stop logging, run 'tools/towerside-stop-logging.bat' or 'wsl tmux kill-session -t Logging'