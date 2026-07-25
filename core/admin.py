from django.contrib import admin
from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("created_at", "action", "module", "user", "ip_address")
    list_filter = ("action", "module", "created_at")
    search_fields = ("description", "user__username", "action")

