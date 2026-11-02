@echo off
rem Double-click on Windows to run HN Screening Room at http://localhost:8765
cd /d "%~dp0"
start "" "http://localhost:8765"
python -m http.server 8765 || py -m http.server 8765
