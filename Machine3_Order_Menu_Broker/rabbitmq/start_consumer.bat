@echo off
REM ============================================
REM RabbitMQ Consumer Startup Script
REM Restaurant Order Notification System
REM ============================================

title RabbitMQ Order Notification Consumer

echo.
echo ========================================
echo   RabbitMQ Consumer - Starting...
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python from https://www.python.org/downloads/
    pause
    exit /b 1
)

REM Check if pika is installed
python -c "import pika" >nul 2>&1
if errorlevel 1 (
    echo ERROR: pika module not found
    echo Installing pika...
    pip install pika==1.3.2
    if errorlevel 1 (
        echo ERROR: Failed to install pika
        pause
        exit /b 1
    )
)

REM Check if RabbitMQ is running
echo Checking RabbitMQ service...
sc query RabbitMQ | find "RUNNING" >nul
if errorlevel 1 (
    echo WARNING: RabbitMQ service is not running
    echo Please start RabbitMQ service first
    echo.
    echo Starting RabbitMQ service...
    net start RabbitMQ
    if errorlevel 1 (
        echo ERROR: Failed to start RabbitMQ service
        echo Please start it manually from Services (services.msc)
        pause
        exit /b 1
    )
    timeout /t 5 >nul
)

echo RabbitMQ service is running
echo.

REM Navigate to project directory
cd /d "%~dp0"

echo Starting consumer...
echo Press Ctrl+C to stop
echo.

REM Run the consumer
python consumer.py

REM If consumer exits
echo.
echo Consumer stopped.
pause
