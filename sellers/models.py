from django.conf import settings
from django.db import models


class SellerProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="seller_profile")
    full_name = models.CharField(max_length=160)
    phone = models.CharField(max_length=30, blank=True)
    is_seller = models.BooleanField(default=True)
    is_blocked = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    perm_sell = models.BooleanField(default=True)
    perm_sales = models.BooleanField(default=True)
    perm_winners = models.BooleanField(default=True)
    perm_closures = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["full_name"]

    def __str__(self):
        return self.full_name
