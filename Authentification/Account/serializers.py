from rest_framework import serializers
from .models import Compte

class AdminCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Compte
        fields = ['id', 'email', 'password', 'nom', 'prenom']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = Compte.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()
        return user
