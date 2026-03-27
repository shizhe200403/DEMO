from django.contrib.auth import authenticate, get_user_model
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

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

    class Meta:
        model = User
        fields = ["username", "email", "phone", "password"]

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
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

        authenticated = authenticate(username=user.username, password=password)
        if authenticated is None:
            raise serializers.ValidationError("账号或密码错误")

        attrs["user"] = authenticated
        return attrs
