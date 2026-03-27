from django.urls import path

from .views import ExportReportView, MonthlyReportView, ReportTaskListView, ReportTaskView, WeeklyReportView

urlpatterns = [
    path("reports/weekly/", WeeklyReportView.as_view(), name="report-weekly"),
    path("reports/monthly/", MonthlyReportView.as_view(), name="report-monthly"),
    path("reports/export/", ExportReportView.as_view(), name="report-export"),
    path("reports/tasks/", ReportTaskListView.as_view(), name="report-task-list"),
    path("reports/tasks/<int:task_id>/", ReportTaskView.as_view(), name="report-task"),
]
