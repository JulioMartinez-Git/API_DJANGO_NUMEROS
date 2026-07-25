from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db import transaction

from sellers.models import SellerProfile


class Command(BaseCommand):
    help = "Crea o actualiza el vendedor de prueba para integracion Android/API."

    @transaction.atomic
    def handle(self, *args, **options):
        user, created = User.objects.get_or_create(
            username="vendedor1",
            defaults={
                "email": "vendedor1@test.com",
                "first_name": "Vendedor",
                "last_name": "de Prueba",
                "is_active": True,
            },
        )
        user.email = "vendedor1@test.com"
        user.first_name = "Vendedor"
        user.last_name = "de Prueba"
        user.is_active = True
        user.set_password("Vendedor123*")
        user.save()

        profile, _ = SellerProfile.objects.update_or_create(
            user=user,
            defaults={
                "full_name": "Vendedor de Prueba",
                "phone": "00000000",
                "is_seller": True,
                "is_blocked": False,
                "is_active": True,
            },
        )

        action = "creado" if created else "actualizado"
        self.stdout.write(self.style.SUCCESS(f"Usuario vendedor {action}: {user.username}"))
        self.stdout.write(self.style.SUCCESS(f"SellerProfile listo: {profile.full_name}"))
