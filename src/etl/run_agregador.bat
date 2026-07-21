@echo off
cd /d "C:\Users\elena\OneDrive\Escritorio\bootcamp-da-p2\Inteligencia-de-movilidad-urbana-de-Madrid"
call .venv\Scripts\activate.bat
python src\etl\agregador_horario.py >> logs\agregador.log 2>&1