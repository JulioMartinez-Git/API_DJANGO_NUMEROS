from django.contrib.auth.models import User
from rest_framework import serializers
from sellers.serializers import SellerProfileSerializer


class UserSerializer(serializers.ModelSerializer):
    seller = SellerProfileSerializer(source="seller_profile", read_only=True)

    class Meta:
        model = User
        fields = ["id", "username", "email", "first_name", "last_name", "is_active", "seller"]


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)
