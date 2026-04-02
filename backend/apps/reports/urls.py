from django.urls import path

from .views import AdminOperationsOverviewView, ExportReportView, MonthlyReportView, ReportDashboardView, ReportTaskListView, ReportTaskView, WeeklyReportView

urlpatterns = [
    path("reports/dashboard/", ReportDashboardView.as_view(), name="report-dashboard"),
    path("reports/weekly/", WeeklyReportView.as_view(), name="report-weekly"),
    path("reports/monthly/", MonthlyReportView.as_view(), name="report-monthly"),
    path("reports/export/", ExportReportView.as_view(), name="report-export"),
    path("reports/tasks/", ReportTaskListView.as_view(), name="report-task-list"),
    path("reports/tasks/<int:task_id>/", ReportTaskView.as_view(), name="report-task"),
    path("reports/admin/overview/", AdminOperationsOverviewView.as_view(), name="report-admin-overview"),
]
