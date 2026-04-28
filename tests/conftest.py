import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.surveys.constants import QuestionType
from apps.surveys.models import AnswerOption, Question, Survey

User = get_user_model()


@pytest.fixture
def api_client() -> APIClient:
    return APIClient()


def _make_auth_client(user: User) -> APIClient:
    client = APIClient()
    refresh = RefreshToken.for_user(user)
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")
    return client


@pytest.fixture
def creator_user(db) -> User:
    return User.objects.create_user(
        username="creator",
        password="testpass123",
        role="creator",
    )


@pytest.fixture
def taker_user(db) -> User:
    return User.objects.create_user(
        username="taker",
        password="testpass123",
        role="taker",
    )


@pytest.fixture
def another_creator(db) -> User:
    return User.objects.create_user(
        username="creator2",
        password="testpass123",
        role="creator",
    )


@pytest.fixture
def creator_client(creator_user: User) -> APIClient:
    return _make_auth_client(creator_user)


@pytest.fixture
def taker_client(taker_user: User) -> APIClient:
    return _make_auth_client(taker_user)


@pytest.fixture
def another_creator_client(another_creator: User) -> APIClient:
    return _make_auth_client(another_creator)


@pytest.fixture
def survey(creator_user: User) -> Survey:
    return Survey.objects.create(title="Тестовый опрос", author=creator_user)


@pytest.fixture
def full_survey(creator_user: User) -> Survey:
    """Опрос с тремя вопросами разных типов и вариантами ответов."""
    s = Survey.objects.create(title="Полный опрос", author=creator_user)

    q1 = Question.objects.create(
        survey=s,
        text="Вопрос с одним вариантом",
        question_type=QuestionType.SINGLE,
        order=1,
    )
    AnswerOption.objects.create(question=q1, text="Да", order=1)
    AnswerOption.objects.create(question=q1, text="Нет", order=2)

    q2 = Question.objects.create(
        survey=s,
        text="Вопрос с несколькими вариантами",
        question_type=QuestionType.MULTIPLE,
        order=2,
    )
    AnswerOption.objects.create(question=q2, text="Вариант А", order=1)
    AnswerOption.objects.create(question=q2, text="Вариант Б", order=2)
    AnswerOption.objects.create(question=q2, text="Вариант В", order=3)

    Question.objects.create(
        survey=s,
        text="Вопрос с текстовым ответом",
        question_type=QuestionType.TEXT,
        order=3,
    )

    return s
