from datetime import datetime

from django.utils import timezone
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Draw
from .serializers import DrawSerializer


class AvailableDrawsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        draw_date_text = request.query_params.get("draw_date")
        if draw_date_text:
            draw_date = datetime.strptime(draw_date_text, "%Y-%m-%d").date()
        else:
            draw_date = timezone.localdate()

        now = timezone.localtime()
        weekday = draw_date.weekday()
        draws = Draw.objects.filter(
            is_active=True,
            schedules__is_active=True,
            schedules__days_of_week__contains=[weekday],
        ).distinct()

        available = []
        for draw in draws:
            active_schedules = []
            for schedule in draw.schedules.filter(is_active=True):
                if weekday not in schedule.days_of_week:
                    continue
                close_datetime = schedule.close_datetime or timezone.make_aware(
                    datetime.combine(draw_date, schedule.close_time),
                    timezone.get_current_timezone(),
                )
                if close_datetime > now:
                    active_schedules.append(schedule)
            if active_schedules:
                draw._prefetched_objects_cache = {"schedules": active_schedules}
                available.append(draw)

        return Response({"success": True, "data": DrawSerializer(available, many=True).data})
