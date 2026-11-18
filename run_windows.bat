@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if errorlevel 1 (
  echo Python launcher (py) not found. Install Python 3.10+ first.
  pause
  exit /b 1
)
if not exist .venv\Scripts\python.exe (
  py -3 -m venv .venv
  if errorlevel 1 goto :error
)
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
if errorlevel 1 goto :error
python -m streamlit run app.py
if errorlevel 1 goto :error
exit /b 0
:error
echo Setup or startup failed. Check the error above and see README_VI.md.
pause
exit /b 1
