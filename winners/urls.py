from django.urls import path

from .views import MyWinnersAPIView, WinnerPayAPIView

urlpatterns = [
    path("my-winners/", MyWinnersAPIView.as_view(), name="winners-my-winners"),
    path("<int:winner_id>/pay/", WinnerPayAPIView.as_view(), name="winners-pay"),
]
