@echo off
REM Quick run script for Secret Hitler LLM Game

echo.
echo ========================================
echo   SECRET HITLER - LLM RESEARCH PROJECT
echo ========================================
echo.

REM Check if virtual environment exists
if not exist "venv\Scripts\activate.bat" (
    echo Creating virtual environment...
    python -m venv venv
    echo.
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Check if .env exists
if not exist ".env" (
    echo WARNING: .env file not found!
    echo Please copy .env.example to .env and configure your Azure OpenAI credentials.
    echo.
    pause
    exit /b 1
)

REM Install/update dependencies
echo Checking dependencies...
pip install -q -r requirements.txt

echo.
echo Starting game...
echo.

REM Run the game
python main.py

echo.
echo.
pause
