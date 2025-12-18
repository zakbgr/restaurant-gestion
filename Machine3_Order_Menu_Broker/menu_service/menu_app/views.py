# menu/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from rest_framework import viewsets
from .models import Category, MenuItem
from .serializers import CategorySerializer, MenuItemSerializer
from .forms import CheckoutForm
import logging,requests

# Import des producers RabbitMQ
##from rabbitmq_config import OrderNotificationProducer

logger = logging.getLogger(__name__)

# ============================================
# API ViewSets (existants)
# ============================================
class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class MenuItemViewSet(viewsets.ModelViewSet):
    queryset = MenuItem.objects.all()
    serializer_class = MenuItemSerializer


# ============================================
# Vues Templates pour les clients
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
    """Passer la commande - AVEC APPEL API à l'Order Service"""
    cart = request.session.get('cart', {})
    
    if not cart:
        messages.error(request, 'Votre panier est vide !')
        return redirect('menu-list')
    
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
            pass
    
    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            # Préparer les données pour l'API Order Service
            order_data = {
                'customer_name': form.cleaned_data['customer_name'],
                'customer_phone': form.cleaned_data['customer_phone'],
                'customer_email': form.cleaned_data['customer_email'],
                'address': form.cleaned_data['address'],
                'items': []
            }
            
            # Ajouter les items
            for item_data in cart_items:
                order_data['items'].append({
                    'menu_item_id': item_data['menu_item'].id,
                    'menu_item_name': item_data['menu_item'].name,
                    'menu_item_price': float(item_data['menu_item'].price),
                    'quantity': item_data['quantity']
                })
            
            try:
                # Appel API à l'Order Service
                # TODO: Remplacer par l'URL réelle de votre Order Service
                response = requests.post(
                    'http://localhost:8001/api/orders/',  # Port de l'order_service
                    json=order_data,
                    timeout=5
                )
                
                if response.status_code == 201:
                    order = response.json()
                    order_id = order['id']
                    
                    # Vider le panier
                    request.session['cart'] = {}
                    request.session.modified = True
                    
                    messages.success(
                        request, 
                        f'✓ Commande #{order_id} passée avec succès ! Merci {order["customer_name"]} !'
                    )
                    return redirect('order-confirmation', order_id=order_id)
                else:
                    messages.error(request, 'Erreur lors de la création de la commande.')
                    logger.error(f"Erreur API Order Service: {response.status_code} - {response.text}")
                    
            except requests.exceptions.RequestException as e:
                messages.error(request, 'Impossible de contacter le service de commandes.')
                logger.error(f"Erreur connexion Order Service: {e}")
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
    try:
        # Récupérer la commande depuis l'Order Service
        response = requests.get(
            f'http://localhost:8001/api/orders/{order_id}/',
            timeout=5
        )
        
        if response.status_code == 200:
            order = response.json()
            context = {
                'order': order,
            }
            return render(request, 'menu/order_confirmation.html', context)
        else:
            messages.error(request, 'Commande non trouvée.')
            return redirect('home')
            
    except requests.exceptions.RequestException as e:
        messages.error(request, 'Impossible de récupérer les détails de la commande.')
        logger.error(f"Erreur récupération commande: {e}")
        return redirect('home')