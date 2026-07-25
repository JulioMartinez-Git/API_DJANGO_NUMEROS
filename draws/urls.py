from django.urls import path

from .views import AvailableDrawsAPIView

urlpatterns = [
    path("available/", AvailableDrawsAPIView.as_view(), name="draws-available"),
]
