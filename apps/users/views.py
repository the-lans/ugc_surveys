from rest_framework import generics
from rest_framework.permissions import AllowAny, IsAuthenticated

from apps.users.serializers import RegisterSerializer, UserProfileSerializer


class RegisterView(generics.CreateAPIView):
    """Регистрация нового пользователя"""

    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]


class MeView(generics.RetrieveAPIView):
    """Профиль текущего пользователя: id, username, role"""

    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user
