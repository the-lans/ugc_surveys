from django.db import models


class UserRole(models.TextChoices):
    CREATOR = "creator", "Создатель опросов"
    TAKER = "taker", "Участник опросов"
