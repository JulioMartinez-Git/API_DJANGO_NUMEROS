from django.urls import path

from .views import (
    DashboardDrawsAPIView,
    DashboardDrawsDetailAPIView,
    DashboardLiveSalesAPIView,
    DashboardProfitReportAPIView,
    DashboardSummaryAPIView,
    DashboardUserBlockAPIView,
    DashboardUserDeactivateAPIView,
    DashboardUserUnblockAPIView,
    DashboardUsersAPIView,
    DashboardWinnerResultsAPIView,
    DashboardWinnerResultsDetailAPIView,
    DashboardWinnersReportAPIView,
    DashboardDailyClosuresAPIView,
    DashboardDailyClosureToggleCollectedAPIView,
    DashboardUserUpdateAPIView,
)

urlpatterns = [
    path("summary/", DashboardSummaryAPIView.as_view(), name="dashboard-summary"),
    path("live-sales/", DashboardLiveSalesAPIView.as_view(), name="dashboard-live-sales"),
    path("profit-report/", DashboardProfitReportAPIView.as_view(), name="dashboard-profit-report"),
    path("winners-report/", DashboardWinnersReportAPIView.as_view(), name="dashboard-winners-report"),
    path("draws/", DashboardDrawsAPIView.as_view(), name="dashboard-draws"),
    path("draws/<int:schedule_id>/", DashboardDrawsDetailAPIView.as_view(), name="dashboard-draws-detail"),
    path("users/", DashboardUsersAPIView.as_view(), name="dashboard-users"),
    path("users/<int:seller_id>/", DashboardUserUpdateAPIView.as_view(), name="dashboard-user-update"),
    path("users/<int:seller_id>/block/", DashboardUserBlockAPIView.as_view(), name="dashboard-user-block"),
    path("users/<int:seller_id>/unblock/", DashboardUserUnblockAPIView.as_view(), name="dashboard-user-unblock"),
    path("users/<int:seller_id>/deactivate/", DashboardUserDeactivateAPIView.as_view(), name="dashboard-user-deactivate"),
    path("winner-results/", DashboardWinnerResultsAPIView.as_view(), name="dashboard-winner-results"),
    path("winner-results/<int:result_id>/", DashboardWinnerResultsDetailAPIView.as_view(), name="dashboard-winner-results-detail"),
    path("closures/", DashboardDailyClosuresAPIView.as_view(), name="dashboard-closures"),
    path("closures/<int:closure_id>/toggle-collected/", DashboardDailyClosureToggleCollectedAPIView.as_view(), name="dashboard-closure-toggle-collected"),
]
