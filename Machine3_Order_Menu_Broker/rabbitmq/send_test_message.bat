@echo off
REM ============================================
REM Send Test Order Notification
REM ============================================

title Send Test Notification

echo.
echo ========================================
echo   Send Test Order Notification
echo ========================================
echo.

cd /d "%~dp0"

python -c "from rabbitmq_config import OrderNotificationProducer; result = OrderNotificationProducer.notify_new_order(order_id=999, customer_name='Test Customer', total_price=1500.00, items_count=3); print('Message sent successfully!' if result else 'Failed to send message')"

if errorlevel 1 (
    echo.
    echo ERROR: Failed to send test message
    echo Please check:
    echo - RabbitMQ is running
    echo - rabbitmq_config.py is in the current directory
    echo - Consumer is running to receive the message
) else (
    echo.
    echo Test message sent successfully!
    echo Check the consumer window for the notification.
)

echo.
pause