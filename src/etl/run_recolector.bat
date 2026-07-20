@echo off
cd /d "C:\Users\elena\OneDrive\Escritorio\bootcamp-da-p2\Inteligencia-de-movilidad-urbana-de-Madrid"
call .venv\Scripts\activate.bat
python src\etl\recolector_crudo.py >> logs\recolector.log 2>&1