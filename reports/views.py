from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Count, Sum
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from draws.models import Draw, DrawSchedule
from sales.models import Sale, DailyClosure
from sellers.models import SellerProfile
from winners.models import Winner, WinningResult
from core.models import AuditLog



DAY_LABELS = {
    0: "Lun",
    1: "Mar",
    2: "Mie",
    3: "Jue",
    4: "Vie",
    5: "Sab",
    6: "Dom",
}


def decimal_value(value):
    return float(value or 0)


def format_days(days):
    if not days:
        return "Sin dias"
    if sorted(days) == [0, 1, 2, 3, 4, 5, 6]:
        return "Todos"
    return ", ".join(DAY_LABELS.get(day, str(day)) for day in days)


def format_time(value):
    return value.strftime("%H:%M") if hasattr(value, "strftime") else str(value)[:5]


def apply_date_filters(queryset, request, date_field):
    date_from = request.query_params.get("date_from")
    date_to = request.query_params.get("date_to")
    seller_id = request.query_params.get("seller_id")
    if date_from:
        queryset = queryset.filter(**{f"{date_field}__gte": date_from})
    if date_to:
        queryset = queryset.filter(**{f"{date_field}__lte": date_to})
    if seller_id:
        queryset = queryset.filter(seller_id=seller_id)
    return queryset


class DashboardSummaryAPIView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        today = timezone.localdate()
        today_sales = Sale.objects.filter(draw_date=today, status=Sale.Status.ACTIVE)
        total_sold_today = today_sales.aggregate(total=Sum("total_amount"))["total"]
        total_possible_prizes = Sale.objects.filter(status=Sale.Status.ACTIVE).aggregate(
            total=Sum("total_possible_prize")
        )["total"]
        active_sellers = SellerProfile.objects.filter(is_seller=True, is_active=True, is_blocked=False).count()

        data = {
            "total_sold_today": decimal_value(total_sold_today),
            "total_possible_prizes": decimal_value(total_possible_prizes),
            "estimated_profit": decimal_value(total_sold_today) - decimal_value(total_possible_prizes),
            "active_sellers": active_sellers,
        }
        return Response({"success": True, "data": data})


