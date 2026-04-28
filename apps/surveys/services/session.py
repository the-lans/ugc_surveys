from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.surveys.models import Survey, SurveySession

User = get_user_model()


def get_or_create_session(*, user: User, survey: Survey) -> SurveySession:
    """Возвращает существующую сессию или создаёт новую."""
    session, _ = SurveySession.objects.get_or_create(user=user, survey=survey)
    return session


def mark_session_complete(session: SurveySession) -> None:
    """Помечает сессию как завершённую, если она ещё не завершена."""
    if session.completed_at is None:
        session.completed_at = timezone.now()
        session.save(update_fields=["completed_at"])
