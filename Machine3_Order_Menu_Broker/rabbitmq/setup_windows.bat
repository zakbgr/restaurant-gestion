@echo off
REM ============================================
REM RabbitMQ Setup Script for Windows
REM Restaurant Order Notification System
REM ============================================

title RabbitMQ Setup

echo.
echo ============================================
echo   RabbitMQ Setup for Windows
echo ============================================
echo.

REM Check if running as administrator
net session >nul 2>&1
if errorlevel 1 (
    echo ERROR: This script must be run as Administrator
    echo Right-click and select "Run as administrator"
    pause
    exit /b 1
)

echo Running as Administrator - OK
echo.

REM ============================================
REM Step 1: Check Prerequisites
REM ============================================
echo [Step 1/7] Checking prerequisites...
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed
    echo Please install Python from: https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation
    pause
    exit /b 1
)
echo - Python: OK
python --version

REM Check Erlang
erl -version >nul 2>&1
if errorlevel 1 (
    echo.
    echo ERROR: Erlang is not installed
    echo.
    echo Please install Erlang first:
    echo 1. Visit: https://www.erlang.org/downloads
    echo 2. Download: OTP 26.x Windows 64-bit
    echo 3. Install and restart this script
    pause
    exit /b 1
)
echo - Erlang: OK

REM Check RabbitMQ
sc query RabbitMQ >nul 2>&1
if errorlevel 1 (
    echo.
    echo ERROR: RabbitMQ is not installed
    echo.
    echo Please install RabbitMQ:
    echo 1. Visit: https://www.rabbitmq.com/install-windows.html
    echo 2. Download: rabbitmq-server-3.12.x.exe
    echo 3. Install and restart this script
    pause
    exit /b 1
)
echo - RabbitMQ: OK
echo.

REM ============================================
REM Step 2: Install Python Dependencies
REM ============================================
echo [Step 2/7] Installing Python dependencies...
pip install pika==1.3.2
if errorlevel 1 (
    echo ERROR: Failed to install pika
    pause
    exit /b 1
)
echo - pika installed
echo.

REM ============================================
REM Step 3: Create Directories
REM ============================================
echo [Step 3/7] Creating directories...

if not exist "C:\RabbitMQ\logs" (
    mkdir "C:\RabbitMQ\logs"
    echo - Created C:\RabbitMQ\logs
)

if not exist "%APPDATA%\RabbitMQ" (
    mkdir "%APPDATA%\RabbitMQ"
    echo - Created %APPDATA%\RabbitMQ
)
echo.

REM ============================================
REM Step 4: Configure RabbitMQ
REM ============================================
echo [Step 4/7] Configuring RabbitMQ...

if exist "%~dp0rabbitmq_windows.conf" (
    copy /Y "%~dp0rabbitmq_windows.conf" "%APPDATA%\RabbitMQ\rabbitmq.conf"
    echo - Copied rabbitmq.conf to %APPDATA%\RabbitMQ\
) else (
    echo WARNING: rabbitmq_windows.conf not found
)
echo.

REM ============================================
REM Step 5: Enable Management Plugin
REM ============================================
echo [Step 5/7] Enabling Management Plugin...

set RABBITMQ_SBIN=C:\Program Files\RabbitMQ Server\rabbitmq_server-3.12.14\sbin
if not exist "%RABBITMQ_SBIN%" (
    REM Try to find RabbitMQ installation
    for /d %%i in ("C:\Program Files\RabbitMQ Server\rabbitmq_server-*") do (
        set RABBITMQ_SBIN=%%i\sbin
    )
)

cd /d "%RABBITMQ_SBIN%"
call rabbitmq-plugins.bat enable rabbitmq_management
if errorlevel 1 (
    echo WARNING: Failed to enable management plugin
) else (
    echo - Management plugin enabled
)
echo.

REM ============================================
REM Step 6: Create Application User
REM ============================================
echo [Step 6/7] Creating application user...

call rabbitmqctl.bat add_user restaurant_app restaurant_pass_123 >nul 2>&1
call rabbitmqctl.bat set_user_tags restaurant_app administrator
call rabbitmqctl.bat set_permissions -p / restaurant_app ".*" ".*" ".*"
echo - User 'restaurant_app' created with password 'restaurant_pass_123'
echo.

REM ============================================
REM Step 7: Restart RabbitMQ
REM ============================================
echo [Step 7/7] Restarting RabbitMQ service...

net stop RabbitMQ
timeout /t 3 /nobreak >nul
net start RabbitMQ
if errorlevel 1 (
    echo ERROR: Failed to start RabbitMQ
    pause
    exit /b 1
)
echo - RabbitMQ service restarted
echo.

REM ============================================
REM Configuration Complete
REM ============================================
echo.
echo ============================================
echo   Setup Complete!
echo ============================================
echo.
echo Management UI: http://localhost:15672
echo.
echo Credentials:
echo   Guest User:  guest / guest (localhost only)
echo   Admin User:  restaurant_app / restaurant_pass_123
echo.
echo Next Steps:
echo   1. Open Management UI in browser
echo   2. Run test_rabbitmq.bat to verify installation
echo   3. Run start_consumer.bat to start the consumer
echo   4. Run send_test_message.bat to test messaging
echo.
echo For detailed instructions, see:
echo   WINDOWS_INSTALLATION_GUIDE.md
echo.
pause