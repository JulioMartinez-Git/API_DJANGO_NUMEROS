from django.conf import settings
from django.db import models
from draws.models import Draw, DrawSchedule
from sales.models import Sale, SaleItem
from sellers.models import SellerProfile


class WinningResult(models.Model):
    draw = models.ForeignKey(Draw, on_delete=models.PROTECT, related_name="winning_results")
    draw_schedule = models.ForeignKey(DrawSchedule, on_delete=models.PROTECT, related_name="winning_results")
    draw_date = models.DateField()
    winning_number = models.CharField(max_length=10)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="winning_results")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("draw", "draw_schedule", "draw_date", "winning_number")
        indexes = [
            models.Index(fields=["draw", "draw_schedule", "draw_date"]),
            models.Index(fields=["winning_number"]),
        ]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.draw} {self.draw_date} - {self.winning_number}"


class Winner(models.Model):
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name="winners")
    sale_item = models.OneToOneField(SaleItem, on_delete=models.CASCADE, related_name="winner")
    seller = models.ForeignKey(SellerProfile, on_delete=models.PROTECT, related_name="winners")
    buyer_name = models.CharField(max_length=160)
    winning_number = models.CharField(max_length=10)
    amount_bet = models.DecimalField(max_digits=12, decimal_places=2)
    prize_amount = models.DecimalField(max_digits=12, decimal_places=2)
    is_paid = models.BooleanField(default=False)
    paid_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["seller", "is_paid"]),
            models.Index(fields=["winning_number"]),
        ]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.buyer_name} - {self.winning_number}"
