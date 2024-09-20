@echo off
python src/process.py %1
set /p DUMMY=Press Enter to continue...
@echo on