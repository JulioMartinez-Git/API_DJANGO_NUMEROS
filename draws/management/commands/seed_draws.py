from datetime import time
from decimal import Decimal

from django.core.management.base import BaseCommand

from draws.models import Draw, DrawSchedule


class Command(BaseCommand):
    help = "Crea sorteos y horarios iniciales para el sistema de vendedores."

    def handle(self, *args, **options):
        payout = Decimal("72")
        weekday_all = [0, 1, 2, 3, 4, 5, 6]
        weekend = [5, 6]
        definitions = [
            ("Mañana", time(11, 0), weekday_all, ["Diaria", "Nica", "Salvador"]),
            ("Tarde", time(15, 0), weekday_all, ["Diaria", "Nica"]),
            ("Noche", time(21, 0), weekday_all, ["Diaria", "Nica", "Salvador", "Bolido"]),
            ("Sabado/Domingo", time(15, 0), weekend, ["Santa"]),
        ]

        created = 0
        for event_name, close_time, days, draw_names in definitions:
            for draw_name in draw_names:
                draw, _ = Draw.objects.get_or_create(
                    name=draw_name,
                    defaults={"description": f"Sorteo {draw_name}", "is_active": True},
                )
                _, was_created = DrawSchedule.objects.get_or_create(
                    draw=draw,
                    event_name=event_name,
                    defaults={
                        "close_time": close_time,
                        "days_of_week": days,
                        "payout_multiplier": payout,
                        "is_active": True,
                    },
                )
                if was_created:
                    created += 1

        self.stdout.write(self.style.SUCCESS(f"Horarios creados: {created}"))
