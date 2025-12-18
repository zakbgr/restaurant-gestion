from django.db import models
from django.utils import timezone

# ============================================
# Commande principale
# ============================================
class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'En attente'),
        ('preparing', 'En préparation'),
        ('delivering', 'En cours de livraison'),
        ('completed', 'Terminée'),
        ('cancelled', 'Annulée'),
    ]

    customer_name = models.CharField(max_length=100)
    customer_email = models.EmailField(blank=True, null=True)
    customer_phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):  # ✅ Corrigé : __str__ au lieu de str
        return f"Commande #{self.id} - {self.customer_name}"

    def calculate_total(self):
        """Calcule le total automatiquement à partir des items"""
        total = sum(item.price for item in self.items.all())
        self.total_price = total
        self.save()
        return total


# ============================================
# Détail de la commande (plats commandés)
# ============================================
class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    
    # Store menu item details directly instead of foreign key
    # This avoids cross-service database dependencies
    menu_item_id = models.IntegerField()  # Reference to menu item in menu service
    menu_item_name = models.CharField(max_length=200)
    menu_item_price = models.DecimalField(max_digits=10, decimal_places=2)
    
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)  # menu_item_price * quantity

    def save(self, *args, **kwargs):
        # Calcul automatique du prix total pour cet item
        if not self.price or self.price == 0:
            self.price = self.menu_item_price * self.quantity
        super().save(*args, **kwargs)
        # Mettre à jour le total de la commande
        self.order.calculate_total()

    def __str__(self):  # ✅ Corrigé : __str__ au lieu de str
        return f"{self.quantity} x {self.menu_item_name}"