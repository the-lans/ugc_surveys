from apps.surveys.constants import QuestionType
from apps.surveys.db.answers import (
    get_all_option_counts,
    get_all_text_answer_counts,
    get_session_completion_stats,
    get_text_answers_for_question,
)
from apps.surveys.db.questions import get_ordered_questions
from apps.surveys.models import Survey


def calculate_survey_stats(survey: Survey) -> dict:
    """Собирает статистику прохождения опроса.
    Для single/multiple — количество и процент выборов каждого варианта.
    Для text — количество ответов и последние 50 текстовых ответов.
    """
    session_stats = get_session_completion_stats(survey.pk)
    questions = list(get_ordered_questions(survey))
    option_counts = get_all_option_counts(survey)
    text_counts = get_all_text_answer_counts(survey)
    questions_data = []

    for question in questions:
        q_data: dict = {
            "question_id": question.pk,
            "text": question.text,
            "question_type": question.question_type,
        }

        if question.question_type == QuestionType.TEXT:
            q_data["answer_count"] = text_counts.get(question.pk, 0)
            q_data["sample_answers"] = list(get_text_answers_for_question(question))
        else:
            options = option_counts.get(question.pk, [])
            total_answers = sum(o["answer_count"] for o in options)
            q_data["total_answers"] = total_answers
            q_data["options"] = [
                {
                    "option_id": opt["id"],
                    "text": opt["text"],
                    "count": opt["answer_count"],
                    "percentage": (
                        round(opt["answer_count"] / total_answers * 100, 1)
                        if total_answers
                        else 0.0
                    ),
                }
                for opt in options
            ]

        questions_data.append(q_data)

    return {
        "survey_id": survey.pk,
        "title": survey.title,
        **session_stats,
        "questions": questions_data,
    }
