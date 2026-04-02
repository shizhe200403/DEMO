from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import AuthenticationFailed

from .auth_state import is_user_disabled


class ActiveStatusJWTAuthentication(JWTAuthentication):
    def get_user(self, validated_token):
        user = super().get_user(validated_token)
        if is_user_disabled(user):
            raise AuthenticationFailed("User is disabled", code="user_disabled")
        return user
