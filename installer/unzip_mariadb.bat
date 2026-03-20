@echo off
powershell.exe -NoProfile -NonInteractive -Command "Expand-Archive -Force -Path '%1' -DestinationPath '%2'"
exit /b %errorlevel%
