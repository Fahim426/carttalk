@echo off
echo Setting up localized environment...
set PYTHONDONTWRITEBYTECODE=1
set PYTHONPATH=%~dp0libs;%PYTHONPATH%
echo Starting CartTalk Backend...
python main.py
pause
