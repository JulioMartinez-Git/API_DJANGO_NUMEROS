from django.urls import path

from .views import (
    MySalesAPIView,
    SaleCancelAPIView,
    SaleCreateAPIView,
    SaleDetailAPIView,
    DailyClosureCreateAPIView,
    DailyClosureListAPIView,
)

urlpatterns = [
    path("", SaleCreateAPIView.as_view(), name="sales-create"),
    path("my-sales/", MySalesAPIView.as_view(), name="sales-my-sales"),
    path("<int:pk>/cancel/", SaleCancelAPIView.as_view(), name="sales-cancel"),
    path("<int:pk>/", SaleDetailAPIView.as_view(), name="sales-detail"),
    path("closures/", DailyClosureCreateAPIView.as_view(), name="closures-create"),
    path("closures/history/", DailyClosureListAPIView.as_view(), name="closures-history"),
]
