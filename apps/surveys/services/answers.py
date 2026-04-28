from django.db import transaction
from rest_framework.exceptions import ValidationError

from apps.surveys.constants import QuestionType
from apps.surveys.db.answers import create_user_answer
from apps.surveys.models import AnswerOption, Question, SurveySession, UserAnswer


def submit_answer(
    *,
    session: SurveySession,
    question: Question,
    selected_option_ids: list[int],
    text_answer: str,
) -> UserAnswer:
    """Валидирует и сохраняет ответ пользователя."""
    _validate_answer_data(
        question=question,
        selected_option_ids=selected_option_ids,
        text_answer=text_answer,
    )
    with transaction.atomic():
        _validate_not_already_answered(session=session, question=question)
        return create_user_answer(
            session=session,
            question=question,
            selected_option_ids=selected_option_ids,
            text_answer=text_answer,
        )


def _validate_not_already_answered(
    *,
    session: SurveySession,
    question: Question,
) -> None:
    if UserAnswer.objects.filter(session=session, question=question).exists():
        raise ValidationError("Вы уже отвечали на этот вопрос.")


def _validate_answer_data(
    *,
    question: Question,
    selected_option_ids: list[int],
    text_answer: str,
) -> None:
    qtype = question.question_type

    if qtype == QuestionType.TEXT:
        if selected_option_ids:
            raise ValidationError("Для вопроса с текстовым ответом нельзя выбирать варианты.")
        if not text_answer.strip():
            raise ValidationError("Текстовый ответ не может быть пустым.")
        return

    if not selected_option_ids:
        raise ValidationError("Необходимо выбрать хотя бы один вариант ответа.")

    if text_answer:
        raise ValidationError("Текстовый ответ не допускается для данного типа вопроса.")

    if qtype == QuestionType.SINGLE and len(selected_option_ids) > 1:
        raise ValidationError("Для данного вопроса допускается только один вариант ответа.")

    _validate_options_belong_to_question(
        question=question,
        selected_option_ids=selected_option_ids,
    )


def _validate_options_belong_to_question(
    *,
    question: Question,
    selected_option_ids: list[int],
) -> None:
    valid_ids = set(AnswerOption.objects.filter(question=question).values_list("id", flat=True))
    invalid = set(selected_option_ids) - valid_ids
    if invalid:
        raise ValidationError(f"Варианты ответа {sorted(invalid)} не принадлежат данному вопросу.")
