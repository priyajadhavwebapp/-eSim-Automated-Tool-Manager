@echo off
cd /d "%~dp0"
python src\dashboard.py
if errorlevel 1 pause
