from rest_framework import serializers
from django.contrib.auth import get_user_model
from .services import register_user

User = get_user_model()

class UserListSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'name', 'surname', 'email', 'username']
        # El método get_all() fue removido porque la lógica vive correctamente en views.py y services.py


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('email', 'name', 'surname', 'password', 'username')

    def create(self, validated_data):
        return register_user(validated_data)