from rest_framework import serializers

from .models import Draw, DrawSchedule


class DrawScheduleSerializer(serializers.ModelSerializer):
    class Meta:
        model = DrawSchedule
        fields = [
            "id",
            "event_name",
            "close_time",
            "close_datetime",
            "days_of_week",
            "payout_multiplier",
            "is_active",
        ]


class DrawSerializer(serializers.ModelSerializer):
    schedules = DrawScheduleSerializer(many=True, read_only=True)

    class Meta:
        model = Draw
        fields = ["id", "name", "description", "is_active", "schedules"]
