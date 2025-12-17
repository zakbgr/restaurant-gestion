from django.urls import path, include
from rest_framework import routers
from .views import (
    OrderViewSet,
    CategoryViewSet,
)





from order_app.views import OrderViewSet, OrderItemViewSet


router = routers.DefaultRouter()
router.register(r"order-items", OrderItemViewSet)
router.register(r"orders", OrderViewSet)

urlpatterns = [
    path("api/", include(router.urls)),  # toutes les routes DRF
]