from django.conf import settings
from django.db import models

from apps.surveys.constants import (
    MAX_OPTION_TEXT_LENGTH,
    MAX_TITLE_LENGTH,
    QuestionType,
)


class Survey(models.Model):
    """Опрос"""

    title = models.CharField(max_length=MAX_TITLE_LENGTH, verbose_name="Название")
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="surveys",
        verbose_name="Автор",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создан")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Обновлён")
    is_active = models.BooleanField(default=True, verbose_name="Активен")

    class Meta:
        verbose_name = "Опрос"
        verbose_name_plural = "Опросы"
        indexes = [
            models.Index(fields=["author"], name="survey_author_idx"),
            models.Index(fields=["created_at"], name="survey_created_idx"),
            # Покрывающий индекс для get_available_surveys():
            # filter(is_active=True).order_by("-created_at") — без него sequential scan по 1M строк
            models.Index(fields=["is_active", "-created_at"], name="survey_active_created_idx"),
        ]

    def __str__(self) -> str:
        return self.title


class Question(models.Model):
    """Вопрос внутри опроса"""

    survey = models.ForeignKey(
        Survey,
        on_delete=models.CASCADE,
        related_name="questions",
        verbose_name="Опрос",
    )
    text = models.TextField(verbose_name="Текст вопроса")
    question_type = models.CharField(
        max_length=10,
        choices=QuestionType.choices,
        default=QuestionType.SINGLE,
        verbose_name="Тип вопроса",
    )
    order = models.PositiveIntegerField(verbose_name="Порядок")

    class Meta:
        verbose_name = "Вопрос"
        verbose_name_plural = "Вопросы"
        unique_together = [("survey", "order")]
        ordering = ["order"]
        indexes = [
            models.Index(fields=["survey", "order"], name="question_survey_order_idx"),
        ]

    def __str__(self) -> str:
        return f"[{self.order}] {self.text[:60]}"


class AnswerOption(models.Model):
    """Вариант ответа на вопрос"""

    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name="options",
        verbose_name="Вопрос",
    )
    text = models.CharField(
        max_length=MAX_OPTION_TEXT_LENGTH,
        verbose_name="Текст варианта",
    )
    order = models.PositiveIntegerField(verbose_name="Порядок")

    class Meta:
        verbose_name = "Вариант ответа"
        verbose_name_plural = "Варианты ответа"
        unique_together = [("question", "order")]
        ordering = ["order"]
        indexes = [
            models.Index(fields=["question", "order"], name="option_question_order_idx"),
        ]

    def __str__(self) -> str:
        return f"[{self.order}] {self.text[:60]}"


class SurveySession(models.Model):
    """Сессия прохождения опроса конкретным пользователем"""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="sessions",
        verbose_name="Пользователь",
    )
    survey = models.ForeignKey(
        Survey,
        on_delete=models.CASCADE,
        related_name="sessions",
        verbose_name="Опрос",
    )
    started_at = models.DateTimeField(auto_now_add=True, verbose_name="Начат")
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Завершён",
    )

    class Meta:
        verbose_name = "Сессия опроса"
        verbose_name_plural = "Сессии опросов"
        unique_together = [("user", "survey")]
        indexes = [
            models.Index(fields=["user", "survey"], name="session_user_survey_idx"),
        ]

    def __str__(self) -> str:
        status = "завершена" if self.completed_at else "в процессе"
        return f"{self.user} / {self.survey} ({status})"


class UserAnswer(models.Model):
    """Ответ пользователя на конкретный вопрос в рамках сессии.
    Индексы:
      (session_id, question_id) — для NOT EXISTS subquery в get_next_unanswered_question
      (question_id,) — для агрегации статистики по вопросу
    """

    session = models.ForeignKey(
        SurveySession,
        on_delete=models.CASCADE,
        related_name="answers",
        verbose_name="Сессия",
    )
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name="user_answers",
        verbose_name="Вопрос",
    )
    selected_options = models.ManyToManyField(
        AnswerOption,
        blank=True,
        related_name="user_answers",
        verbose_name="Выбранные варианты",
    )
    text_answer = models.TextField(blank=True, verbose_name="Текстовый ответ")
    answered_at = models.DateTimeField(auto_now_add=True, verbose_name="Отвечен")

    class Meta:
        verbose_name = "Ответ пользователя"
        verbose_name_plural = "Ответы пользователей"
        unique_together = [("session", "question")]
        indexes = [
            models.Index(
                fields=["session", "question"],
                name="answer_session_question_idx",
            ),
            models.Index(fields=["question"], name="answer_question_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.session.user} → {self.question}"
