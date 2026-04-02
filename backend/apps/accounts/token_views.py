from django.contrib.auth import get_user_model
from rest_framework_simplejwt.exceptions import AuthenticationFailed
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.settings import api_settings
from rest_framework_simplejwt.views import TokenRefreshView

from .auth_state import is_user_disabled


class ActiveStatusTokenRefreshSerializer(TokenRefreshSerializer):
    default_error_messages = {
        "no_active_account": "No active account found for the given token.",
    }

    def validate(self, attrs):
        refresh = self.token_class(attrs["refresh"])
        user_id = refresh.payload.get(api_settings.USER_ID_CLAIM)
        if user_id is not None:
            user = get_user_model().objects.filter(**{api_settings.USER_ID_FIELD: user_id}).first()
            if user is not None and is_user_disabled(user):
                raise AuthenticationFailed(
                    self.error_messages["no_active_account"],
                    "no_active_account",
                )

        return super().validate(attrs)


class ActiveStatusTokenRefreshView(TokenRefreshView):
    serializer_class = ActiveStatusTokenRefreshSerializer
