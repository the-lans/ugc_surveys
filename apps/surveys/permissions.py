from rest_framework.permissions import BasePermission
from rest_framework.request import Request
from rest_framework.views import APIView

from apps.surveys.models import Survey


class IsAuthorOrReadOnly(BasePermission):
    """Изменять опрос может только его автор"""

    def has_object_permission(self, request: Request, view: APIView, obj: Survey) -> bool:
        if request.method in ("GET", "HEAD", "OPTIONS"):
            return True
        return obj.author == request.user
