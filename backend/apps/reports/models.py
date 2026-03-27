from django.conf import settings
from django.db import models

from apps.common.models import TimeStampedModel


class ReportTask(TimeStampedModel):
    REPORT_TYPE_CHOICES = [
        ("weekly", "Weekly"),
        ("monthly", "Monthly"),
    ]
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("processing", "Processing"),
        ("completed", "Completed"),
        ("failed", "Failed"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="report_tasks")
    report_type = models.CharField(max_length=32, choices=REPORT_TYPE_CHOICES)
    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default="pending")
    file_url = models.TextField(blank=True, default="")
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    generated_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "report_task"
        ordering = ["-created_at"]

