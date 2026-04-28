from django.contrib.auth.models import AbstractUser
from django.db import models

from apps.users.constants import UserRole


class User(AbstractUser):
    """Пользователь системы"""

    role = models.CharField(
        max_length=10,
        choices=UserRole.choices,
        default=UserRole.TAKER,
        verbose_name="Роль",
    )

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"

    @property
    def is_creator(self) -> bool:
        return self.role == UserRole.CREATOR

    @property
    def is_taker(self) -> bool:
        return self.role == UserRole.TAKER

    def __str__(self) -> str:
        return f"{self.username} ({self.get_role_display()})"
