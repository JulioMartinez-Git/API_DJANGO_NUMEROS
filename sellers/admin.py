from django.contrib import admin

from .models import SellerProfile


@admin.register(SellerProfile)
class SellerProfileAdmin(admin.ModelAdmin):
    list_display = ("full_name", "user", "phone", "is_seller", "is_blocked", "is_active")
    list_filter = ("is_seller", "is_blocked", "is_active")
    search_fields = ("full_name", "user__username", "user__email", "phone")
