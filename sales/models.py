from decimal import Decimal

from django.db import models
from sellers.models import SellerProfile
from draws.models import Draw, DrawSchedule


class Sale(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Activa"
        CANCELLED = "CANCELLED", "Cancelada"
        CLOSED = "CLOSED", "Cerrada"

    seller = models.ForeignKey(SellerProfile, on_delete=models.PROTECT, related_name="sales")
    buyer_name = models.CharField(max_length=160)
    draw = models.ForeignKey(Draw, on_delete=models.PROTECT, related_name="sales")
    draw_schedule = models.ForeignKey(DrawSchedule, on_delete=models.PROTECT, related_name="sales")
    draw_date = models.DateField()
    sale_datetime = models.DateTimeField(auto_now_add=True)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_possible_prize = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["seller", "draw_date"]),
            models.Index(fields=["draw", "draw_schedule", "draw_date"]),
            models.Index(fields=["status"]),
        ]
        ordering = ["-sale_datetime"]

    def recalculate_totals(self):
        totals = self.items.aggregate(
            amount=models.Sum("amount"),
            prize=models.Sum("possible_prize"),
        )
        self.total_amount = totals["amount"] or Decimal("0")
        self.total_possible_prize = totals["prize"] or Decimal("0")
        self.save(update_fields=["total_amount", "total_possible_prize"])

    def __str__(self):
        return f"Venta #{self.pk} - {self.buyer_name}"


class SaleItem(models.Model):
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name="items")
    number = models.CharField(max_length=10)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    possible_prize = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        indexes = [
            models.Index(fields=["number"]),
        ]
        ordering = ["number"]

    def __str__(self):
        return f"{self.number} - {self.amount}"


class DailyClosure(models.Model):
    seller = models.ForeignKey(SellerProfile, on_delete=models.PROTECT, related_name="closures")
    closure_date = models.DateField()
    total_sales = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_cancelled = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_cash = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    sales_count = models.IntegerField(default=0)
    cancelled_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    is_collected = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(fields=["seller", "closure_date"], name="unique_seller_closure_date")
        ]

    def __str__(self):
        return f"Cierre {self.closure_date} - {self.seller.full_name}"
