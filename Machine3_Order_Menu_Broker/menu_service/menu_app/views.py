# menu/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from rest_framework import viewsets
from .models import Category, MenuItem
from .serializers import CategorySerializer, MenuItemSerializer
from .forms import CheckoutForm
import logging

# Import des producers RabbitMQ
##from rabbitmq_config import OrderNotificationProducer

logger = logging.getLogger(__name__)

# ============================================
# API ViewSets
# ============================================
class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class MenuItemViewSet(viewsets.ModelViewSet):
    queryset = MenuItem.objects.all()
    serializer_class = MenuItemSerializer


# ============================================
# Template Views
# ============================================

def home_view(request):
    """Page d'accueil du restaurant"""
    cart = request.session.get('cart', {})
    cart_count = sum(cart.values())
    
    context = {
        'cart_count': cart_count,
    }
    return render(request, 'menu/home.html', context)


def menu_list_view(request):
    """Affiche le menu avec possibilité de filtrer par catégorie"""
    category_slug = request.GET.get('category', 'all')
    categories = Category.objects.all()
    
    if category_slug == 'all':
        menu_items = MenuItem.objects.filter(available=True)
        current_category = 'all'
    else:
        category = get_object_or_404(Category, slug=category_slug)
        menu_items = MenuItem.objects.filter(category=category, available=True)
        current_category = category.slug
    
    if request.method == 'POST':
        menu_item_id = request.POST.get('menu_item_id')
        quantity = int(request.POST.get('quantity', 1))
        
        if 'cart' not in request.session:
            request.session['cart'] = {}
        
        cart = request.session['cart']
        cart[str(menu_item_id)] = cart.get(str(menu_item_id), 0) + quantity
        
        request.session.modified = True
        messages.success(request, '✓ Plat ajouté au panier !')
        return redirect('menu-list')
    
    cart = request.session.get('cart', {})
    cart_count = sum(cart.values())
    
    context = {
        'categories': categories,
        'menu_items': menu_items,
        'current_category': current_category,
        'cart_count': cart_count,
    }
    return render(request, 'menu/menu_list.html', context)


def cart_view(request):
    """Affiche le panier et permet de modifier les quantités"""
    cart = request.session.get('cart', {})
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'update':
            item_id = request.POST.get('item_id')
            quantity = int(request.POST.get('quantity', 0))
            if quantity > 0:
                cart[item_id] = quantity
            else:
                cart.pop(item_id, None)
            request.session['cart'] = cart
            request.session.modified = True
            messages.success(request, 'Panier mis à jour !')
            return redirect('cart')
        
        elif action == 'clear':
            request.session['cart'] = {}
            request.session.modified = True
            messages.success(request, 'Panier vidé !')
            return redirect('cart')
    
    cart_items = []
    total = 0
    for item_id, quantity in cart.items():
        try:
            menu_item = MenuItem.objects.get(id=item_id, available=True)
            subtotal = menu_item.price * quantity
            cart_items.append({
                'menu_item': menu_item,
                'quantity': quantity,
                'subtotal': subtotal
            })
            total += subtotal
        except MenuItem.DoesNotExist:
            cart.pop(item_id, None)
            request.session.modified = True
    
    context = {
        'cart_items': cart_items,
        'total': total,
        'cart_count': sum(cart.values()),
    }
    return render(request, 'menu/cart.html', context)


def checkout_view(request):
    """Passer la commande - AVEC RABBITMQ"""
    cart = request.session.get('cart', {})
    
    if not cart:
        messages.error(request, 'Votre panier est vide !')
        return redirect('menu-list')
    
    cart_items = []
    total = Decimal('0.00')
    
    for item_id, quantity in cart.items():
        try:
            menu_item = MenuItem.objects.get(id=item_id, available=True)
            subtotal = menu_item.price * quantity
            cart_items.append({
                'menu_item': menu_item,
                'quantity': quantity,
                'subtotal': subtotal
            })
            total += subtotal
        except MenuItem.DoesNotExist:
            pass
    
    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            order = Order.objects.create(
                customer_name=form.cleaned_data['customer_name'],
                customer_phone=form.cleaned_data['customer_phone'],
                customer_email=form.cleaned_data['customer_email'],
                status='pending'
            )
            
            for item_data in cart_items:
                OrderItem.objects.create(
                    order=order,
                    menu_item=item_data['menu_item'],
                    quantity=item_data['quantity']
                )
            
            order.calculate_total()
            
            try:
                success = OrderNotificationProducer.notify_new_order(
                    order_id=order.id,
                    customer_name=order.customer_name,
                    total_price=order.total_price,
                    items_count=len(cart_items)
                )
                if success:
                    logger.info(f"✅ Message RabbitMQ envoyé pour commande #{order.id}")
                else:
                    logger.warning(f"⚠️ Échec envoi message RabbitMQ pour commande #{order.id}")
            except Exception as e:
                logger.error(f"❌ Erreur RabbitMQ: {e}")
            
            request.session['cart'] = {}
            request.session.modified = True
            
            messages.success(
                request, 
                f'✓ Commande #{order.id} passée avec succès ! Merci {order.customer_name} !'
            )
            return redirect('order-confirmation', order_id=order.id)
    else:
        form = CheckoutForm()
    
    context = {
        'form': form,
        'cart_items': cart_items,
        'total': total,
        'cart_count': len(cart),
    }
    return render(request, 'menu/checkout.html', context)


def order_confirmation_view(request, order_id):
    """Page de confirmation de commande"""
    order = get_object_or_404(Order, id=order_id)
    
    context = {
        'order': order,
    }
    return render(request, 'menu/order_confirmation.html', context)
