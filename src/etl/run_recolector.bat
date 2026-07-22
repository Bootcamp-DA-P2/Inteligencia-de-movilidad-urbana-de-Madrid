@echo off
cd /d "%~dp0"
call .venv\Scripts\activate.bat
python src\etl\recolector_crudo.py >> logs\recolector.log 2>&1