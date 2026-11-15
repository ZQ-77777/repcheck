@echo off
REM Double-click to start RepCheck on Windows (after installing, see README.md).
cd /d "%~dp0"
if exist ".venv\Scripts\activate.bat" call ".venv\Scripts\activate.bat"
python -m streamlit run app.py
pause
