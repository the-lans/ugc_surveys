import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import status

from apps.surveys.constants import QuestionType
from apps.surveys.models import SurveySession, UserAnswer

User = get_user_model()


@pytest.mark.django_db
class TestSurveyStats:
    def _url(self, survey_id: int) -> str:
        return f"/api/surveys/{survey_id}/stats/"

    def _complete_survey(self, taker_user, full_survey):
        session = SurveySession.objects.create(
            user=taker_user,
            survey=full_survey,
            completed_at=timezone.now(),
        )
        for q in full_survey.questions.filter(question_type=QuestionType.SINGLE):
            answer = UserAnswer.objects.create(session=session, question=q)
            answer.selected_options.set([q.options.first()])
        for q in full_survey.questions.filter(question_type=QuestionType.MULTIPLE):
            answer = UserAnswer.objects.create(session=session, question=q)
            answer.selected_options.set(q.options.all())
        for q in full_survey.questions.filter(question_type=QuestionType.TEXT):
            UserAnswer.objects.create(session=session, question=q, text_answer="ответ")
        return session

    def test_stats_returns_200(self, creator_client, full_survey, taker_user):
        self._complete_survey(taker_user, full_survey)
        response = creator_client.get(self._url(full_survey.pk))
        assert response.status_code == status.HTTP_200_OK

    def test_stats_counts_are_correct(self, creator_client, full_survey, taker_user):
        self._complete_survey(taker_user, full_survey)
        response = creator_client.get(self._url(full_survey.pk))
        data = response.json()
        assert data["total_sessions"] == 1
        assert data["completed_sessions"] == 1
        assert data["completion_rate"] == 100.0

    def test_text_question_has_sample_answers(self, creator_client, full_survey, taker_user):
        self._complete_survey(taker_user, full_survey)
        response = creator_client.get(self._url(full_survey.pk))
        data = response.json()
        text_q = next(q for q in data["questions"] if q["question_type"] == QuestionType.TEXT)
        assert "sample_answers" in text_q
        assert "options" not in text_q

    def test_single_question_has_percentages(self, creator_client, full_survey, taker_user):
        self._complete_survey(taker_user, full_survey)
        response = creator_client.get(self._url(full_survey.pk))
        data = response.json()
        single_q = next(q for q in data["questions"] if q["question_type"] == QuestionType.SINGLE)
        assert "options" in single_q
        for opt in single_q["options"]:
            assert "percentage" in opt

    def test_text_answer_count_exceeds_sample_size(
        self, creator_client, creator_user, full_survey
    ):
        """answer_count должен отражать реальное число ответов, а не размер превью (≤50)."""
        text_q = full_survey.questions.get(question_type=QuestionType.TEXT)

        for i in range(55):
            taker = User.objects.create_user(
                username=f"taker_{i}",
                password="pass",
                role="taker",
            )
            session = SurveySession.objects.create(user=taker, survey=full_survey)
            UserAnswer.objects.create(session=session, question=text_q, text_answer=f"ответ {i}")

        response = creator_client.get(self._url(full_survey.pk))
        data = response.json()
        text_q_data = next(q for q in data["questions"] if q["question_type"] == QuestionType.TEXT)
        assert text_q_data["answer_count"] == 55
        assert len(text_q_data["sample_answers"]) == 50

    def test_another_creator_cannot_view_stats(self, another_creator_client, full_survey):
        response = another_creator_client.get(self._url(full_survey.pk))
        assert response.status_code == status.HTTP_403_FORBIDDEN
