from django.conf import settings
from django.db import models

from apps.common.models import TimeStampedModel


class Post(TimeStampedModel):
    STATUS_CHOICES = [
        ("published", "Published"),
        ("archived", "Archived"),
    ]
    AUDIT_STATUS_CHOICES = [
        ("pending", "Pending"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="posts")
    title = models.CharField(max_length=255)
    content = models.TextField()
    cover_image_url = models.TextField(blank=True, default="")
    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default="published")
    audit_status = models.CharField(max_length=32, choices=AUDIT_STATUS_CHOICES, default="pending")

    class Meta:
        db_table = "post"
        ordering = ["-created_at"]


class PostComment(TimeStampedModel):
    STATUS_CHOICES = [
        ("visible", "Visible"),
        ("hidden", "Hidden"),
    ]

    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="comments")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="post_comments")
    content = models.TextField()
    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default="visible")

    class Meta:
        db_table = "post_comment"
        ordering = ["-created_at"]


class ContentReport(TimeStampedModel):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("processed", "Processed"),
        ("rejected", "Rejected"),
    ]

    reporter = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="content_reports")
    target_type = models.CharField(max_length=32)
    target_id = models.BigIntegerField()
    reason = models.TextField()
    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default="pending")
    processed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="processed_reports",
    )
    processed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "content_report"
        ordering = ["-created_at"]

