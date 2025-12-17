from django.urls import path, include
from rest_framework import routers
from .views import (
    home_view,
    menu_list_view,
    cart_view,
    checkout_view,
    order_confirmation_view,
    CategoryViewSet,
    MenuItemViewSet,
)

# Router DRF
router = routers.DefaultRouter()
router.register(r"categories", CategoryViewSet)
router.register(r"menu-items", MenuItemViewSet)

urlpatterns = [
    # URLs des templates
    path('', home_view, name='home'),
    path('menu/', menu_list_view, name='menu-list'),
    path('cart/', cart_view, name='cart'),
    path('checkout/', checkout_view, name='checkout'),
    path('order-confirmation/<int:order_id>/', order_confirmation_view, name='order-confirmation'),

    # URLs API
    path('api/', include(router.urls)),
]
