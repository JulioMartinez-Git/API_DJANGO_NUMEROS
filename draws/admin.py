from django.contrib import admin

from .models import Draw, DrawSchedule


class DrawScheduleInline(admin.TabularInline):
    model = DrawSchedule
    extra = 0


@admin.register(Draw)
class DrawAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("name",)
    inlines = [DrawScheduleInline]


@admin.register(DrawSchedule)
class DrawScheduleAdmin(admin.ModelAdmin):
    list_display = ("draw", "event_name", "close_time", "payout_multiplier", "is_active")
    list_filter = ("event_name", "is_active")
    search_fields = ("draw__name", "event_name")
