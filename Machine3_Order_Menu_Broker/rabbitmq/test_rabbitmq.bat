@echo off
REM ============================================
REM RabbitMQ Connection Test Script
REM ============================================

title RabbitMQ Connection Test

echo.
echo ========================================
echo   RabbitMQ Connection Test
echo ========================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found
    pause
    exit /b 1
)

REM Check RabbitMQ Service
echo [1/4] Checking RabbitMQ service...
sc query RabbitMQ | find "RUNNING" >nul
if errorlevel 1 (
    echo FAILED: RabbitMQ service is not running
    echo Please start it with: net start RabbitMQ
    pause
    exit /b 1
)
echo PASSED: RabbitMQ service is running
echo.

REM Test Python pika module
echo [2/4] Checking pika module...
python -c "import pika" >nul 2>&1
if errorlevel 1 (
    echo FAILED: pika module not installed
    echo Installing now...
    pip install pika==1.3.2
)
echo PASSED: pika module is installed
echo.

REM Test connection to RabbitMQ
echo [3/4] Testing connection to localhost:5672...
python -c "import pika; c=pika.BlockingConnection(pika.ConnectionParameters('localhost')); print('PASSED: Connected successfully'); c.close()" 2>nul
if errorlevel 1 (
    echo FAILED: Cannot connect to RabbitMQ
    echo.
    echo Troubleshooting:
    echo - Ensure RabbitMQ is running: net start RabbitMQ
    echo - Check firewall settings
    echo - Verify RabbitMQ is listening on port 5672
    pause
    exit /b 1
)
echo.

REM Test Management UI
echo [4/4] Checking Management UI...
powershell -Command "(Invoke-WebRequest -Uri http://localhost:15672 -UseBasicParsing -TimeoutSec 5).StatusCode" >nul 2>&1
if errorlevel 1 (
    echo WARNING: Management UI not accessible at http://localhost:15672
    echo Try enabling the plugin: rabbitmq-plugins.bat enable rabbitmq_management
) else (
    echo PASSED: Management UI is accessible at http://localhost:15672
)
echo.

echo ========================================
echo   All Tests Completed!
echo ========================================
echo.
echo Management UI: http://localhost:15672
echo Default credentials: guest / guest
echo.
pause