from django.db.models import Count, QuerySet
from django.shortcuts import get_object_or_404

from apps.surveys.models import Survey, UserAnswer


def get_survey_by_id(survey_id: int) -> Survey:
    """Возвращает активный опрос по id или 404."""
    return get_object_or_404(Survey, pk=survey_id, is_active=True)


def get_creator_surveys(author_id: int) -> QuerySet[Survey]:
    """Активные опросы автора."""
    return (
        Survey.objects.filter(author_id=author_id, is_active=True)
        .select_related("author")
        .annotate(question_count=Count("questions"))
        .order_by("-created_at")
    )


def get_available_surveys() -> QuerySet[Survey]:
    """Активные опросы для выбора участниками."""
    return (
        Survey.objects.filter(is_active=True)
        .select_related("author")
        .annotate(question_count=Count("questions"))
        .order_by("-created_at")
    )


def has_responses(survey: Survey) -> bool:
    """Есть ли уже хоть один ответ на вопросы этого опроса."""
    return UserAnswer.objects.filter(question__survey=survey).exists()


def deactivate_survey(survey: Survey) -> None:
    """Мягкое удаление: скрывает опрос, не трогая данные сессий."""
    survey.is_active = False
    survey.save(update_fields=["is_active", "updated_at"])
