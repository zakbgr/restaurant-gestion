"""
RabbitMQ Configuration for Order Notifications
Handles connection and message publishing for order events
"""
import pika
import json
import logging

logger = logging.getLogger(__name__)

# RabbitMQ Configuration
RABBITMQ_HOST = '192.168.1.102'  # Machine3 - same as order/menu services
RABBITMQ_PORT = 5672
RABBITMQ_USER = 'guest'
RABBITMQ_PASSWORD = 'guest'
RABBITMQ_VHOST = '/'

# Queue and Exchange Configuration
ORDER_EXCHANGE = 'order_notifications'
ORDER_QUEUE = 'order_queue'
ORDER_ROUTING_KEY = 'order.new'


class RabbitMQConnection:
    """Singleton RabbitMQ connection manager"""
    _instance = None
    _connection = None
    _channel = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(RabbitMQConnection, cls).__new__(cls)
        return cls._instance

    def connect(self):
        """Establish connection to RabbitMQ"""
        if self._connection and not self._connection.is_closed:
            return self._connection

        try:
            credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASSWORD)
            parameters = pika.ConnectionParameters(
                host=RABBITMQ_HOST,
                port=RABBITMQ_PORT,
                virtual_host=RABBITMQ_VHOST,
                credentials=credentials,
                heartbeat=600,
                blocked_connection_timeout=300
            )
            
            self._connection = pika.BlockingConnection(parameters)
            self._channel = self._connection.channel()
            
            # Declare exchange
            self._channel.exchange_declare(
                exchange=ORDER_EXCHANGE,
                exchange_type='topic',
                durable=True
            )
            
            # Declare queue
            self._channel.queue_declare(
                queue=ORDER_QUEUE,
                durable=True
            )
            
            # Bind queue to exchange
            self._channel.queue_bind(
                exchange=ORDER_EXCHANGE,
                queue=ORDER_QUEUE,
                routing_key=ORDER_ROUTING_KEY
            )
            
            logger.info(f"✅ Connected to RabbitMQ at {RABBITMQ_HOST}:{RABBITMQ_PORT}")
            return self._connection
            
        except Exception as e:
            logger.error(f"❌ Failed to connect to RabbitMQ: {e}")
            return None

    def get_channel(self):
        """Get RabbitMQ channel"""
        if not self._connection or self._connection.is_closed:
            self.connect()
        return self._channel

    def close(self):
        """Close RabbitMQ connection"""
        try:
            if self._channel and not self._channel.is_closed:
                self._channel.close()
            if self._connection and not self._connection.is_closed:
                self._connection.close()
            logger.info("✅ RabbitMQ connection closed")
        except Exception as e:
            logger.error(f"❌ Error closing RabbitMQ connection: {e}")


class OrderNotificationProducer:
    """Producer for sending order notifications"""

    @staticmethod
    def notify_new_order(order_id, customer_name, total_price, items_count):
        """
        Send new order notification to RabbitMQ
        
        Args:
            order_id: Order ID
            customer_name: Customer name
            total_price: Total order price
            items_count: Number of items in order
            
        Returns:
            bool: True if message sent successfully, False otherwise
        """
        connection_manager = RabbitMQConnection()
        channel = connection_manager.get_channel()
        
        if not channel:
            logger.error("❌ No RabbitMQ channel available")
            return False

        try:
            message = {
                'event': 'new_order',
                'order_id': order_id,
                'customer_name': customer_name,
                'total_price': str(total_price),
                'items_count': items_count,
                'timestamp': str(json.dumps({}, default=str))
            }
            
            channel.basic_publish(
                exchange=ORDER_EXCHANGE,
                routing_key=ORDER_ROUTING_KEY,
                body=json.dumps(message),
                properties=pika.BasicProperties(
                    delivery_mode=2,  # Make message persistent
                    content_type='application/json'
                )
            )
            
            logger.info(f"✅ Order notification sent for order #{order_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to send order notification: {e}")
            return False

    @staticmethod
    def notify_order_status_change(order_id, old_status, new_status):
        """
        Send order status change notification
        
        Args:
            order_id: Order ID
            old_status: Previous order status
            new_status: New order status
            
        Returns:
            bool: True if message sent successfully, False otherwise
        """
        connection_manager = RabbitMQConnection()
        channel = connection_manager.get_channel()
        
        if not channel:
            logger.error("❌ No RabbitMQ channel available")
            return False

        try:
            message = {
                'event': 'status_change',
                'order_id': order_id,
                'old_status': old_status,
                'new_status': new_status
            }
            
            channel.basic_publish(
                exchange=ORDER_EXCHANGE,
                routing_key='order.status',
                body=json.dumps(message),
                properties=pika.BasicProperties(
                    delivery_mode=2,
                    content_type='application/json'
                )
            )
            
            logger.info(f"✅ Status change notification sent for order #{order_id}: {old_status} → {new_status}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to send status change notification: {e}")
            return False


class OrderNotificationConsumer:
    """Consumer for processing order notifications"""

    def __init__(self):
        self.connection_manager = RabbitMQConnection()
        self.channel = None

    def start_consuming(self, callback):
        """
        Start consuming messages from order queue
        
        Args:
            callback: Function to call when message is received
        """
        self.channel = self.connection_manager.get_channel()
        
        if not self.channel:
            logger.error("❌ Cannot start consuming: No channel available")
            return

        try:
            self.channel.basic_qos(prefetch_count=1)
            self.channel.basic_consume(
                queue=ORDER_QUEUE,
                on_message_callback=callback,
                auto_ack=False
            )
            
            logger.info(f"✅ Started consuming from {ORDER_QUEUE}")
            logger.info("⏳ Waiting for order notifications...")
            
            self.channel.start_consuming()
            
        except KeyboardInterrupt:
            logger.info("⏹️ Consumer stopped by user")
            self.stop_consuming()
        except Exception as e:
            logger.error(f"❌ Error in consumer: {e}")
            self.stop_consuming()

    def stop_consuming(self):
        """Stop consuming messages"""
        if self.channel:
            self.channel.stop_consuming()
        self.connection_manager.close()
        logger.info("✅ Consumer stopped")


def process_order_notification(ch, method, properties, body):
    """
    Default callback function for processing order notifications
    
    Args:
        ch: Channel
        method: Method
        properties: Properties
        body: Message body
    """
    try:
        message = json.loads(body)
        event_type = message.get('event')
        
        if event_type == 'new_order':
            logger.info(f"📦 New Order #{message.get('order_id')}")
            logger.info(f"   Customer: {message.get('customer_name')}")
            logger.info(f"   Total: {message.get('total_price')} DA")
            logger.info(f"   Items: {message.get('items_count')}")
            
        elif event_type == 'status_change':
            logger.info(f"🔄 Order #{message.get('order_id')} status changed")
            logger.info(f"   {message.get('old_status')} → {message.get('new_status')}")
        
        # Acknowledge message
        ch.basic_ack(delivery_tag=method.delivery_tag)
        logger.info("✅ Message processed and acknowledged")
        
    except json.JSONDecodeError as e:
        logger.error(f"❌ Invalid JSON message: {e}")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
    except Exception as e:
        logger.error(f"❌ Error processing message: {e}")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)