class DashboardDrawsAPIView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        schedules = DrawSchedule.objects.select_related("draw").order_by("draw__name", "event_name", "close_time")
        data = [
            {
                "id": schedule.id,
                "draw_id": schedule.draw_id,
                "name": schedule.draw.name,
                "event": schedule.event_name,
                "close_time": format_time(schedule.close_time),
                "days": format_days(schedule.days_of_week),
                "days_of_week": schedule.days_of_week,
                "payout_multiplier": decimal_value(schedule.payout_multiplier),
                "is_active": schedule.draw.is_active and schedule.is_active,
            }
            for schedule in schedules
        ]
        return Response({"success": True, "data": data})

    def post(self, request):
        name = str(request.data.get("name", "")).strip()
        event = str(request.data.get("event", "")).strip()
        close_time = request.data.get("close_time")
        days_of_week = request.data.get("days_of_week", [0, 1, 2, 3, 4, 5, 6])
        payout_multiplier = request.data.get("payout_multiplier", 72)
        is_active = bool(request.data.get("is_active", True))

        if not name or not event or not close_time:
            return Response(
                {"success": False, "message": "Nombre, evento y hora de cierre son obligatorios."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        draw, _ = Draw.objects.get_or_create(name=name, defaults={"is_active": is_active})
        draw.is_active = is_active
        draw.save(update_fields=["is_active", "updated_at"])

        schedule = DrawSchedule.objects.create(
            draw=draw,
            event_name=event,
            close_time=close_time,
            days_of_week=days_of_week,
            payout_multiplier=payout_multiplier,
            is_active=is_active,
        )
        return Response(
            {
                "success": True,
                "data": {
                    "id": schedule.id,
                    "draw_id": draw.id,
                    "name": draw.name,
                    "event": schedule.event_name,
                    "close_time": format_time(schedule.close_time),
                    "days": format_days(schedule.days_of_week),
                    "days_of_week": schedule.days_of_week,
                    "payout_multiplier": decimal_value(schedule.payout_multiplier),
                    "is_active": draw.is_active and schedule.is_active,
                },
            },
            status=status.HTTP_201_CREATED,
        )


class DashboardDrawsDetailAPIView(APIView):
    permission_classes = [IsAdminUser]

    def delete(self, request, schedule_id):
        reason = request.data.get("reason", "").strip()
        if not reason:
            return Response(
                {"success": False, "message": "El motivo de eliminación es obligatorio."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            schedule = DrawSchedule.objects.select_related("draw").get(id=schedule_id)
        except DrawSchedule.DoesNotExist:
            return Response(
                {"success": False, "message": "El sorteo no existe."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if Sale.objects.filter(draw_schedule=schedule).exists():
            return Response(
                {"success": False, "message": "No se puede eliminar el sorteo porque ya tiene números vendidos (ventas registradas)."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Get client IP
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0]
        else:
            ip = request.META.get("REMOTE_ADDR")

        # Create audit log
        AuditLog.objects.create(
            user=request.user,
            action="ELIMINACION_SORTEO",
            module="Sorteos",
            ip_address=ip,
            description=f"Sorteo '{schedule.draw.name} - {schedule.event_name}' (ID: {schedule.id}) eliminado. Motivo: {reason}"
        )

        schedule.delete()
        return Response({"success": True, "message": "Sorteo eliminado correctamente."})


class DashboardUsersAPIView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        sellers = SellerProfile.objects.select_related("user").order_by("full_name")
        data = [
            {
                "id": seller.id,
                "user_id": seller.user_id,
                "full_name": seller.full_name,
                "username": seller.user.username,
                "email": seller.user.email,
                "phone": seller.phone,
                "is_active": seller.is_active and seller.user.is_active,
                "is_blocked": seller.is_blocked,
                "perm_sell": seller.perm_sell,
                "perm_sales": seller.perm_sales,
                "perm_winners": seller.perm_winners,
                "perm_closures": seller.perm_closures,
                "created_at": seller.created_at.date().isoformat(),
                "role": "ADMIN" if seller.user.is_staff else "VENDEDOR",
            }
            for seller in sellers
        ]
        return Response({"success": True, "data": data})

    def post(self, request):
        username = str(request.data.get("username", "")).strip()
        password = str(request.data.get("password", "")).strip()
        full_name = str(request.data.get("full_name", "")).strip()
        email = str(request.data.get("email", "")).strip()
        phone = str(request.data.get("phone", "")).strip()
        role = str(request.data.get("role", "VENDEDOR")).strip().upper()

        if not username or not password or not full_name:
            return Response(
                {"success": False, "message": "Usuario, contrasena y nombre son obligatorios."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        User = get_user_model()
        if User.objects.filter(username=username).exists():
            return Response(
                {"success": False, "message": "Ya existe un usuario con ese username."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        is_staff = (role == "ADMIN")
        is_seller = (role == "VENDEDOR")

        perm_sell = request.data.get("perm_sell", True)
        perm_sales = request.data.get("perm_sales", True)
        perm_winners = request.data.get("perm_winners", True)
        perm_closures = request.data.get("perm_closures", True)

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            is_staff=is_staff,
        )
        profile = SellerProfile.objects.create(
            user=user,
            full_name=full_name,
            phone=phone,
            is_seller=is_seller,
            is_active=True,
            is_blocked=False,
            perm_sell=bool(perm_sell),
            perm_sales=bool(perm_sales),
            perm_winners=bool(perm_winners),
            perm_closures=bool(perm_closures),
        )
        return Response(
            {
                "success": True,
                "data": {
                    "id": profile.id,
                    "user_id": user.id,
                    "full_name": profile.full_name,
                    "username": user.username,
                    "email": user.email,
                    "phone": profile.phone,
                    "is_active": profile.is_active and user.is_active,
                    "is_blocked": profile.is_blocked,
                    "perm_sell": profile.perm_sell,
                    "perm_sales": profile.perm_sales,
                    "perm_winners": profile.perm_winners,
                    "perm_closures": profile.perm_closures,
                    "created_at": profile.created_at.date().isoformat(),
                    "role": "ADMIN" if user.is_staff else "VENDEDOR",
                },
            },
            status=status.HTTP_201_CREATED,
        )


class DashboardUserUpdateAPIView(APIView):
    permission_classes = [IsAdminUser]

    def put(self, request, seller_id):
        try:
            seller = SellerProfile.objects.select_related("user").get(id=seller_id)
        except SellerProfile.DoesNotExist:
            return Response(
                {"success": False, "message": "Usuario no encontrado."},
                status=status.HTTP_404_NOT_FOUND,
            )

        full_name = str(request.data.get("full_name", "")).strip()
        username = str(request.data.get("username", "")).strip()
        email = str(request.data.get("email", "")).strip()
        phone = str(request.data.get("phone", "")).strip()
        password = str(request.data.get("password", "")).strip()
        role = str(request.data.get("role", "")).strip().upper()

        if not username or not full_name:
            return Response(
                {"success": False, "message": "Usuario y nombre son obligatorios."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        User = get_user_model()
        if User.objects.filter(username=username).exclude(id=seller.user.id).exists():
            return Response(
                {"success": False, "message": "Ya existe otro usuario con ese username."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        perm_sell = request.data.get("perm_sell")
        perm_sales = request.data.get("perm_sales")
        perm_winners = request.data.get("perm_winners")
        perm_closures = request.data.get("perm_closures")

        # Update User
        seller.user.username = username
        seller.user.email = email
        if password:
            seller.user.set_password(password)
        if role:
            seller.user.is_staff = (role == "ADMIN")
            seller.is_seller = (role == "VENDEDOR")
        
        seller.user.save()

        # Update Profile
        seller.full_name = full_name
        seller.phone = phone
        if perm_sell is not None:
            seller.perm_sell = bool(perm_sell)
        if perm_sales is not None:
            seller.perm_sales = bool(perm_sales)
        if perm_winners is not None:
            seller.perm_winners = bool(perm_winners)
        if perm_closures is not None:
            seller.perm_closures = bool(perm_closures)
        seller.save()

        return Response(
            {
                "success": True,
                "data": {
                    "id": seller.id,
                    "user_id": seller.user.id,
                    "full_name": seller.full_name,
                    "username": seller.user.username,
                    "email": seller.user.email,
                    "phone": seller.phone,
                    "is_active": seller.is_active and seller.user.is_active,
                    "is_blocked": seller.is_blocked,
                    "perm_sell": seller.perm_sell,
                    "perm_sales": seller.perm_sales,
                    "perm_winners": seller.perm_winners,
                    "perm_closures": seller.perm_closures,
                    "created_at": seller.created_at.date().isoformat(),
                    "role": "ADMIN" if seller.user.is_staff else "VENDEDOR",
                },
            }
        )


class DashboardUserBlockAPIView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request, seller_id):
        seller = SellerProfile.objects.get(id=seller_id)
        seller.is_blocked = True
        seller.save(update_fields=["is_blocked", "updated_at"])
        return Response({"success": True, "data": {"id": seller.id, "is_blocked": seller.is_blocked}})


class DashboardUserUnblockAPIView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request, seller_id):
        seller = SellerProfile.objects.get(id=seller_id)
        seller.is_blocked = False
        seller.save(update_fields=["is_blocked", "updated_at"])
        return Response({"success": True, "data": {"id": seller.id, "is_blocked": seller.is_blocked}})


class DashboardUserDeactivateAPIView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request, seller_id):
        seller = SellerProfile.objects.select_related("user").get(id=seller_id)
        seller.is_active = False
        seller.user.is_active = False
        seller.save(update_fields=["is_active", "updated_at"])
        seller.user.save(update_fields=["is_active"])
        return Response({"success": True, "data": {"id": seller.id, "is_active": False}})


class DashboardWinnerResultsAPIView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        results = WinningResult.objects.select_related("draw", "draw_schedule", "created_by")
        data = [
            {
                "id": result.id,
                "date": result.draw_date.isoformat(),
                "draw": result.draw.name,
                "event": result.draw_schedule.event_name,
                "winning_number": result.winning_number,
                "registered_by": result.created_by.get_username(),
                "registered_at": timezone.localtime(result.created_at).strftime("%Y-%m-%d %H:%M"),
            }
            for result in results
        ]
        return Response({"success": True, "data": data})

    @transaction.atomic
    def post(self, request):
        draw_id = request.data.get("draw_id")
        schedule_id = request.data.get("draw_schedule_id")
        draw_date = request.data.get("draw_date")
        winning_number = str(request.data.get("winning_number", "")).strip()
        if winning_number.isdigit() and len(winning_number) == 1:
            winning_number = f"0{winning_number}"

        if not draw_id or not schedule_id or not draw_date or not winning_number:
            return Response(
                {"success": False, "message": "Sorteo, horario, fecha y numero ganador son obligatorios."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        draw = Draw.objects.get(id=draw_id)
        schedule = DrawSchedule.objects.get(id=schedule_id, draw=draw)
        result, _ = WinningResult.objects.get_or_create(
            draw=draw,
            draw_schedule=schedule,
            draw_date=draw_date,
            winning_number=winning_number,
            defaults={"created_by": request.user},
        )

        matching_items = (
            Sale.objects.filter(
                draw=draw,
                draw_schedule=schedule,
                draw_date=draw_date,
                status=Sale.Status.ACTIVE,
                items__number=winning_number,
            )
            .select_related("seller")
            .prefetch_related("items")
        )

        winners_created = 0
        for sale in matching_items:
            for item in sale.items.filter(number=winning_number):
                _, created = Winner.objects.update_or_create(
                    sale_item=item,
                    defaults={
                        "sale": sale,
                        "seller": sale.seller,
                        "buyer_name": sale.buyer_name,
                        "winning_number": winning_number,
                        "amount_bet": item.amount,
                        "prize_amount": item.possible_prize,
                    },
                )
                if created:
                    winners_created += 1

        return Response(
            {
                "success": True,
                "data": {
                    "id": result.id,
                    "date": result.draw_date,
                    "draw": result.draw.name,
                    "event": result.draw_schedule.event_name,
                    "winning_number": result.winning_number,
                    "registered_by": result.created_by.get_username(),
                    "registered_at": timezone.localtime(result.created_at).strftime("%Y-%m-%d %H:%M"),
                    "winners_created": winners_created,
                },
            },
            status=status.HTTP_201_CREATED,
        )


class DashboardWinnerResultsDetailAPIView(APIView):
    permission_classes = [IsAdminUser]

    @transaction.atomic
    def delete(self, request, result_id):
        try:
            result = WinningResult.objects.select_related("draw", "draw_schedule").get(id=result_id)
        except WinningResult.DoesNotExist:
            return Response(
                {"success": False, "message": "El resultado no existe."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Check if any associated winner is paid
        has_paid = Winner.objects.filter(
            sale__draw=result.draw,
            sale__draw_schedule=result.draw_schedule,
            sale__draw_date=result.draw_date,
            winning_number=result.winning_number,
            is_paid=True,
        ).exists()

        if has_paid:
            return Response(
                {
                    "success": False,
                    "message": "No se puede eliminar el resultado porque ya existen números pagados para este sorteo.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Get client IP
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0]
        else:
            ip = request.META.get("REMOTE_ADDR")

        # Log audit
        AuditLog.objects.create(
            user=request.user,
            action="ELIMINACION_RESULTADO_GANADOR",
            module="Ganadores",
            ip_address=ip,
            description=f"Resultado ganador '{result.winning_number}' para '{result.draw.name} - {result.draw_schedule.event_name}' del día {result.draw_date} eliminado.",
        )

        # Delete associated Winners
        Winner.objects.filter(
            sale__draw=result.draw,
            sale__draw_schedule=result.draw_schedule,
            sale__draw_date=result.draw_date,
            winning_number=result.winning_number,
        ).delete()

        # Delete the result
        result.delete()

        return Response({"success": True, "message": "Resultado ganador y ganadores asociados eliminados correctamente."})


class DashboardLiveSalesAPIView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        sales = (
            Sale.objects.select_related("seller", "draw", "draw_schedule")
            .prefetch_related("items")
            .order_by("-sale_datetime")[:100]
        )
        data = [
            {
                "id": sale.id,
                "seller_name": sale.seller.full_name,
                "buyer_name": sale.buyer_name,
                "draw_name": sale.draw.name,
                "event_name": sale.draw_schedule.event_name,
                "draw_date": sale.draw_date,
                "sale_datetime": sale.sale_datetime,
                "total_amount": decimal_value(sale.total_amount),
                "total_possible_prize": decimal_value(sale.total_possible_prize),
                "items_count": sale.items.count(),
                "status": sale.status,
            }
            for sale in sales
        ]
        return Response({"success": True, "data": data})


class DashboardProfitReportAPIView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        sales = apply_date_filters(Sale.objects.filter(status=Sale.Status.ACTIVE), request, "draw_date")
        rows = sales.values("seller_id", "seller__full_name").annotate(
            total_sold=Sum("total_amount"),
            total_prizes=Sum("total_possible_prize"),
            sales_count=Count("id"),
        )
        data = [
            {
                "id": row["seller_id"],
                "seller": row["seller__full_name"],
                "total_sold": decimal_value(row["total_sold"]),
                "total_prizes": decimal_value(row["total_prizes"]),
                "profit": decimal_value(row["total_sold"]) - decimal_value(row["total_prizes"]),
                "sales_count": row["sales_count"],
                "winners_count": Winner.objects.filter(seller_id=row["seller_id"]).count(),
            }
            for row in rows
        ]
        return Response({"success": True, "data": data})


class DashboardWinnersReportAPIView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        winners = apply_date_filters(
            Winner.objects.select_related("seller", "sale", "sale__draw", "sale__draw_schedule"),
            request,
            "sale__draw_date",
        )
        data = [
            {
                "id": winner.id,
                "seller": winner.seller.full_name,
                "buyer": winner.buyer_name,
                "draw": winner.sale.draw.name,
                "event": winner.sale.draw_schedule.event_name,
                "winning_number": winner.winning_number,
                "amount": decimal_value(winner.amount_bet),
                "prize": decimal_value(winner.prize_amount),
                "payment_status": "PAGADO" if winner.is_paid else "PENDIENTE",
            }
            for winner in winners
        ]
        return Response({"success": True, "data": data})


class DashboardDailyClosuresAPIView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        closures = DailyClosure.objects.select_related("seller").order_by("-closure_date", "seller__full_name")
        
        date_str = request.query_params.get("date")
        seller_id = request.query_params.get("seller_id")
        
        if date_str:
            closures = closures.filter(closure_date=date_str)
        if seller_id:
            closures = closures.filter(seller_id=seller_id)
            
        data = [
            {
                "id": closure.id,
                "seller_id": closure.seller.id,
                "seller_name": closure.seller.full_name,
                "closure_date": closure.closure_date.isoformat(),
                "total_sales": decimal_value(closure.total_sales),
                "total_cancelled": decimal_value(closure.total_cancelled),
                "total_cash": decimal_value(closure.total_cash),
                "sales_count": closure.sales_count,
                "cancelled_count": closure.cancelled_count,
                "is_collected": closure.is_collected,
                "created_at": closure.created_at.strftime("%Y-%m-%d %H:%M"),
            }
            for closure in closures
        ]
        return Response({"success": True, "data": data})


class DashboardDailyClosureToggleCollectedAPIView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request, closure_id):
        try:
            closure = DailyClosure.objects.get(id=closure_id)
        except DailyClosure.DoesNotExist:
            return Response(
                {"success": False, "message": "Cierre no encontrado."},
                status=status.HTTP_404_NOT_FOUND,
            )
        
        closure.is_collected = not closure.is_collected
        closure.save(update_fields=["is_collected"])
        return Response({
            "success": True,
            "message": "Estado de cobro actualizado.",
            "data": {
                "id": closure.id,
                "is_collected": closure.is_collected
            }
        })
