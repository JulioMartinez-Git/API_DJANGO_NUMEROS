from rest_framework import serializers

from .models import Winner


class WinnerSerializer(serializers.ModelSerializer):
    draw_name = serializers.CharField(source="sale.draw.name", read_only=True)
    event_name = serializers.CharField(source="sale.draw_schedule.event_name", read_only=True)
    draw_date = serializers.DateField(source="sale.draw_date", read_only=True)

    class Meta:
        model = Winner
        fields = [
            "id",
            "sale",
            "sale_item",
            "buyer_name",
            "draw_name",
            "event_name",
            "draw_date",
            "winning_number",
            "amount_bet",
            "prize_amount",
            "is_paid",
            "paid_at",
            "created_at",
        ]
