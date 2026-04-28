from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

from apps.users.constants import UserRole

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    """Регистрация нового пользователя"""

    password = serializers.CharField(write_only=True, min_length=8)
    role = serializers.ChoiceField(
        choices=UserRole.choices,
        required=False,
        default=UserRole.TAKER,
        allow_blank=True,
    )
    access = serializers.CharField(read_only=True)
    refresh = serializers.CharField(read_only=True)

    class Meta:
        model = User
        fields = ["id", "username", "password", "role", "access", "refresh"]

    def validate_role(self, value: str) -> str:
        allowed = {UserRole.CREATOR, UserRole.TAKER}
        if not value or value not in allowed:
            raise serializers.ValidationError(f"Допустимые роли: {', '.join(allowed)}.")
        return value

    def create(self, validated_data: dict) -> User:
        user = User.objects.create_user(
            username=validated_data["username"],
            password=validated_data["password"],
            role=validated_data.get("role", UserRole.TAKER),
        )
        return user

    def to_representation(self, instance: User) -> dict:
        data = super().to_representation(instance)
        refresh = RefreshToken.for_user(instance)
        data["access"] = str(refresh.access_token)
        data["refresh"] = str(refresh)
        return data


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "role"]
        read_only_fields = ["id", "username", "role"]
