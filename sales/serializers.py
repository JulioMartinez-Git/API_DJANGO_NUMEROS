from datetime import datetime
from decimal import Decimal

from django.db import transaction
from django.utils import timezone
from rest_framework import serializers

from draws.models import DrawSchedule
from .models import Sale, SaleItem, DailyClosure


class SaleItemSerializer(serializers.ModelSerializer):
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=Decimal("0.01"))

    class Meta:
        model = SaleItem
        fields = ["id", "number", "amount", "possible_prize"]
        read_only_fields = ["id", "possible_prize"]

    def validate_number(self, value):
        value = str(value).strip()
        if not value.isdigit():
            raise serializers.ValidationError("El numero debe ser numerico.")
        number = int(value)
        if number < 0 or number > 99:
            raise serializers.ValidationError("El numero debe estar entre 0 y 99.")
        return str(number).zfill(2)


class SaleSerializer(serializers.ModelSerializer):
    items = SaleItemSerializer(many=True)
    seller_name = serializers.CharField(source="seller.full_name", read_only=True)
    draw_name = serializers.CharField(source="draw.name", read_only=True)
    event_name = serializers.CharField(source="draw_schedule.event_name", read_only=True)
    can_cancel = serializers.SerializerMethodField()

    class Meta:
        model = Sale
        fields = [
            "id",
            "seller",
            "seller_name",
            "buyer_name",
            "draw",
            "draw_name",
            "draw_schedule",
            "event_name",
            "draw_date",
            "sale_datetime",
            "total_amount",
            "total_possible_prize",
            "status",
            "can_cancel",
            "items",
        ]
        read_only_fields = [
            "id",
            "seller",
            "seller_name",
            "draw_name",
            "event_name",
            "sale_datetime",
            "total_amount",
            "total_possible_prize",
            "status",
            "can_cancel",
        ]

    def get_can_cancel(self, obj):
        close_datetime = obj.draw_schedule.close_datetime or timezone.make_aware(
            datetime.combine(obj.draw_date, obj.draw_schedule.close_time),
            timezone.get_current_timezone(),
        )
        if timezone.localtime() >= close_datetime:
            return False
            
        from winners.models import WinningResult
        has_result = WinningResult.objects.filter(
            draw=obj.draw,
            draw_schedule=obj.draw_schedule,
            draw_date=obj.draw_date
        ).exists()
        if has_result:
            return False
            
        return obj.status == Sale.Status.ACTIVE

    def validate(self, attrs):
        request = self.context["request"]
        seller = request.user.seller_profile
        if seller.is_blocked or not seller.is_active:
            raise serializers.ValidationError({"code": "USER_BLOCKED", "message": "Usuario bloqueado."})

        items = attrs.get("items", [])
        if not items:
            raise serializers.ValidationError({"items": "La venta debe contener al menos un numero."})
        numbers = [item["number"] for item in items]
        if len(numbers) != len(set(numbers)):
            raise serializers.ValidationError({"items": "No se permiten numeros duplicados en una venta."})

        draw_schedule: DrawSchedule = attrs["draw_schedule"]
        draw = attrs["draw"]
        if not draw.is_active:
            raise serializers.ValidationError({"draw": "El sorteo no esta activo."})
        if not draw_schedule.is_active:
            raise serializers.ValidationError({"draw_schedule": "El horario no esta activo."})
        if draw_schedule.draw_id != draw.id:
            raise serializers.ValidationError({"draw_schedule": "El horario no pertenece al sorteo seleccionado."})

        draw_date = attrs["draw_date"]
        if draw_date.weekday() not in draw_schedule.days_of_week:
            raise serializers.ValidationError({"draw_date": "El sorteo no esta disponible para esta fecha."})

        close_datetime = draw_schedule.close_datetime or timezone.make_aware(
            datetime.combine(draw_date, draw_schedule.close_time),
            timezone.get_current_timezone(),
        )
        if timezone.localtime() >= close_datetime:
            raise serializers.ValidationError({"draw_date": "El sorteo ya cerro y no permite nuevas ventas."})

        return attrs

    @transaction.atomic
    def create(self, validated_data):
        items_data = validated_data.pop("items")
        seller = self.context["request"].user.seller_profile
        payout_multiplier = validated_data["draw_schedule"].payout_multiplier
        sale = Sale.objects.create(seller=seller, **validated_data)

        total_amount = Decimal("0")
        total_possible_prize = Decimal("0")
        for item_data in items_data:
            amount = item_data["amount"]
            possible_prize = amount * payout_multiplier
            SaleItem.objects.create(
                sale=sale,
                number=item_data["number"],
                amount=amount,
                possible_prize=possible_prize,
            )
            total_amount += amount
            total_possible_prize += possible_prize

        sale.total_amount = total_amount
        sale.total_possible_prize = total_possible_prize
        sale.save(update_fields=["total_amount", "total_possible_prize"])
        return sale


class DailyClosureSerializer(serializers.ModelSerializer):
    seller_name = serializers.CharField(source="seller.full_name", read_only=True)
    sales = serializers.SerializerMethodField()

    class Meta:
        model = DailyClosure
        fields = [
            "id",
            "seller",
            "seller_name",
            "closure_date",
            "total_sales",
            "total_cancelled",
            "total_cash",
            "sales_count",
            "cancelled_count",
            "created_at",
            "sales",
        ]
        read_only_fields = [
            "id",
            "seller",
            "seller_name",
            "total_sales",
            "total_cancelled",
            "total_cash",
            "sales_count",
            "cancelled_count",
            "created_at",
            "sales",
        ]

    def get_sales(self, obj):
        sales_qs = Sale.objects.filter(seller=obj.seller, draw_date=obj.closure_date).prefetch_related("items")
        return SaleSerializer(sales_qs, many=True).data
