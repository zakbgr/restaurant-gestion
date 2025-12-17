from rest_framework import generics
from .models import Compte
from .serializers import AdminCreateSerializer
from .permissions import IsAdmin

class AdminCreateView(generics.CreateAPIView):
    queryset = Compte.objects.all()
    serializer_class = AdminCreateSerializer
    permission_classes = [IsAdmin]


class AdminDeleteView(generics.DestroyAPIView):
    queryset = Compte.objects.all()
    permission_classes = [IsAdmin]
