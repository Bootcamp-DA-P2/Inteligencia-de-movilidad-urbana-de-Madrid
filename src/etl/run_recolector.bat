@echo off

cd /d "%~dp0"

echo Carpeta actual:
cd

echo Activando entorno virtual...
call ..\..\.venv\Scripts\activate.bat

echo Ejecutando recolector...

python recolector_crudo.py >> ..\..\logs\recolector.log 2>&1

echo Codigo salida: %errorlevel%