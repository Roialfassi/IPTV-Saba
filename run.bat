@echo off
REM Quick start script for Windows

REM Activate virtual environment if it exists
IF EXIST venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
)

REM Run application
python -m app.main

pause
