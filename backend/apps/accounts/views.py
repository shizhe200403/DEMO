from django.contrib.auth import get_user_model
from django.db import transaction
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .models import UserHealthCondition, UserProfile
from .serializers import (
    FlexibleTokenObtainPairSerializer,
    RegisterSerializer,
    UserHealthConditionSerializer,
    UserProfileSerializer,
    UserUpdateSerializer,
    UserSerializer,
)


User = get_user_model()


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
