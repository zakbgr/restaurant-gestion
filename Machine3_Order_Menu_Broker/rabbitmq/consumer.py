#!/usr/bin/env python
"""
Order Notification Consumer
Listens for new orders and status changes from RabbitMQ
Run this script to start consuming order notifications
"""
import os
import sys
import django
import logging

# Setup Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'order_service.settings')
django.setup()

from rabbitmq_config import OrderNotificationConsumer, process_order_notification

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('/var/log/order_consumer.log')
    ]
)

logger = logging.getLogger(__name__)


def main():
    """Start the order notification consumer"""
    logger.info("=" * 60)
    logger.info("🚀 Starting Order Notification Consumer")
    logger.info("=" * 60)
    
    consumer = OrderNotificationConsumer()
    
    try:
        consumer.start_consuming(process_order_notification)
    except KeyboardInterrupt:
        logger.info("\n⏹️ Shutting down consumer...")
        consumer.stop_consuming()
    except Exception as e:
        logger.error(f"❌ Consumer error: {e}")
        consumer.stop_consuming()
        sys.exit(1)


if __name__ == '__main__':
    main()