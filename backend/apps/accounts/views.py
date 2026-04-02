from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import permissions, serializers, status
from rest_framework.pagination import PageNumberPagination
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from apps.common.operation_logs import build_change_entries, create_admin_operation_log, snapshot_model_fields
from .auth_state import sync_user_active_flag
from .models import UserHealthCondition, UserProfile
from .serializers import (
    AdminUserDetailSerializer,
    AdminUserListSerializer,
    AdminUserUpdateSerializer,
    FlexibleTokenObtainPairSerializer,
    RegisterSerializer,
    UserHealthConditionSerializer,
    UserProfileSerializer,
    UserUpdateSerializer,
    UserSerializer,
)


User = get_user_model()
USER_STATUS_LABELS = {
    "active": "正常",
    "disabled": "已停用",
}
ACCOUNT_FIELD_LABELS = {
    "username": "用户名",
    "email": "邮箱",
    "phone": "手机号",
    "nickname": "昵称",
    "signature": "签名",
    "avatar_url": "头像",
    "role": "角色",
    "status": "账号状态",
}
PROFILE_FIELD_LABELS = {
    "gender": "性别",
    "birthday": "生日",
    "height_cm": "身高",
    "weight_kg": "体重",
    "target_weight_kg": "目标体重",
    "activity_level": "活动水平",
    "occupation": "职业",
    "budget_level": "预算水平",
    "cooking_skill": "烹饪水平",
    "meal_preference": "餐次偏好",
    "diet_type": "饮食类型",
    "is_outdoor_eating_frequent": "外食频率",
    "household_size": "家庭人数",
}
HEALTH_FIELD_LABELS = {
    "has_allergy": "是否过敏",
    "allergy_tags": "过敏标签",
    "avoid_food_tags": "忌口标签",
    "religious_restriction": "宗教限制",
    "has_hypertension": "高血压",
    "has_diabetes": "糖尿病",
    "has_hyperlipidemia": "高血脂",
    "is_pregnant": "孕期",
    "is_lactating": "哺乳期",
    "notes": "备注",
}


class EnvelopeUserSerializer(serializers.Serializer):
    code = serializers.IntegerField()
    message = serializers.CharField()
    data = UserSerializer()


class EnvelopeProfileSerializer(serializers.Serializer):
    code = serializers.IntegerField()
    message = serializers.CharField()
    data = UserProfileSerializer()


class EnvelopeHealthConditionSerializer(serializers.Serializer):
    code = serializers.IntegerField()
    message = serializers.CharField()
    data = UserHealthConditionSerializer()


class FullProfileRequestSerializer(serializers.Serializer):
    account = UserUpdateSerializer(required=False)
    profile = UserProfileSerializer(required=False)
    health_condition = UserHealthConditionSerializer(required=False)


class FullProfileResponseDataSerializer(serializers.Serializer):
    account = UserSerializer()
    profile = UserProfileSerializer()
    health_condition = UserHealthConditionSerializer()


class EnvelopeFullProfileSerializer(serializers.Serializer):
    code = serializers.IntegerField()
    message = serializers.CharField()
    data = FullProfileResponseDataSerializer()


class LoginResponseDataSerializer(serializers.Serializer):
    access = serializers.CharField()
    refresh = serializers.CharField()
    user = UserSerializer()


class EnvelopeLoginSerializer(serializers.Serializer):
    code = serializers.IntegerField()
    message = serializers.CharField()
    data = LoginResponseDataSerializer()


class AdminUserListEnvelopeSerializer(serializers.Serializer):
    code = serializers.IntegerField()
    message = serializers.CharField()
    data = inline_serializer(
        name="AdminUserListData",
        fields={
            "count": serializers.IntegerField(),
            "next": serializers.CharField(allow_null=True),
            "previous": serializers.CharField(allow_null=True),
            "items": AdminUserListSerializer(many=True),
        },
    )


class AdminUserDetailEnvelopeSerializer(serializers.Serializer):
    code = serializers.IntegerField()
    message = serializers.CharField()
    data = AdminUserDetailSerializer()


