@echo off
REM Simple script to run AlzKB updater on Windows

echo ================================
echo AlzKB Updater
echo ================================
echo.

REM Check if virtual environment exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Install dependencies
echo Installing dependencies...
pip install -q -r requirements.txt

REM Run the updater
echo.
echo Running AlzKB updater...
echo.
cd src
python main.py %*

echo.
echo ================================
echo Update complete!
echo ================================
pause
