from django.urls import path
from . import views
from . import health

urlpatterns = [
    # Pages principales
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),
    
    # Menu
    path('menu/', views.menu_list, name='menu_list'),
    
    # Commandes
    path('order/', views.order_create, name='order_create'),
    path('orders/', views.order_list, name='order_list'),
    path('order/<int:order_id>/', views.order_detail, name='order_detail'),
    
    # Health check
    path('health/', health.health_check, name='health'),
]