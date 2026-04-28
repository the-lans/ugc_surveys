import pytest
from django.utils import timezone
from rest_framework import status

from apps.surveys.models import SurveySession, UserAnswer


@pytest.mark.django_db
class TestNextQuestion:
    def _url(self, survey_id: int) -> str:
        return f"/api/surveys/{survey_id}/next-question/"

    def test_first_question_returned(self, taker_client, full_survey):
        response = taker_client.get(self._url(full_survey.pk))
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["order"] == 1
        assert "options" in data
        assert data["session_progress"]["answered"] == 0
        assert data["session_progress"]["total"] == 3

    def test_next_question_after_answer(self, taker_client, taker_user, full_survey):
        session = SurveySession.objects.create(user=taker_user, survey=full_survey)
        first_q = full_survey.questions.order_by("order").first()
        UserAnswer.objects.create(session=session, question=first_q)

        response = taker_client.get(self._url(full_survey.pk))
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["order"] == 2

    def test_survey_completed_returns_204(self, taker_client, taker_user, full_survey):
        session = SurveySession.objects.create(user=taker_user, survey=full_survey)
        for q in full_survey.questions.all():
            UserAnswer.objects.create(session=session, question=q)

        response = taker_client.get(self._url(full_survey.pk))
        assert response.status_code == status.HTTP_204_NO_CONTENT
        session.refresh_from_db()
        assert session.completed_at is not None

    def test_already_completed_survey_returns_204(self, taker_client, taker_user, full_survey):
        SurveySession.objects.create(
            user=taker_user,
            survey=full_survey,
            completed_at=timezone.now(),
        )
        response = taker_client.get(self._url(full_survey.pk))
        assert response.status_code == status.HTTP_204_NO_CONTENT

    @pytest.mark.parametrize("survey_id", [99999])
    def test_nonexistent_survey_returns_404(self, taker_client, survey_id):
        response = taker_client.get(self._url(survey_id))
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_inactive_survey_returns_404(self, taker_client, full_survey):
        full_survey.is_active = False
        full_survey.save()
        response = taker_client.get(self._url(full_survey.pk))
        assert response.status_code == status.HTTP_404_NOT_FOUND
