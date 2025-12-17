from rest_framework import serializers
from .models import Order, OrderItem

# OrderItem Serializer
class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ['id', 'order', 'menu_item_id', 'menu_item_name', 'menu_item_price', 'quantity', 'price']
        read_only_fields = ['id', 'price']

    def validate(self, data):
        # Ensure price is calculated correctly
        if 'menu_item_price' in data and 'quantity' in data:
            data['price'] = data['menu_item_price'] * data['quantity']
        return data


# Order Serializer (for GET requests)
class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = ['id', 'customer_name', 'customer_email', 'customer_phone', 'address', 
                  'status', 'total_price', 'created_at', 'updated_at', 'items']
        read_only_fields = ['id', 'total_price', 'created_at', 'updated_at']


# Create Order with Items Serializer (for POST requests)
class CreateOrderSerializer(serializers.Serializer):
    customer_name = serializers.CharField(max_length=100)
    customer_email = serializers.EmailField(required=False, allow_blank=True)
    customer_phone = serializers.CharField(max_length=20, required=False, allow_blank=True)
    address = serializers.CharField(required=False, allow_blank=True)
    items = serializers.ListField(
        child=serializers.DictField(),
        write_only=True
    )

    def validate_items(self, value):
        """Validate items list"""
        if not value:
            raise serializers.ValidationError("Au moins un item est requis")
        
        for item in value:
            required_fields = ['menu_item_id', 'menu_item_name', 'menu_item_price', 'quantity']
            for field in required_fields:
                if field not in item:
                    raise serializers.ValidationError(f"Le champ '{field}' est requis pour chaque item")
        
        return value

    def create(self, validated_data):
        items_data = validated_data.pop('items')
        
        # Create order
        order = Order.objects.create(**validated_data)
        
        # Create order items
        for item_data in items_data:
            OrderItem.objects.create(
                order=order,
                menu_item_id=item_data['menu_item_id'],
                menu_item_name=item_data['menu_item_name'],
                menu_item_price=item_data['menu_item_price'],
                quantity=item_data['quantity']
            )
        
        return order

    def to_representation(self, instance):
        """Return full order details"""
        return OrderSerializer(instance).data