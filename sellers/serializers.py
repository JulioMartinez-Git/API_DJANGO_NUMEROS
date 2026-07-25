from rest_framework import serializers
from .models import SellerProfile


class SellerProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = SellerProfile
        fields = [
            "id",
            "full_name",
            "phone",
            "is_seller",
            "is_blocked",
            "is_active",
            "perm_sell",
            "perm_sales",
            "perm_winners",
            "perm_closures",
            "created_at",
            "updated_at",
        ]
