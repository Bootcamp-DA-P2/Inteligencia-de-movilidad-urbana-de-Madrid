@echo off

cd /d "%~dp0"

call ..\..\.venv\Scripts\activate.bat

python agregador_horario.py >> ..\..\logs\agregador.log 2>&1

exit /b %errorlevel%