class AdminUserRequestSerializer(serializers.Serializer):
    account = AdminUserUpdateSerializer(required=False)
    profile = UserProfileSerializer(required=False)
    health_condition = UserHealthConditionSerializer(required=False)


class AdminUserBulkRequestSerializer(serializers.Serializer):
    ids = serializers.ListField(child=serializers.IntegerField(min_value=1), allow_empty=False)
    status = serializers.ChoiceField(choices=[("active", "active"), ("disabled", "disabled")])


class AdminUserBulkResponseSerializer(serializers.Serializer):
    code = serializers.IntegerField()
    message = serializers.CharField()
    data = inline_serializer(
        name="AdminUserBulkData",
        fields={
            "updated_count": serializers.IntegerField(),
            "ids": serializers.ListField(child=serializers.IntegerField()),
            "status": serializers.CharField(),
        },
    )


class IsAdminManager(permissions.BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and (user.is_superuser or user.is_staff or getattr(user, "role", "") == "admin"))


class AdminUserPagination(PageNumberPagination):
    page_size = 12
    page_size_query_param = "page_size"
    max_page_size = 50

    def get_paginated_response(self, data):
        return Response(
            {
                "code": 0,
                "message": "success",
                "data": {
                    "count": self.page.paginator.count,
                    "next": self.get_next_link(),
                    "previous": self.get_previous_link(),
                    "items": data,
                },
            }
        )


class RegisterView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(request=RegisterSerializer, responses=EnvelopeUserSerializer)
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response({"code": 0, "message": "success", "data": UserSerializer(user).data})


class MeView(APIView):
    @extend_schema(responses=EnvelopeUserSerializer)
    def get(self, request):
        return Response({"code": 0, "message": "success", "data": UserSerializer(request.user).data})

    @extend_schema(request=UserUpdateSerializer, responses=EnvelopeUserSerializer)
    def put(self, request):
        serializer = UserUpdateSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response({"code": 0, "message": "success", "data": UserSerializer(user).data})


class ProfileView(APIView):
    @extend_schema(request=UserProfileSerializer, responses=EnvelopeProfileSerializer)
    def put(self, request):
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        serializer = UserProfileSerializer(profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"code": 0, "message": "success", "data": serializer.data})


class HealthConditionView(APIView):
    @extend_schema(request=UserHealthConditionSerializer, responses=EnvelopeHealthConditionSerializer)
    def put(self, request):
        health_condition, _ = UserHealthCondition.objects.get_or_create(user=request.user)
        serializer = UserHealthConditionSerializer(health_condition, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"code": 0, "message": "success", "data": serializer.data})


class FullProfileView(APIView):
    @transaction.atomic
    @extend_schema(request=FullProfileRequestSerializer, responses=EnvelopeFullProfileSerializer)
    def put(self, request):
        user_serializer = UserUpdateSerializer(request.user, data=request.data.get("account", {}), partial=True)
        user_serializer.is_valid(raise_exception=True)
        user = user_serializer.save()

        profile, _ = UserProfile.objects.get_or_create(user=user)
        profile_serializer = UserProfileSerializer(profile, data=request.data.get("profile", {}), partial=True)
        profile_serializer.is_valid(raise_exception=True)
        profile_serializer.save()

        health_condition, _ = UserHealthCondition.objects.get_or_create(user=user)
        health_serializer = UserHealthConditionSerializer(health_condition, data=request.data.get("health_condition", {}), partial=True)
        health_serializer.is_valid(raise_exception=True)
        health_serializer.save()

        return Response(
            {
                "code": 0,
                "message": "success",
                "data": {
                    "account": UserSerializer(user).data,
                    "profile": profile_serializer.data,
                    "health_condition": health_serializer.data,
                },
            }
        )


