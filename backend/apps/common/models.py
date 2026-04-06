from django.conf import settings
from django.db import models


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class AdminOperationLog(TimeStampedModel):
    MODULE_CHOICES = [
        ("users", "Users"),
        ("recipes", "Recipes"),
        ("community", "Community"),
        ("reports", "Reports"),
        ("announcements", "Announcements"),
    ]

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="admin_operation_logs",
    )
    module = models.CharField(max_length=32, choices=MODULE_CHOICES)
    action = models.CharField(max_length=64)
    target_type = models.CharField(max_length=64, blank=True, default="")
    target_id = models.BigIntegerField(null=True, blank=True)
    target_label = models.CharField(max_length=255, blank=True, default="")
    summary = models.CharField(max_length=255)
    changes = models.JSONField(default=list, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "admin_operation_log"
        ordering = ["-created_at", "-id"]


class UserNotification(TimeStampedModel):
    TYPE_CHOICES = [
        ("mention_post", "Mention Post"),
        ("mention_comment", "Mention Comment"),
        ("reply_comment", "Reply Comment"),
        ("like_post", "Like Post"),
        ("like_comment", "Like Comment"),
        ("announcement", "Announcement"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="sent_notifications",
    )
    notification_type = models.CharField(max_length=32, choices=TYPE_CHOICES)
    title = models.CharField(max_length=120)
    body = models.CharField(max_length=255, blank=True, default="")
    link_path = models.CharField(max_length=255, blank=True, default="")
    metadata = models.JSONField(default=dict, blank=True)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "user_notification"
        ordering = ["-created_at", "-id"]


class Announcement(TimeStampedModel):
    title = models.CharField(max_length=120)
    body = models.CharField(max_length=255)
    link_path = models.CharField(max_length=255, blank=True, default="")
    notification_count = models.PositiveIntegerField(default=0)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="announcements",
    )
    published_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "announcement"
        ordering = ["-published_at", "-id"]
