import pytest
from rest_framework import status

from apps.surveys.constants import QuestionType
from apps.surveys.models import SurveySession, UserAnswer


@pytest.mark.django_db
class TestSubmitAnswer:
    def _url(self, survey_id: int) -> str:
        return f"/api/surveys/{survey_id}/answer/"

    def _get_question(self, full_survey, qtype):
        return full_survey.questions.get(question_type=qtype)

    def test_single_choice_valid(self, taker_client, full_survey):
        q = self._get_question(full_survey, QuestionType.SINGLE)
        option = q.options.first()
        response = taker_client.post(
            self._url(full_survey.pk),
            {
                "question_id": q.pk,
                "selected_option_ids": [option.pk],
            },
        )
        assert response.status_code == status.HTTP_201_CREATED

    def test_single_choice_multiple_options_rejected(self, taker_client, full_survey):
        q = self._get_question(full_survey, QuestionType.SINGLE)
        option_ids = list(q.options.values_list("id", flat=True))
        response = taker_client.post(
            self._url(full_survey.pk),
            {
                "question_id": q.pk,
                "selected_option_ids": option_ids,
            },
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_multiple_choice_valid(self, taker_client, full_survey):
        q = self._get_question(full_survey, QuestionType.MULTIPLE)
        option_ids = list(q.options.values_list("id", flat=True))
        response = taker_client.post(
            self._url(full_survey.pk),
            {
                "question_id": q.pk,
                "selected_option_ids": option_ids,
            },
        )
        assert response.status_code == status.HTTP_201_CREATED

    def test_text_answer_valid(self, taker_client, full_survey):
        q = self._get_question(full_survey, QuestionType.TEXT)
        response = taker_client.post(
            self._url(full_survey.pk),
            {
                "question_id": q.pk,
                "text_answer": "Мой текстовый ответ",
            },
        )
        assert response.status_code == status.HTTP_201_CREATED

    def test_text_question_with_options_rejected(self, taker_client, full_survey):
        q_text = self._get_question(full_survey, QuestionType.TEXT)
        q_single = self._get_question(full_survey, QuestionType.SINGLE)
        option = q_single.options.first()
        response = taker_client.post(
            self._url(full_survey.pk),
            {
                "question_id": q_text.pk,
                "selected_option_ids": [option.pk],
            },
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_duplicate_answer_rejected(self, taker_client, taker_user, full_survey):
        q = self._get_question(full_survey, QuestionType.SINGLE)
        option = q.options.first()
        session = SurveySession.objects.create(user=taker_user, survey=full_survey)
        UserAnswer.objects.create(session=session, question=q)

        response = taker_client.post(
            self._url(full_survey.pk),
            {
                "question_id": q.pk,
                "selected_option_ids": [option.pk],
            },
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_option_from_another_question_rejected(self, taker_client, full_survey):
        q1 = self._get_question(full_survey, QuestionType.SINGLE)
        q2 = self._get_question(full_survey, QuestionType.MULTIPLE)
        wrong_option = q2.options.first()

        response = taker_client.post(
            self._url(full_survey.pk),
            {
                "question_id": q1.pk,
                "selected_option_ids": [wrong_option.pk],
            },
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_last_answer_marks_survey_complete(self, taker_client, taker_user, full_survey):
        session = SurveySession.objects.create(user=taker_user, survey=full_survey)
        questions = list(full_survey.questions.order_by("order"))

        for q in questions[:-1]:
            UserAnswer.objects.create(session=session, question=q)

        last_q = questions[-1]
        response = taker_client.post(
            self._url(full_survey.pk),
            {
                "question_id": last_q.pk,
                "text_answer": "Последний ответ",
            },
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.json()["completed"] is True
        assert response.json()["next_question_url"] is None
