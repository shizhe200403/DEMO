from django.urls import path

from .views import AdminOperationLogListView, HealthCheckView, UserNotificationListView, UserNotificationReadAllView, UserNotificationReadView

urlpatterns = [
    path("health/", HealthCheckView.as_view(), name="health-check"),
    path("notifications/", UserNotificationListView.as_view(), name="user-notifications"),
    path("notifications/read-all/", UserNotificationReadAllView.as_view(), name="user-notification-read-all"),
    path("notifications/<int:notification_id>/read/", UserNotificationReadView.as_view(), name="user-notification-read"),
    path("admin/operation-logs/", AdminOperationLogListView.as_view(), name="admin-operation-logs"),
]
