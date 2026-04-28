from django.db.models import Exists, OuterRef, QuerySet

from apps.surveys.models import AnswerOption, Question, Survey, SurveySession, UserAnswer


def get_ordered_questions(survey: Survey) -> QuerySet[Question]:
    """Все вопросы опроса в порядке отображения."""
    return Question.objects.filter(survey=survey).prefetch_related("options")


def get_next_unanswered_question(
    *,
    session: SurveySession,
    survey: Survey,
) -> Question | None:
    """Возвращает первый вопрос, на который пользователь ещё не ответил."""
    already_answered = Exists(
        UserAnswer.objects.filter(
            session=session,
            question_id=OuterRef("pk"),
        )
    )
    return (
        Question.objects.filter(survey=survey)
        .select_related("survey")
        .annotate(is_answered=already_answered)
        .filter(is_answered=False)
        .prefetch_related("options")
        .order_by("order")
        .first()
    )


def bulk_update_question_order(items: list[dict]) -> None:
    """Обновляет order для списка вопросов."""
    if not items:
        return

    ids = [item["id"] for item in items]
    questions = {q.pk: q for q in Question.objects.filter(pk__in=ids)}

    for item in items:
        question = questions.get(item["id"])
        if question:
            question.order = item["order"]

    Question.objects.bulk_update(list(questions.values()), fields=["order"])


def bulk_update_option_order(items: list[dict]) -> None:
    """Обновляет order для вариантов ответа."""
    if not items:
        return

    ids = [item["id"] for item in items]
    options = {o.pk: o for o in AnswerOption.objects.filter(pk__in=ids)}

    for item in items:
        option = options.get(item["id"])
        if option:
            option.order = item["order"]

    AnswerOption.objects.bulk_update(list(options.values()), fields=["order"])
