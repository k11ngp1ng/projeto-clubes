@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
    py -3 -m venv .venv || goto :erro
)
".venv\Scripts\python.exe" -c "import flask, waitress" >nul 2>&1
if errorlevel 1 (
    ".venv\Scripts\python.exe" -m pip install -r requirements.txt || goto :erro
)
".venv\Scripts\python.exe" app.py
if errorlevel 1 goto :erro
exit /b 0
:erro
echo Verifique a instalacao do Python 3 e as mensagens acima.
pause
exit /b 1
