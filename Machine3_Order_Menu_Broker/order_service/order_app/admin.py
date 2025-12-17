from django.contrib import admin
from .models import Order, OrderItem

# Inline pour voir les OrderItem directement dans Order
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0  # Ne pas afficher de lignes vides par défaut
    readonly_fields = ('price',)  # prix calculé automatiquement
    fields = ('menu_item_id', 'menu_item_name', 'menu_item_price', 'quantity', 'price')

# Admin pour Order
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer_name', 'customer_phone', 'status', 'total_price', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('customer_name', 'customer_email', 'customer_phone')
    readonly_fields = ('total_price', 'created_at', 'updated_at')
    inlines = [OrderItemInline]
    
    fieldsets = (
        ('Informations Client', {
            'fields': ('customer_name', 'customer_email', 'customer_phone', 'address')
        }),
        ('Statut Commande', {
            'fields': ('status', 'total_price')
        }),
        ('Dates', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

# Admin pour OrderItem (optionnel, pour vue séparée)
@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'order', 'menu_item_name', 'quantity', 'menu_item_price', 'price')
    list_filter = ('order',)
    search_fields = ('menu_item_name', 'order__customer_name')
    readonly_fields = ('price',)