from django.contrib.auth import get_user_model
from django.db.models import Q
from rest_framework import serializers

from .models import ContentReport, Post, PostComment

User = get_user_model()


def admin_report_assignee_queryset():
    return User.objects.filter(
        Q(is_superuser=True) | Q(is_staff=True) | Q(role__in=["admin", "auditor"]),
        status="active",
    ).order_by("role", "username", "id")


class UserBriefSerializer(serializers.ModelSerializer):
    display_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "username", "nickname", "avatar_url", "display_name"]

    def get_display_name(self, obj):
        return obj.nickname or obj.username


class PostCommentSerializer(serializers.ModelSerializer):
    user_info = UserBriefSerializer(source="user", read_only=True)

    class Meta:
        model = PostComment
        fields = ["id", "user", "user_info", "content", "image_url", "status", "created_at"]
        read_only_fields = ["id", "status", "created_at", "user"]


class AdminPostCommentSerializer(serializers.ModelSerializer):
    user_info = UserBriefSerializer(source="user", read_only=True)

    class Meta:
        model = PostComment
        fields = ["id", "user", "user_info", "content", "status", "created_at", "updated_at"]
        read_only_fields = ["id", "user", "user_info", "created_at", "updated_at"]


class LinkedRecipeSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    title = serializers.CharField()
    cover_image_url = serializers.CharField()
    meal_type = serializers.CharField()
    cook_time_minutes = serializers.IntegerField(allow_null=True)
    description = serializers.CharField()


class PostSerializer(serializers.ModelSerializer):
    comments = serializers.SerializerMethodField()
    user_info = UserBriefSerializer(source="user", read_only=True)
    like_count = serializers.SerializerMethodField()
    is_liked_by_me = serializers.SerializerMethodField()
    linked_recipe_info = LinkedRecipeSerializer(source="linked_recipe", read_only=True)

    class Meta:
        model = Post
        fields = [
            "id",
            "user",
            "user_info",
            "title",
            "content",
            "cover_image_url",
            "linked_recipe",
            "linked_recipe_info",
            "status",
            "audit_status",
            "like_count",
            "is_liked_by_me",
            "comments",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "user", "audit_status", "created_at", "updated_at", "comments",
                            "like_count", "is_liked_by_me", "linked_recipe_info"]

    def get_like_count(self, obj):
        return obj.likes.count()

    def get_is_liked_by_me(self, obj):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return False
        return obj.likes.filter(user=request.user).exists()

    def get_comments(self, obj):
        comments = obj.comments.filter(status="visible").select_related("user")
        return PostCommentSerializer(comments, many=True).data

    def create(self, validated_data):
        return Post.objects.create(user=self.context["request"].user, **validated_data)


class AdminPostListSerializer(serializers.ModelSerializer):
    user_info = UserBriefSerializer(source="user", read_only=True)
    visible_comment_count = serializers.SerializerMethodField()
    hidden_comment_count = serializers.SerializerMethodField()
    report_count = serializers.SerializerMethodField()
    latest_report_status = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = [
            "id",
            "user",
            "user_info",
            "title",
            "content",
            "cover_image_url",
            "status",
            "audit_status",
            "created_at",
            "updated_at",
            "visible_comment_count",
            "hidden_comment_count",
            "report_count",
            "latest_report_status",
        ]

    def get_visible_comment_count(self, obj):
        return obj.comments.filter(status="visible").count()

    def get_hidden_comment_count(self, obj):
        return obj.comments.filter(status="hidden").count()

    def get_report_count(self, obj):
        return ContentReport.objects.filter(target_type="post", target_id=obj.id).count()

    def get_latest_report_status(self, obj):
        latest = ContentReport.objects.filter(target_type="post", target_id=obj.id).order_by("-created_at").first()
        return latest.status if latest else ""


class AdminPostDetailSerializer(serializers.ModelSerializer):
    user_info = UserBriefSerializer(source="user", read_only=True)
    comments = serializers.SerializerMethodField()
    report_count = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = [
            "id",
            "user",
            "user_info",
            "title",
            "content",
            "cover_image_url",
            "status",
            "audit_status",
            "comments",
            "report_count",
            "created_at",
            "updated_at",
        ]

    def get_comments(self, obj):
        comments = obj.comments.select_related("user").order_by("-created_at")
        return AdminPostCommentSerializer(comments, many=True).data

    def get_report_count(self, obj):
        return ContentReport.objects.filter(target_type="post", target_id=obj.id).count()


class AdminPostUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        fields = ["title", "content", "cover_image_url", "status", "audit_status"]


class ContentReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContentReport
        fields = ["id", "target_type", "target_id", "reason", "status", "processed_by", "processed_at", "created_at"]
        read_only_fields = ["id", "status", "processed_by", "processed_at", "created_at"]
        extra_kwargs = {
            "target_type": {"required": False},
            "target_id": {"required": False},
        }

    def create(self, validated_data):
        return ContentReport.objects.create(reporter=self.context["request"].user, **validated_data)


class AdminContentReportListSerializer(serializers.ModelSerializer):
    reporter_info = UserBriefSerializer(source="reporter", read_only=True)
    processed_by_info = UserBriefSerializer(source="processed_by", read_only=True)
    assigned_to_info = UserBriefSerializer(source="assigned_to", read_only=True)
    target_post_title = serializers.SerializerMethodField()

    class Meta:
        model = ContentReport
        fields = [
            "id",
            "reporter",
            "reporter_info",
            "target_type",
            "target_id",
            "target_post_title",
            "reason",
            "status",
            "priority",
            "assigned_to",
            "assigned_to_info",
            "internal_note",
            "follow_up_at",
            "processed_by",
            "processed_by_info",
            "processed_at",
            "created_at",
            "updated_at",
        ]

    def get_target_post_title(self, obj):
        if obj.target_type != "post":
            return ""
        post = Post.objects.filter(id=obj.target_id).only("title").first()
        return post.title if post else ""


class AdminContentReportDetailSerializer(AdminContentReportListSerializer):
    target_post = serializers.SerializerMethodField()
    assignable_users = serializers.SerializerMethodField()

    class Meta(AdminContentReportListSerializer.Meta):
        fields = AdminContentReportListSerializer.Meta.fields + ["target_post", "assignable_users"]

    def get_target_post(self, obj):
        if obj.target_type != "post":
            return None
        post = Post.objects.select_related("user").prefetch_related("comments__user").filter(id=obj.target_id).first()
        return AdminPostDetailSerializer(post).data if post else None

    def get_assignable_users(self, obj):
        return UserBriefSerializer(admin_report_assignee_queryset(), many=True).data


class AdminContentReportUpdateSerializer(serializers.ModelSerializer):
    assigned_to = serializers.PrimaryKeyRelatedField(
        queryset=admin_report_assignee_queryset(),
        required=False,
        allow_null=True,
    )
    internal_note = serializers.CharField(required=False, allow_blank=True)
    follow_up_at = serializers.DateTimeField(required=False, allow_null=True)

    class Meta:
        model = ContentReport
        fields = ["status", "priority", "assigned_to", "internal_note", "follow_up_at"]
