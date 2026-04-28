import pytest
from django.db import IntegrityError

from apps.surveys.models import Question, SurveySession, UserAnswer


@pytest.mark.django_db
class TestSurveyModel:
    def test_survey_created(self, survey):
        assert survey.pk is not None
        assert survey.is_active is True
        assert survey.created_at is not None

    def test_str_representation(self, survey):
        assert str(survey) == survey.title


@pytest.mark.django_db
class TestQuestionModel:
    def test_unique_order_per_survey(self, full_survey):
        q = full_survey.questions.first()
        with pytest.raises(IntegrityError):
            Question.objects.create(
                survey=full_survey,
                text="Дубль",
                order=q.order,
            )

    def test_ordering_by_order(self, full_survey):
        orders = list(full_survey.questions.values_list("order", flat=True))
        assert orders == sorted(orders)


@pytest.mark.django_db
class TestSurveySessionModel:
    def test_unique_session_per_user_survey(self, taker_user, full_survey):
        SurveySession.objects.create(user=taker_user, survey=full_survey)
        with pytest.raises(IntegrityError):
            SurveySession.objects.create(user=taker_user, survey=full_survey)

    def test_session_not_completed_by_default(self, taker_user, full_survey):
        session = SurveySession.objects.create(user=taker_user, survey=full_survey)
        assert session.completed_at is None


@pytest.mark.django_db
class TestUserAnswerModel:
    def test_unique_answer_per_session_question(self, taker_user, full_survey):
        session = SurveySession.objects.create(user=taker_user, survey=full_survey)
        question = full_survey.questions.first()
        UserAnswer.objects.create(session=session, question=question)
        with pytest.raises(IntegrityError):
            UserAnswer.objects.create(session=session, question=question)
