from datetime import datetime

from django.utils import timezone
from rest_framework import generics, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from core.permissions import IsActiveSeller
from .models import Sale, DailyClosure
from .serializers import SaleSerializer, DailyClosureSerializer


def cancel_sale_or_error(sale, serializer):
    if sale.status != Sale.Status.ACTIVE:
        return Response(
            {"success": False, "message": "La venta ya no esta activa."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    close_datetime = sale.draw_schedule.close_datetime or timezone.make_aware(
        datetime.combine(sale.draw_date, sale.draw_schedule.close_time),
        timezone.get_current_timezone(),
    )
    if timezone.localtime() >= close_datetime:
        return Response(
            {"success": False, "message": "No se puede eliminar la venta porque el sorteo ya cerro."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    from winners.models import WinningResult
    has_result = WinningResult.objects.filter(
        draw=sale.draw,
        draw_schedule=sale.draw_schedule,
        draw_date=sale.draw_date
    ).exists()
    if has_result:
        return Response(
            {"success": False, "message": "No se puede eliminar la venta porque ya se ingresaron los ganadores del sorteo."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    sale.status = Sale.Status.CANCELLED
    sale.save(update_fields=["status"])
    return Response(
        {"success": True, "message": "Venta eliminada correctamente.", "data": serializer(sale).data}
    )


class SaleCreateAPIView(generics.CreateAPIView):
    serializer_class = SaleSerializer
    permission_classes = [IsActiveSeller]

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        return Response({"success": True, "data": response.data}, status=response.status_code)


class MySalesAPIView(generics.ListAPIView):
    serializer_class = SaleSerializer
    permission_classes = [IsActiveSeller]

    def get_queryset(self):
        return Sale.objects.filter(seller=self.request.user.seller_profile).prefetch_related("items")

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        return Response({"success": True, "data": response.data}, status=response.status_code)


class SaleDetailAPIView(generics.RetrieveDestroyAPIView):
    serializer_class = SaleSerializer
    permission_classes = [IsActiveSeller]

    def get_queryset(self):
        return Sale.objects.filter(seller=self.request.user.seller_profile).prefetch_related("items")

    def get_object(self):
        sale = super().get_object()
        if sale.seller_id != self.request.user.seller_profile.id:
            raise PermissionDenied("No puede consultar ventas de otro vendedor.")
        return sale

    def retrieve(self, request, *args, **kwargs):
        response = super().retrieve(request, *args, **kwargs)
        return Response({"success": True, "data": response.data}, status=response.status_code)

    def destroy(self, request, *args, **kwargs):
        sale = self.get_object()
        return cancel_sale_or_error(sale, self.get_serializer)


class SaleCancelAPIView(generics.GenericAPIView):
    serializer_class = SaleSerializer
    permission_classes = [IsActiveSeller]

    def get_queryset(self):
        return Sale.objects.filter(seller=self.request.user.seller_profile).prefetch_related("items")

    def post(self, request, *args, **kwargs):
        sale = self.get_object()
        return cancel_sale_or_error(sale, self.get_serializer)


class DailyClosureCreateAPIView(generics.GenericAPIView):
    serializer_class = DailyClosureSerializer
    permission_classes = [IsActiveSeller]

    def post(self, request, *args, **kwargs):
        seller = request.user.seller_profile
        closure_date_str = request.data.get("closure_date")
        if closure_date_str:
            try:
                closure_date = datetime.strptime(closure_date_str, "%Y-%m-%d").date()
            except ValueError:
                return Response(
                    {"success": False, "message": "Formato de fecha invalido. Use YYYY-MM-DD."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        else:
            closure_date = timezone.localdate()

        active_sales = Sale.objects.filter(seller=seller, draw_date=closure_date, status=Sale.Status.ACTIVE)
        cancelled_sales = Sale.objects.filter(seller=seller, draw_date=closure_date, status=Sale.Status.CANCELLED)

        from django.db.models import Sum
        from decimal import Decimal
        total_sales = active_sales.aggregate(total=Sum("total_amount"))["total"] or Decimal("0")
        total_cancelled = cancelled_sales.aggregate(total=Sum("total_amount"))["total"] or Decimal("0")
        total_cash = total_sales
        sales_count = active_sales.count()
        cancelled_count = cancelled_sales.count()

        closure, created = DailyClosure.objects.update_or_create(
            seller=seller,
            closure_date=closure_date,
            defaults={
                "total_sales": total_sales,
                "total_cancelled": total_cancelled,
                "total_cash": total_cash,
                "sales_count": sales_count,
                "cancelled_count": cancelled_count,
            },
        )

        serializer = self.get_serializer(closure)
        return Response({"success": True, "data": serializer.data}, status=status.HTTP_200_OK)


class DailyClosureListAPIView(generics.ListAPIView):
    serializer_class = DailyClosureSerializer
    permission_classes = [IsActiveSeller]

    def get_queryset(self):
        return DailyClosure.objects.filter(seller=self.request.user.seller_profile)

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        return Response({"success": True, "data": response.data}, status=response.status_code)
