@echo off
python -c "import requests" 2>nul

IF %ERRORLEVEL% NEQ 0 (
    echo Installing requirements...
    pip install -r requirements.txt
) ELSE (
    echo All requirements have already been installed.
)
md result
set /p DUMMY=Press Enter to exit...
@echo on