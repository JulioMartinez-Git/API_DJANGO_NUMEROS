from django.db import models


class Draw(models.Model):
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class DrawSchedule(models.Model):
    draw = models.ForeignKey(Draw, on_delete=models.CASCADE, related_name="schedules")
    event_name = models.CharField(max_length=80)
    close_time = models.TimeField()
    close_datetime = models.DateTimeField(null=True, blank=True)
    days_of_week = models.JSONField(default=list, help_text="0=Lunes, 6=Domingo")
    payout_multiplier = models.DecimalField(max_digits=10, decimal_places=2, default=72)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["event_name", "close_time", "draw__name"]

    def __str__(self):
        return f"{self.draw.name} - {self.event_name}"