class AvatarUploadView(APIView):
    parser_classes = [MultiPartParser]

    @extend_schema(
        request=inline_serializer(name="AvatarUploadRequest", fields={"avatar": serializers.ImageField()}),
        responses=inline_serializer(name="AvatarUploadResponse", fields={"code": serializers.IntegerField(), "message": serializers.CharField(), "avatar_url": serializers.CharField()}),
    )
    def post(self, request):
        file = request.FILES.get("avatar")
        if not file:
            return Response({"code": 1, "message": "请选择图片文件"}, status=status.HTTP_400_BAD_REQUEST)
        if file.size > 5 * 1024 * 1024:
            return Response({"code": 1, "message": "图片大小不能超过 5MB"}, status=status.HTTP_400_BAD_REQUEST)
        if not file.content_type.startswith("image/"):
            return Response({"code": 1, "message": "只支持图片格式"}, status=status.HTTP_400_BAD_REQUEST)

        import os, uuid
        ext = os.path.splitext(file.name)[1].lower() or ".jpg"
        filename = f"{uuid.uuid4().hex}{ext}"
        save_dir = os.path.join("avatars")
        from django.core.files.storage import default_storage
        path = default_storage.save(os.path.join(save_dir, filename), file)
        avatar_url = f"/media/{path}"

        request.user.avatar_url = avatar_url
        request.user.save(update_fields=["avatar_url"])
        return Response({"code": 0, "message": "头像已更新", "avatar_url": avatar_url})


class ChangePasswordView(APIView):
    @extend_schema(
        request=inline_serializer(
            name="ChangePasswordRequest",
            fields={
                "old_password": serializers.CharField(),
                "new_password": serializers.CharField(min_length=8),
            },
        ),
        responses=inline_serializer(
            name="ChangePasswordResponse",
            fields={"code": serializers.IntegerField(), "message": serializers.CharField()},
        ),
    )
    def post(self, request):
        old_password = request.data.get("old_password", "")
        new_password = request.data.get("new_password", "")
        if not old_password or not new_password:
            return Response({"code": 1, "message": "请填写当前密码和新密码"}, status=status.HTTP_400_BAD_REQUEST)
        if len(new_password) < 8:
            return Response({"code": 1, "message": "新密码至少需要 8 位"}, status=status.HTTP_400_BAD_REQUEST)
        if not request.user.check_password(old_password):
            return Response({"code": 1, "message": "当前密码不正确"}, status=status.HTTP_400_BAD_REQUEST)
        request.user.set_password(new_password)
        request.user.save()
        return Response({"code": 0, "message": "密码已更新，请重新登录"})


SECURITY_QUESTIONS = [
    "你的出生城市是？",
    "你的小学校名是？",
    "你的第一只宠物叫什么名字？",
    "你母亲的姓氏是？",
    "你最喜欢的食物是？",
    "你第一部手机的品牌是？",
    "你最好的朋友叫什么名字？",
]


class SecurityQuestionListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        return Response({"code": 0, "message": "success", "data": SECURITY_QUESTIONS})


class SetSecurityQuestionView(APIView):
    def post(self, request):
        question = request.data.get("question", "").strip()
        answer = request.data.get("answer", "").strip()
        if not question or not answer:
            return Response({"code": 1, "message": "密保问题和答案均不能为空"}, status=status.HTTP_400_BAD_REQUEST)
        if question not in SECURITY_QUESTIONS:
            return Response({"code": 1, "message": "请从预设问题中选择"}, status=status.HTTP_400_BAD_REQUEST)
        import hashlib
        answer_hash = hashlib.sha256(answer.lower().strip().encode()).hexdigest()
        request.user.security_question = question
        request.user.security_answer_hash = answer_hash
        request.user.save(update_fields=["security_question", "security_answer_hash"])
        return Response({"code": 0, "message": "密保已设置"})


class GetSecurityQuestionView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        account = request.data.get("account", "").strip()
        if not account:
            return Response({"code": 1, "message": "请输入账号"}, status=status.HTTP_400_BAD_REQUEST)
        from django.db.models import Q
        user = User.objects.filter(
            Q(username=account) | Q(email=account) | Q(phone=account)
        ).first()
        if not user or not user.security_question:
            return Response({"code": 1, "message": "该账号未设置密保问题，无法通过此方式找回密码"}, status=status.HTTP_404_NOT_FOUND)
        return Response({"code": 0, "message": "success", "data": {"question": user.security_question}})


