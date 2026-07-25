from django.utils import timezone
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from core.permissions import IsActiveSeller
from .models import Winner
from .serializers import WinnerSerializer


class MyWinnersAPIView(generics.ListAPIView):
    serializer_class = WinnerSerializer
    permission_classes = [IsActiveSeller]

    def get_queryset(self):
        return Winner.objects.filter(seller=self.request.user.seller_profile)

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        return Response({"success": True, "data": response.data}, status=response.status_code)


class WinnerPayAPIView(APIView):
    permission_classes = [IsActiveSeller]

    def post(self, request, winner_id):
        try:
            winner = Winner.objects.get(id=winner_id, seller=request.user.seller_profile)
        except Winner.DoesNotExist:
            return Response(
                {"success": False, "message": "Ganador no encontrado."},
                status=status.HTTP_404_NOT_FOUND,
            )
        
        if winner.is_paid:
            return Response(
                {"success": False, "message": "Este premio ya fue pagado."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        winner.is_paid = True
        winner.paid_at = timezone.now()
        winner.save(update_fields=["is_paid", "paid_at"])
        
        return Response({
            "success": True,
            "message": "Premio marcado como pagado.",
            "data": WinnerSerializer(winner).data
        })
