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
    linked_recipe = models.ForeignKey(
        "recipes.Recipe",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="community_posts",
    )

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
    parent_comment = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="replies",
    )
    content = models.TextField()
    image_url = models.TextField(blank=True, default="")
    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default="visible")

    class Meta:
        db_table = "post_comment"
        ordering = ["-created_at"]


class SensitiveWordRule(TimeStampedModel):
    ACTION_CHOICES = [
        ("mask", "Mask"),
        ("block", "Block"),
    ]

    word = models.CharField(max_length=128, unique=True)
    action = models.CharField(max_length=16, choices=ACTION_CHOICES, default="mask")
    is_active = models.BooleanField(default=True)
    note = models.TextField(blank=True, default="")

    class Meta:
        db_table = "community_sensitive_word_rule"
        ordering = ["action", "word", "-id"]


class ContentReport(TimeStampedModel):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("processed", "Processed"),
        ("rejected", "Rejected"),
    ]
    PRIORITY_CHOICES = [
        ("low", "Low"),
        ("normal", "Normal"),
        ("high", "High"),
        ("urgent", "Urgent"),
    ]

    reporter = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="content_reports")
    target_type = models.CharField(max_length=32)
    target_id = models.BigIntegerField()
    reason = models.TextField()
    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default="pending")
    priority = models.CharField(max_length=32, choices=PRIORITY_CHOICES, default="normal")
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_content_reports",
    )
    internal_note = models.TextField(blank=True, default="")
    follow_up_at = models.DateTimeField(null=True, blank=True)
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


class PostLike(TimeStampedModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="post_likes")
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="likes")

    class Meta:
        db_table = "post_like"
        constraints = [
            models.UniqueConstraint(fields=["user", "post"], name="uq_post_like"),
        ]


class CommentLike(TimeStampedModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="comment_likes")
    comment = models.ForeignKey(PostComment, on_delete=models.CASCADE, related_name="likes")

    class Meta:
        db_table = "comment_like"
        constraints = [
            models.UniqueConstraint(fields=["user", "comment"], name="uq_comment_like"),
        ]