class ResetPasswordBySecurityView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        account = request.data.get("account", "").strip()
        answer = request.data.get("answer", "").strip()
        new_password = request.data.get("new_password", "")
        if not account or not answer or not new_password:
            return Response({"code": 1, "message": "请填写完整信息"}, status=status.HTTP_400_BAD_REQUEST)
        if len(new_password) < 8:
            return Response({"code": 1, "message": "新密码至少需要 8 位"}, status=status.HTTP_400_BAD_REQUEST)
        from django.db.models import Q
        import hashlib
        user = User.objects.filter(
            Q(username=account) | Q(email=account) | Q(phone=account)
        ).first()
        if not user or not user.security_answer_hash:
            return Response({"code": 1, "message": "账号不存在或未设置密保"}, status=status.HTTP_404_NOT_FOUND)
        answer_hash = hashlib.sha256(answer.lower().strip().encode()).hexdigest()
        if answer_hash != user.security_answer_hash:
            return Response({"code": 1, "message": "密保答案不正确"}, status=status.HTTP_400_BAD_REQUEST)
        user.set_password(new_password)
        user.save()
        return Response({"code": 0, "message": "密码已重置，请用新密码登录"})


class DeleteAccountView(APIView):
    @extend_schema(
        request=inline_serializer(
            name="DeleteAccountRequest",
            fields={"password": serializers.CharField()},
        ),
        responses=inline_serializer(
            name="DeleteAccountResponse",
            fields={"code": serializers.IntegerField(), "message": serializers.CharField()},
        ),
    )
    def post(self, request):
        password = request.data.get("password", "")
        if not password:
            return Response({"code": 1, "message": "请输入密码确认注销"}, status=status.HTTP_400_BAD_REQUEST)
        if not request.user.check_password(password):
            return Response({"code": 1, "message": "密码不正确"}, status=status.HTTP_400_BAD_REQUEST)
        request.user.delete()
        return Response({"code": 0, "message": "账号已注销"})


class LoginView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(request=FlexibleTokenObtainPairSerializer, responses=EnvelopeLoginSerializer)
    def post(self, request):
        serializer = FlexibleTokenObtainPairSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        refresh = RefreshToken.for_user(user)
        return Response(
            {
                "code": 0,
                "message": "success",
                "data": {
                    "access": str(refresh.access_token),
                    "refresh": str(refresh),
                    "user": UserSerializer(user).data,
                },
            }
        )


class AdminUserListView(APIView):
    permission_classes = [IsAdminManager]
    pagination_class = AdminUserPagination

    @extend_schema(responses=AdminUserListEnvelopeSerializer)
    def get(self, request):
        queryset = User.objects.select_related("profile", "health_condition").order_by("-date_joined", "-id")

        keyword = request.query_params.get("keyword", "").strip()
        role = request.query_params.get("role", "").strip()
        status_value = request.query_params.get("status", "").strip()

        if keyword:
            queryset = queryset.filter(
                Q(username__icontains=keyword)
                | Q(nickname__icontains=keyword)
                | Q(email__icontains=keyword)
                | Q(phone__icontains=keyword)
            )
        if role:
            queryset = queryset.filter(role=role)
        if status_value:
            queryset = queryset.filter(status=status_value)

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request, view=self)
        serializer = AdminUserListSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)




