@echo off
cd /d "%~dp0"
call .venv\Scripts\activate.bat
python src\etl\agregador_horario.py >> logs\agregador.log 2>&1