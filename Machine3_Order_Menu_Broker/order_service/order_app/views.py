from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Order, OrderItem
from .serializers import OrderSerializer, OrderItemSerializer, CreateOrderSerializer
import logging
import sys
import os

# Add parent directory to path for rabbitmq_config import
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Import RabbitMQ producer
try:
    from rabbitmq_config import OrderNotificationProducer
    RABBITMQ_AVAILABLE = True
except ImportError:
    RABBITMQ_AVAILABLE = False
    logging.warning("⚠️ RabbitMQ module not available - notifications disabled")

logger = logging.getLogger(__name__)

# Order ViewSet
class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    
    def get_serializer_class(self):
        """Use different serializers for different actions"""
        if self.action == 'create':
            return CreateOrderSerializer
        return OrderSerializer
    
    def create(self, request, *args, **kwargs):
        """Create a new order with items"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        order = serializer.save()
        
        # Send RabbitMQ notification for new order
        if RABBITMQ_AVAILABLE:
            try:
                items_count = order.items.count()
                success = OrderNotificationProducer.notify_new_order(
                    order_id=order.id,
                    customer_name=order.customer_name,
                    total_price=order.total_price,
                    items_count=items_count
                )
                if success:
                    logger.info(f"✅ RabbitMQ notification sent for new order #{order.id}")
                else:
                    logger.warning(f"⚠️ Failed to send RabbitMQ notification for order #{order.id}")
            except Exception as e:
                logger.error(f"❌ RabbitMQ error: {e}")
        
        # Return the created order
        return Response(
            OrderSerializer(order).data,
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=True, methods=['patch'])
    def update_status(self, request, pk=None):
        """Update order status and send notification"""
        order = self.get_object()
        new_status = request.data.get('status')
        
        if new_status not in dict(Order.STATUS_CHOICES):
            return Response(
                {'error': 'Invalid status'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        old_status = order.status
        order.status = new_status
        order.save()
        
        # Send RabbitMQ notification for status change
        if RABBITMQ_AVAILABLE and old_status != new_status:
            try:
                success = OrderNotificationProducer.notify_order_status_change(
                    order_id=order.id,
                    old_status=old_status,
                    new_status=new_status
                )
                if success:
                    logger.info(f"✅ Status change notification sent for order #{order.id}")
                else:
                    logger.warning(f"⚠️ Failed to send status change notification")
            except Exception as e:
                logger.error(f"❌ RabbitMQ error: {e}")
        
        return Response({
            'message': f'Status updated from {old_status} to {new_status}',
            'order': OrderSerializer(order).data
        })


# OrderItem ViewSet
class OrderItemViewSet(viewsets.ModelViewSet):
    queryset = OrderItem.objects.all()
    serializer_class = OrderItemSerializer