class AdminUserBulkActionView(APIView):
    permission_classes = [IsAdminManager]

    @transaction.atomic
    @extend_schema(request=AdminUserBulkRequestSerializer, responses=AdminUserBulkResponseSerializer)
    def post(self, request):
        serializer = AdminUserBulkRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        ids = list(dict.fromkeys(serializer.validated_data["ids"]))
        target_status = serializer.validated_data["status"]
        users = list(User.objects.filter(id__in=ids).order_by("id"))
        found_ids = [user.id for user in users]

        for user in users:
            before = snapshot_model_fields(user, ["status"])
            user.status = target_status
            sync_user_active_flag(user)
            user.save(update_fields=["status", "is_active"])
            create_admin_operation_log(
                actor=request.user,
                module="users",
                action="bulk_update_user_status",
                target_type="user",
                target_id=user.id,
                target_label=user.nickname or user.username,
                summary=f"批量将用户 {user.nickname or user.username} 设为{USER_STATUS_LABELS[target_status]}",
                changes=build_change_entries(before, snapshot_model_fields(user, ["status"]), {"status": "账号状态"}, section="账号信息"),
                metadata={"username": user.username, "bulk_action": "update_status", "bulk_status": target_status},
            )

        create_admin_operation_log(
            actor=request.user,
            module="users",
            action="bulk_update_user_status",
            target_type="user_batch",
            target_label=f"{len(found_ids)} 个账号",
            summary=f"批量将 {len(found_ids)} 个账号设为{USER_STATUS_LABELS[target_status]}",
            metadata={"ids": found_ids, "requested_ids": ids, "status": target_status},
        )
        return Response(
            {"code": 0, "message": "success", "data": {"updated_count": len(found_ids), "ids": found_ids, "status": target_status}},
            status=status.HTTP_200_OK,
        )


class AdminUserDetailView(APIView):
    permission_classes = [IsAdminManager]

    def get_object(self, user_id):
        return get_object_or_404(User.objects.select_related("profile", "health_condition"), pk=user_id)

    @extend_schema(responses=AdminUserDetailEnvelopeSerializer)
    def get(self, request, user_id):
        user = self.get_object(user_id)
        serializer = AdminUserDetailSerializer(user)
        return Response({"code": 0, "message": "success", "data": serializer.data})

    @transaction.atomic
    @extend_schema(request=AdminUserRequestSerializer, responses=AdminUserDetailEnvelopeSerializer)
    def patch(self, request, user_id):
        user = self.get_object(user_id)
        account_fields = list((request.data.get("account") or {}).keys())
        profile_fields = list((request.data.get("profile") or {}).keys())
        health_fields = list((request.data.get("health_condition") or {}).keys())

        before_account = snapshot_model_fields(user, account_fields)

        account_serializer = AdminUserUpdateSerializer(user, data=request.data.get("account", {}), partial=True)
        account_serializer.is_valid(raise_exception=True)
        user = account_serializer.save()

        profile, _ = UserProfile.objects.get_or_create(user=user)
        before_profile = snapshot_model_fields(profile, profile_fields)
        profile_serializer = UserProfileSerializer(profile, data=request.data.get("profile", {}), partial=True)
        profile_serializer.is_valid(raise_exception=True)
        profile_serializer.save()

        health_condition, _ = UserHealthCondition.objects.get_or_create(user=user)
        before_health = snapshot_model_fields(health_condition, health_fields)
        health_serializer = UserHealthConditionSerializer(health_condition, data=request.data.get("health_condition", {}), partial=True)
        health_serializer.is_valid(raise_exception=True)
        health_serializer.save()

        changes = [
            *build_change_entries(before_account, snapshot_model_fields(user, account_fields), ACCOUNT_FIELD_LABELS, section="账号信息"),
            *build_change_entries(before_profile, snapshot_model_fields(profile, profile_fields), PROFILE_FIELD_LABELS, section="档案信息"),
            *build_change_entries(before_health, snapshot_model_fields(health_condition, health_fields), HEALTH_FIELD_LABELS, section="健康约束"),
        ]
        create_admin_operation_log(
            actor=request.user,
            module="users",
            action="update_user",
            target_type="user",
            target_id=user.id,
            target_label=user.nickname or user.username,
            summary=f"更新了用户 {user.nickname or user.username} 的账号资料与状态",
            changes=changes,
            metadata={"username": user.username},
        )

        detail_serializer = AdminUserDetailSerializer(user)
        return Response({"code": 0, "message": "success", "data": detail_serializer.data}, status=status.HTTP_200_OK)
