from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from apps.users.models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ["username", "email", "role", "is_staff", "date_joined"]
    list_filter = ["role", "is_staff", "is_active"]
    fieldsets = BaseUserAdmin.fieldsets + (  # type: ignore[operator]
        ("Роль", {"fields": ("role",)}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (  # type: ignore[operator]
        ("Роль", {"fields": ("role",)}),
    )
