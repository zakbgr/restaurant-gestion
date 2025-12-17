from django.contrib import admin
from django.urls import path, include
from rest_framework import routers

# Import des ViewSets
from orders.views import OrderViewSet, OrderItemViewSet

# Router DRF
router = routers.DefaultRouter()

router.register(r"orders", OrderViewSet)
router.register(r"order-items", OrderItemViewSet)


# URL patterns
urlpatterns = [
    path("api/", include(router.urls)),  # toutes les routes DRF]
]