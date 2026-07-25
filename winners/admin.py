from django.contrib import admin

from .models import Winner, WinningResult


@admin.register(WinningResult)
class WinningResultAdmin(admin.ModelAdmin):
    list_display = ("draw", "draw_schedule", "draw_date", "winning_number", "created_by", "created_at")
    list_filter = ("draw", "draw_schedule", "draw_date")
    search_fields = ("winning_number",)


@admin.register(Winner)
class WinnerAdmin(admin.ModelAdmin):
    list_display = ("seller", "buyer_name", "winning_number", "amount_bet", "prize_amount", "is_paid")
    list_filter = ("is_paid",)
    search_fields = ("buyer_name", "winning_number", "seller__full_name")
