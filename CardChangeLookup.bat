@echo off
python -c "import requests" 2>nul

IF %ERRORLEVEL% NEQ 0 (
    echo Installing requirements...
    pip install -r requirements.txt
)
python src/process.py
set /p DUMMY=Press Enter to continue...
@echo on