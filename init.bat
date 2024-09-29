@echo off
python --version >nul 2>&1
if %errorlevel%==0 (
    set PYTHON_CMD=python
    goto :run
)

python3 --version >nul 2>&1
if %errorlevel%==0 (
    set PYTHON_CMD=python3
    goto :run
)

py --version >nul 2>&1
if %errorlevel%==0 (
    set PYTHON_CMD=py
    goto :run
)

echo Python is not installed or not in PATH.
goto :eof

:run
%PYTHON_CMD% -c "import requests" 2>nul

IF %ERRORLEVEL% NEQ 0 (
    echo Installing requirements...
    pip install -r requirements.txt
) ELSE (
    echo All requirements have already been installed.
)
md result
set /p DUMMY=Press Enter to exit...
@echo on