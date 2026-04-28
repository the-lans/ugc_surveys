from django.db import models


class QuestionType(models.TextChoices):
    SINGLE = "single", "Один вариант"
    MULTIPLE = "multiple", "Несколько вариантов"
    TEXT = "text", "Свободный ответ"


# Ограничения для валидации
MAX_ANSWER_OPTIONS = 10
MAX_QUESTIONS_PER_SURVEY = 100
MAX_TITLE_LENGTH = 255
MAX_OPTION_TEXT_LENGTH = 500
MAX_SAMPLE_TEXT_ANSWERS = 50
