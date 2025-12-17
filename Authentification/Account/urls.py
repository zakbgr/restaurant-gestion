from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

from .views import AdminCreateView, AdminDeleteView

urlpatterns = [
    path('token/', TokenObtainPairView.as_view()),
    path('token/refresh/', TokenRefreshView.as_view()),

    path('admin/create/', AdminCreateView.as_view()),
    path('admin/delete/<int:pk>/', AdminDeleteView.as_view()),
]
