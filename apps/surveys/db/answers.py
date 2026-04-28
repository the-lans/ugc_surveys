from django.db.models import Avg, Count, F, QuerySet

from apps.surveys.constants import MAX_SAMPLE_TEXT_ANSWERS
from apps.surveys.models import AnswerOption, Question, Survey, SurveySession, UserAnswer


def create_user_answer(
    *,
    session: SurveySession,
    question: Question,
    selected_option_ids: list[int],
    text_answer: str,
) -> UserAnswer:
    """Сохраняет ответ пользователя."""
    answer = UserAnswer.objects.create(
        session=session,
        question=question,
        text_answer=text_answer,
    )
    if selected_option_ids:
        answer.selected_options.set(AnswerOption.objects.filter(pk__in=selected_option_ids))
    return answer


def get_answer_counts_for_question(question: Question) -> QuerySet:
    """Количество выборов каждого варианта ответа для вопроса."""
    return (
        AnswerOption.objects.filter(question=question)
        .annotate(answer_count=Count("user_answers"))
        .order_by("order")
    )


def get_text_answer_count(question: Question) -> int:
    """Общее количество текстовых ответов на вопрос."""
    return UserAnswer.objects.filter(question=question).exclude(text_answer="").count()


def get_text_answers_for_question(question: Question) -> QuerySet:
    """Последние 50 текстовых ответов на вопрос типа text (для превью в статистике)."""
    return (
        UserAnswer.objects.filter(question=question)
        .exclude(text_answer="")
        .values_list("text_answer", flat=True)
        .order_by("-answered_at")[:MAX_SAMPLE_TEXT_ANSWERS]
    )


def get_all_option_counts(survey: Survey) -> dict[int, list[dict]]:
    """Количество выборов всех вариантов ответа для опроса одним запросом."""
    options = (
        AnswerOption.objects.filter(question__survey=survey)
        .annotate(answer_count=Count("user_answers"))
        .order_by("question_id", "order")
        .values("id", "text", "order", "question_id", "answer_count")
    )
    result: dict[int, list[dict]] = {}
    for opt in options:
        result.setdefault(opt["question_id"], []).append(opt)
    return result


def get_all_text_answer_counts(survey: Survey) -> dict[int, int]:
    """Количество текстовых ответов на все вопросы опроса одним запросом."""
    rows = (
        UserAnswer.objects.filter(question__survey=survey)
        .exclude(text_answer="")
        .values("question_id")
        .annotate(count=Count("id"))
    )
    return {row["question_id"]: row["count"] for row in rows}


def get_session_completion_stats(survey_id: int) -> dict:
    """Статистика сессий: всего, завершено, среднее время прохождения."""
    sessions = SurveySession.objects.filter(survey_id=survey_id)
    total = sessions.count()
    completed = sessions.filter(completed_at__isnull=False)
    completed_count = completed.count()

    avg_seconds = completed.annotate(duration=F("completed_at") - F("started_at")).aggregate(
        avg=Avg("duration")
    )["avg"]

    avg_completion_time = avg_seconds.total_seconds() if avg_seconds is not None else None

    return {
        "total_sessions": total,
        "completed_sessions": completed_count,
        "completion_rate": round(completed_count / total * 100, 1) if total else 0.0,
        "avg_completion_time_seconds": (
            round(avg_completion_time, 1) if avg_completion_time is not None else None
        ),
    }
