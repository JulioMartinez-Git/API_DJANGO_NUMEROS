from django.contrib import admin

from .models import Sale, SaleItem


class SaleItemInline(admin.TabularInline):
    model = SaleItem
    extra = 0
    readonly_fields = ("possible_prize",)


@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ("id", "seller", "buyer_name", "draw", "draw_schedule", "draw_date", "total_amount", "status")
    list_filter = ("status", "draw", "draw_schedule", "draw_date")
    search_fields = ("buyer_name", "seller__full_name", "items__number")
    inlines = [SaleItemInline]


@admin.register(SaleItem)
class SaleItemAdmin(admin.ModelAdmin):
    list_display = ("sale", "number", "amount", "possible_prize")
    search_fields = ("number", "sale__buyer_name")
