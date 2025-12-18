import requests
from django.shortcuts import render, redirect
from django.contrib import messages
from django.conf import settings
import json

# Page d'accueil
def home(request):
    return render(request, 'home.html')

# Connexion
def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        try:
            # Appel au service d'authentification
            response = requests.post(
                f"{settings.AUTH_SERVICE_URL}/login/",
                json={'username': username, 'password': password},
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                # Stocker le token JWT dans la session
                request.session['jwt_token'] = data.get('token')
                request.session['user_id'] = data.get('user_id')
                request.session['username'] = username
                messages.success(request, 'Connexion réussie!')
                return redirect('menu_list')
            else:
                messages.error(request, 'Identifiants incorrects')
        except requests.exceptions.RequestException as e:
            messages.error(request, f'Erreur de connexion au service: {str(e)}')
    
    return render(request, 'login.html')

# Déconnexion
def logout_view(request):
    request.session.flush()
    messages.success(request, 'Déconnexion réussie')
    return redirect('home')

# Inscription
def register_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        try:
            response = requests.post(
                f"{settings.AUTH_SERVICE_URL}/register/",
                json={'username': username, 'email': email, 'password': password},
                timeout=5
            )
            
            if response.status_code == 201:
                messages.success(request, 'Inscription réussie! Vous pouvez vous connecter.')
                return redirect('login')
            else:
                messages.error(request, 'Erreur lors de l\'inscription')
        except requests.exceptions.RequestException as e:
            messages.error(request, f'Erreur: {str(e)}')
    
    return render(request, 'register.html')

# Liste des menus
def menu_list(request):
    if 'jwt_token' not in request.session:
        return redirect('login')
    
    try:
        headers = {'Authorization': f"Bearer {request.session['jwt_token']}"}
        response = requests.get(
            f"{settings.MENU_SERVICE_URL}/items/",
            headers=headers,
            timeout=5
        )
        
        if response.status_code == 200:
            menus = response.json()
        else:
            menus = []
            messages.error(request, 'Impossible de charger le menu')
    except requests.exceptions.RequestException as e:
        menus = []
        messages.error(request, f'Erreur: {str(e)}')
    
    return render(request, 'menu_list.html', {'menus': menus})

# Créer une commande
def order_create(request):
    if 'jwt_token' not in request.session:
        return redirect('login')
    
    if request.method == 'POST':
        items = request.POST.getlist('items')  # Liste des IDs d'items
        
        try:
            headers = {'Authorization': f"Bearer {request.session['jwt_token']}"}
            response = requests.post(
                f"{settings.ORDER_SERVICE_URL}/create/",
                json={'items': items, 'user_id': request.session['user_id']},
                headers=headers,
                timeout=5
            )
            
            if response.status_code == 201:
                messages.success(request, 'Commande créée avec succès!')
                return redirect('order_list')
            else:
                messages.error(request, 'Erreur lors de la création de la commande')
        except requests.exceptions.RequestException as e:
            messages.error(request, f'Erreur: {str(e)}')
    
    return redirect('menu_list')

# Liste des commandes
def order_list(request):
    if 'jwt_token' not in request.session:
        return redirect('login')
    
    try:
        headers = {'Authorization': f"Bearer {request.session['jwt_token']}"}
        response = requests.get(
            f"{settings.ORDER_SERVICE_URL}/user/{request.session['user_id']}/",
            headers=headers,
            timeout=5
        )
        
        if response.status_code == 200:
            orders = response.json()
        else:
            orders = []
            messages.error(request, 'Impossible de charger les commandes')
    except requests.exceptions.RequestException as e:
        orders = []
        messages.error(request, f'Erreur: {str(e)}')
    
    return render(request, 'order_list.html', {'orders': orders})

# Détail d'une commande
def order_detail(request, order_id):
    if 'jwt_token' not in request.session:
        return redirect('login')
    
    try:
        headers = {'Authorization': f"Bearer {request.session['jwt_token']}"}
        response = requests.get(
            f"{settings.ORDER_SERVICE_URL}/detail/{order_id}/",
            headers=headers,
            timeout=5
        )
        
        if response.status_code == 200:
            order = response.json()
        else:
            order = None
            messages.error(request, 'Commande introuvable')
    except requests.exceptions.RequestException as e:
        order = None
        messages.error(request, f'Erreur: {str(e)}')
    
    return render(request, 'order_detail.html', {'order': order})