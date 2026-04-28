from rest_framework.permissions import BasePermission
from rest_framework.request import Request
from rest_framework.views import APIView


class IsSurveyCreator(BasePermission):
    """Разрешает доступ только пользователям с ролью creator."""

    message = "Доступно только создателям опросов."

    def has_permission(self, request: Request, view: APIView) -> bool:
        return bool(request.user and request.user.is_authenticated and request.user.is_creator)


class IsSurveyTaker(BasePermission):
    """Разрешает доступ только пользователям с ролью taker."""

    message = "Доступно только участникам опросов."

    def has_permission(self, request: Request, view: APIView) -> bool:
        return bool(request.user and request.user.is_authenticated and request.user.is_taker)
