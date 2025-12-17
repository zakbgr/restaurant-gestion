from django.urls import path, include
from rest_framework import routers
from .views import OrderViewSet, OrderItemViewSet

router = routers.DefaultRouter()
router.register(r"orders", OrderViewSet)
router.register(r"order-items", OrderItemViewSet)

urlpatterns = [
    # API routes
    path('api/', include(router.urls)),
]