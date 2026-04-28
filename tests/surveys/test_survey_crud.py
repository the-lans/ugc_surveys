import pytest
from django.contrib.auth import get_user_model
from rest_framework import status

from apps.surveys.constants import QuestionType
from apps.surveys.models import Question, Survey, SurveySession, UserAnswer

User = get_user_model()


@pytest.mark.django_db
class TestSurveyCRUD:
    url = "/api/surveys/"

    def test_create_survey(self, creator_client):
        response = creator_client.post(self.url, {"title": "Новый опрос"})
        assert response.status_code == status.HTTP_201_CREATED
        assert Survey.objects.filter(title="Новый опрос").exists()

    def test_list_own_surveys(self, creator_client, survey):
        response = creator_client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["count"] == 1

    def test_another_creator_cannot_edit(self, another_creator_client, survey):
        response = another_creator_client.patch(f"{self.url}{survey.pk}/", {"title": "Чужой"})
        # Чужой опрос не попадает в queryset другого создателя → 404
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_soft_deactivates(self, creator_client, survey):
        response = creator_client.delete(f"{self.url}{survey.pk}/")
        assert response.status_code == status.HTTP_204_NO_CONTENT
        survey.refresh_from_db()
        assert survey.is_active is False

    def test_delete_removes_from_list(self, creator_client, survey):
        """Удалённый опрос не должен появляться в списке creator'а."""
        creator_client.delete(f"{self.url}{survey.pk}/")
        response = creator_client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["count"] == 0

    def test_cannot_edit_locked_survey(self, creator_client, full_survey):
        """После появления ответов редактирование запрещено."""
        taker_obj = User.objects.create_user(username="t1", password="pass", role="taker")
        session = SurveySession.objects.create(user=taker_obj, survey=full_survey)
        question = full_survey.questions.first()
        UserAnswer.objects.create(session=session, question=question)

        response = creator_client.patch(
            f"{self.url}{full_survey.pk}/",
            {"title": "Изменённый"},
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_reorder_rejects_foreign_question_ids(
        self, creator_client, full_survey, another_creator
    ):
        """Нельзя переупорядочить вопросы, принадлежащие другому опросу."""
        foreign_survey = Survey.objects.create(title="Чужой опрос", author=another_creator)
        foreign_q = Question.objects.create(
            survey=foreign_survey,
            text="Чужой вопрос",
            question_type=QuestionType.SINGLE,
            order=1,
        )
        response = creator_client.post(
            f"/api/surveys/{full_survey.pk}/questions/reorder/",
            {"items": [{"id": foreign_q.pk, "order": 1}]},
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_delete_preserves_sessions(self, creator_client, full_survey, taker_user):
        """Мягкое удаление не удаляет данные сессий."""
        SurveySession.objects.create(user=taker_user, survey=full_survey)
        creator_client.delete(f"{self.url}{full_survey.pk}/")
        assert SurveySession.objects.filter(survey=full_survey).exists()
