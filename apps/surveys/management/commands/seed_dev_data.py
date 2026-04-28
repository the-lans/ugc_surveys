"""Наполняет dev-базу тестовыми данными."""

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.surveys.constants import QuestionType
from apps.surveys.models import AnswerOption, Question, Survey, SurveySession, UserAnswer

User = get_user_model()

CREATOR_USERNAME = "creator"
TAKER_USERNAME = "taker"
PASSWORD = "testpass123"


class Command(BaseCommand):
    help = "Seed the dev database with sample surveys and users."

    def handle(self, *args, **options) -> None:
        creator = self._get_or_create_user(CREATOR_USERNAME, "creator")
        taker = self._get_or_create_user(TAKER_USERNAME, "taker")
        taker2 = self._get_or_create_user("taker2", "taker")

        survey1 = self._create_survey_veggies(creator)
        survey2 = self._create_survey_tech(creator)
        survey3 = self._create_survey_text_only(creator)

        self._complete_session(taker, survey1)
        self._complete_session(taker2, survey1)
        self._complete_session(taker, survey2)

        self.stdout.write(
            self.style.SUCCESS(
                "\nГотово! Данные для тестирования:\n"
                f"  creator: {CREATOR_USERNAME} / {PASSWORD}\n"
                f"  taker:   {TAKER_USERNAME} / {PASSWORD}\n"
                f"\nОпросы:\n"
                f"  #{survey1.pk}: {survey1.title} (2 сессии завершены)\n"
                f"  #{survey2.pk}: {survey2.title} (1 сессия завершена)\n"
                f"  #{survey3.pk}: {survey3.title} (новый)\n"
                "\nSwagger: http://localhost:8000/api/schema/swagger-ui/"
            )
        )

    def _get_or_create_user(self, username: str, role: str) -> User:
        user, created = User.objects.get_or_create(
            username=username,
            defaults={"role": role},
        )
        if created:
            user.set_password(PASSWORD)
            user.save(update_fields=["password"])
            self.stdout.write(f"  Создан пользователь: {username} ({role})")
        else:
            self.stdout.write(f"  Пользователь уже есть: {username}")
        return user

    def _create_survey_veggies(self, creator: User) -> Survey:
        survey, created = Survey.objects.get_or_create(
            title="Овощи и гастрономия",
            author=creator,
        )
        if not created:
            return survey

        q1 = Question.objects.create(
            survey=survey,
            text="Ты любишь буратту с помидорами?",
            question_type=QuestionType.SINGLE,
            order=1,
        )
        AnswerOption.objects.bulk_create(
            [
                AnswerOption(question=q1, text="Да", order=1),
                AnswerOption(question=q1, text="Нет", order=2),
                AnswerOption(question=q1, text="У меня непереносимость лактозы", order=3),
            ]
        )

        q2 = Question.objects.create(
            survey=survey,
            text="Какие овощи ты готовишь чаще всего?",
            question_type=QuestionType.MULTIPLE,
            order=2,
        )
        AnswerOption.objects.bulk_create(
            [
                AnswerOption(question=q2, text="Помидоры", order=1),
                AnswerOption(question=q2, text="Огурцы", order=2),
                AnswerOption(question=q2, text="Перец", order=3),
                AnswerOption(question=q2, text="Баклажан", order=4),
            ]
        )

        Question.objects.create(
            survey=survey,
            text="Твой любимый рецепт с овощами?",
            question_type=QuestionType.TEXT,
            order=3,
        )

        self.stdout.write(f"  Создан опрос: {survey.title} (id={survey.pk})")
        return survey

    def _create_survey_tech(self, creator: User) -> Survey:
        survey, created = Survey.objects.get_or_create(
            title="Технологии и инструменты",
            author=creator,
        )
        if not created:
            return survey

        q1 = Question.objects.create(
            survey=survey,
            text="Какой основной язык программирования ты используешь?",
            question_type=QuestionType.SINGLE,
            order=1,
        )
        AnswerOption.objects.bulk_create(
            [
                AnswerOption(question=q1, text="Python", order=1),
                AnswerOption(question=q1, text="Go", order=2),
                AnswerOption(question=q1, text="TypeScript", order=3),
                AnswerOption(question=q1, text="Другой", order=4),
            ]
        )

        q2 = Question.objects.create(
            survey=survey,
            text="Какими инструментами пользуешься каждый день?",
            question_type=QuestionType.MULTIPLE,
            order=2,
        )
        AnswerOption.objects.bulk_create(
            [
                AnswerOption(question=q2, text="Docker", order=1),
                AnswerOption(question=q2, text="Git", order=2),
                AnswerOption(question=q2, text="PostgreSQL", order=3),
                AnswerOption(question=q2, text="Redis", order=4),
            ]
        )

        Question.objects.create(
            survey=survey,
            text="Что больше всего нравится в твоём стеке?",
            question_type=QuestionType.TEXT,
            order=3,
        )

        self.stdout.write(f"  Создан опрос: {survey.title} (id={survey.pk})")
        return survey

    def _create_survey_text_only(self, creator: User) -> Survey:
        survey, created = Survey.objects.get_or_create(
            title="Обратная связь о сервисе",
            author=creator,
        )
        if not created:
            return survey

        Question.objects.create(
            survey=survey,
            text="Что тебе понравилось в нашем сервисе?",
            question_type=QuestionType.TEXT,
            order=1,
        )
        Question.objects.create(
            survey=survey,
            text="Что можно улучшить?",
            question_type=QuestionType.TEXT,
            order=2,
        )

        self.stdout.write(f"  Создан опрос: {survey.title} (id={survey.pk})")
        return survey

    def _complete_session(self, taker: User, survey: Survey) -> None:
        session, created = SurveySession.objects.get_or_create(
            user=taker,
            survey=survey,
        )
        if not created and session.completed_at:
            return

        for question in survey.questions.order_by("order"):
            if UserAnswer.objects.filter(session=session, question=question).exists():
                continue

            answer = UserAnswer.objects.create(session=session, question=question)

            if question.question_type == QuestionType.SINGLE:
                answer.selected_options.set([question.options.first()])
            elif question.question_type == QuestionType.MULTIPLE:
                answer.selected_options.set(question.options.all()[:2])
            elif question.question_type == QuestionType.TEXT:
                answer.text_answer = f"Тестовый ответ от {taker.username}"
                answer.save(update_fields=["text_answer"])

        session.completed_at = timezone.now()
        session.save(update_fields=["completed_at"])
        self.stdout.write(f"  Завершена сессия: {taker.username} → {survey.title}")
