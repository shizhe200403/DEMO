from django.contrib.auth import authenticate, get_user_model
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from .auth_state import is_user_disabled
from .models import UserHealthCondition, UserProfile


User = get_user_model()


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = [
            "gender",
            "birthday",
            "height_cm",
            "weight_kg",
            "target_weight_kg",
            "activity_level",
            "occupation",
            "budget_level",
            "cooking_skill",
            "meal_preference",
            "diet_type",
            "is_outdoor_eating_frequent",
            "household_size",
        ]


class UserHealthConditionSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserHealthCondition
        fields = [
            "has_allergy",
            "allergy_tags",
            "avoid_food_tags",
            "religious_restriction",
            "has_hypertension",
            "has_diabetes",
            "has_hyperlipidemia",
            "is_pregnant",
            "is_lactating",
            "notes",
        ]


class UserSerializer(serializers.ModelSerializer):
    profile = serializers.SerializerMethodField()
    health_condition = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "phone",
            "role",
            "status",
            "nickname",
            "signature",
            "avatar_url",
            "is_staff",
            "is_superuser",
            "plan",
            "ai_monthly_usage",
            "ai_usage_reset_at",
            "profile",
            "health_condition",
        ]

    @extend_schema_field(UserProfileSerializer(allow_null=True))
    def get_profile(self, obj):
        profile = getattr(obj, "profile", None)
        if profile is None:
            return None
        return UserProfileSerializer(profile).data

    @extend_schema_field(UserHealthConditionSerializer(allow_null=True))
    def get_health_condition(self, obj):
        health_condition = getattr(obj, "health_condition", None)
        if health_condition is None:
            return None
        return UserHealthConditionSerializer(health_condition).data


class PublicUserProfileSerializer(serializers.ModelSerializer):
    profile = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "nickname",
            "signature",
            "avatar_url",
            "date_joined",
            "profile",
        ]

    @extend_schema_field(
        serializers.DictField(
            child=serializers.CharField(allow_blank=True),
            allow_null=True,
        )
    )
    def get_profile(self, obj):
        profile = getattr(obj, "profile", None)
        if profile is None:
            return None
        return {
            "gender": profile.gender or "",
            "occupation": profile.occupation or "",
            "cooking_skill": profile.cooking_skill or "",
            "meal_preference": profile.meal_preference or "",
            "diet_type": profile.diet_type or "",
        }


class PublicUserSearchSerializer(serializers.ModelSerializer):
    display_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "username", "nickname", "avatar_url", "display_name"]

    def get_display_name(self, obj):
        return obj.nickname or obj.username


class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["username", "email", "phone", "nickname", "signature", "avatar_url"]

    def validate_username(self, value):
        user = self.instance
        if User.objects.exclude(pk=user.pk).filter(username=value).exists():
            raise serializers.ValidationError("该用户名已被使用")
        return value

    def validate_email(self, value):
        if value and User.objects.exclude(pk=self.instance.pk).filter(email=value).exists():
            raise serializers.ValidationError("该邮箱已被使用")
        return value

    def validate_phone(self, value):
        if value and User.objects.exclude(pk=self.instance.pk).filter(phone=value).exists():
            raise serializers.ValidationError("该手机号已被使用")
        return value


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    security_question = serializers.CharField(required=False, allow_blank=True, default="")
    security_answer = serializers.CharField(write_only=True, required=False, allow_blank=True, default="")

    class Meta:
        model = User
        fields = ["username", "email", "phone", "password", "security_question", "security_answer"]

    def create(self, validated_data):
        import hashlib
        password = validated_data.pop("password")
        security_answer = validated_data.pop("security_answer", "").strip()
        security_question = validated_data.pop("security_question", "").strip()
        user = User(**validated_data)
        user.set_password(password)
        if security_question and security_answer:
            user.security_question = security_question
            user.security_answer_hash = hashlib.sha256(security_answer.lower().encode()).hexdigest()
        user.save()
        UserProfile.objects.create(user=user)
        UserHealthCondition.objects.create(user=user)
        return user

    def validate(self, attrs):
        if attrs.get("username") and User.objects.filter(username=attrs["username"]).exists():
            raise serializers.ValidationError({"username": "该用户名已被注册"})
        if attrs.get("email") and User.objects.filter(email=attrs["email"]).exists():
            raise serializers.ValidationError({"email": "该邮箱已被注册"})
        if attrs.get("phone") and User.objects.filter(phone=attrs["phone"]).exists():
            raise serializers.ValidationError({"phone": "该手机号已被注册"})
        return attrs


class FlexibleTokenObtainPairSerializer(serializers.Serializer):
    account = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        account = attrs["account"]
        password = attrs["password"]

        user = User.objects.filter(username=account).first()
        if user is None:
            user = User.objects.filter(email=account).first()
        if user is None:
            user = User.objects.filter(phone=account).first()

        if user is None:
            raise serializers.ValidationError("账号或密码错误")

        if is_user_disabled(user):
            raise serializers.ValidationError("账号已停用")

        authenticated = authenticate(username=user.username, password=password)
        if authenticated is None:
            raise serializers.ValidationError("账号或密码错误")

        attrs["user"] = authenticated
        return attrs


class AdminUserListSerializer(serializers.ModelSerializer):
    profile_completion = serializers.SerializerMethodField()
    health_flags = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "nickname",
            "email",
            "phone",
            "role",
            "status",
            "plan",
            "date_joined",
            "last_login",
            "profile_completion",
            "health_flags",
        ]

    def get_profile_completion(self, obj):
        profile = getattr(obj, "profile", None)
        if profile is None:
            return 0

        filled_fields = [
            bool(profile.height_cm),
            bool(profile.weight_kg),
            bool(profile.target_weight_kg),
            bool(profile.activity_level),
            bool(profile.diet_type),
            bool(profile.meal_preference),
            bool(profile.occupation),
        ]
        return round(sum(filled_fields) / len(filled_fields) * 100)

    def get_health_flags(self, obj):
        health = getattr(obj, "health_condition", None)
        if health is None:
            return []

        labels = []
        if health.has_diabetes:
            labels.append("糖尿病")
        if health.has_hypertension:
            labels.append("高血压")
        if health.has_hyperlipidemia:
            labels.append("高血脂")
        if health.has_allergy:
            labels.append("过敏")
        return labels


class AdminUserDetailSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer(read_only=True)
    health_condition = UserHealthConditionSerializer(read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "phone",
            "role",
            "status",
            "plan",
            "nickname",
            "signature",
            "avatar_url",
            "is_staff",
            "is_superuser",
            "date_joined",
            "last_login",
            "profile",
            "health_condition",
        ]


class AdminUserUpdateSerializer(UserUpdateSerializer):
    class Meta(UserUpdateSerializer.Meta):
        fields = UserUpdateSerializer.Meta.fields + ["role", "status"]

    def update(self, instance, validated_data):
        if "status" in validated_data:
            instance.is_active = validated_data["status"] != "disabled"
        return super().update(instance, validated_data)

    def validate_role(self, value):
        if value not in dict(User.ROLE_CHOICES):
            raise serializers.ValidationError("角色不合法")
        return value

    def validate_status(self, value):
        if value not in dict(User.STATUS_CHOICES):
            raise serializers.ValidationError("状态不合法")
        return value
