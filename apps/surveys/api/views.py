from django.db import transaction
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import status, viewsets
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.surveys.api.serializers import (
    NextQuestionSerializer,
    QuestionCreateSerializer,
    QuestionSerializer,
    ReorderSerializer,
    SubmitAnswerSerializer,
    SurveyCreateSerializer,
    SurveyDetailSerializer,
    SurveyListSerializer,
    SurveyProgressSerializer,
)
from apps.surveys.db.questions import (
    bulk_update_option_order,
    bulk_update_question_order,
    get_next_unanswered_question,
)
from apps.surveys.db.surveys import (
    deactivate_survey,
    get_available_surveys,
    get_creator_surveys,
    get_survey_by_id,
    has_responses,
)
from apps.surveys.models import AnswerOption, Question, Survey
from apps.surveys.permissions import IsAuthorOrReadOnly
from apps.surveys.services.answers import submit_answer
from apps.surveys.services.session import get_or_create_session, mark_session_complete
from apps.surveys.services.stats import calculate_survey_stats
from apps.users.permissions import IsSurveyCreator, IsSurveyTaker


class SurveyViewSet(viewsets.ModelViewSet):
    """CRUD опросов для создателей."""

    permission_classes = [IsSurveyCreator, IsAuthorOrReadOnly]
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    def get_queryset(self):
        qs = get_creator_surveys(self.request.user.pk)
        if self.action == "retrieve":
            return qs.prefetch_related("questions__options")
        return qs

    def get_serializer_class(self):
        if self.action == "list":
            return SurveyListSerializer
        if self.action == "create":
            return SurveyCreateSerializer
        return SurveyDetailSerializer

    def perform_update(self, serializer) -> None:
        with transaction.atomic():
            survey = Survey.objects.select_for_update().get(pk=serializer.instance.pk)
            if has_responses(survey):
                raise ValidationError(
                    "Опрос заблокирован для редактирования: по нему уже есть ответы."
                )
            serializer.save()

    def perform_destroy(self, instance: Survey) -> None:
        deactivate_survey(instance)


class AvailableSurveysView(ListAPIView):
    """Список активных опросов для участников."""

    serializer_class = SurveyListSerializer
    permission_classes = [IsSurveyTaker]

    def get_queryset(self):
        return get_available_surveys()


@extend_schema(responses={200: dict})
class SurveyStatsView(RetrieveAPIView):
    """Статистика прохождения опроса. Доступна только автору."""

    permission_classes = [IsSurveyCreator]

    def get_object(self) -> Survey:
        survey = get_object_or_404(Survey, pk=self.kwargs["survey_id"])
        if survey.author != self.request.user:
            raise PermissionDenied("Статистика доступна только автору опроса.")
        return survey

    def retrieve(self, request: Request, *args, **kwargs) -> Response:
        survey = self.get_object()
        stats = calculate_survey_stats(survey)
        return Response(stats)


class QuestionViewSet(viewsets.ModelViewSet):
    """Управление вопросами опроса."""

    permission_classes = [IsSurveyCreator]
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    def get_queryset(self):
        survey = get_object_or_404(
            Survey,
            pk=self.kwargs["survey_id"],
            author=self.request.user,
        )
        return Question.objects.filter(survey=survey).prefetch_related("options")

    def get_serializer_class(self):
        if self.action in ("create", "partial_update"):
            return QuestionCreateSerializer
        return QuestionSerializer

    def perform_create(self, serializer) -> None:
        survey = get_object_or_404(
            Survey,
            pk=self.kwargs["survey_id"],
            author=self.request.user,
        )
        if has_responses(survey):
            raise ValidationError("Нельзя добавлять вопросы: по опросу уже есть ответы.")
        serializer.save(survey=survey)


class ReorderQuestionsView(APIView):
    """Переупорядочивание вопросов в опросе."""

    permission_classes = [IsSurveyCreator]

    def post(self, request: Request, survey_id: int) -> Response:
        survey = get_object_or_404(Survey, pk=survey_id, author=request.user)
        if has_responses(survey):
            raise ValidationError(
                "Опрос заблокирован для редактирования: по нему уже есть ответы."
            )
        serializer = ReorderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        question_ids = {item["id"] for item in serializer.validated_data["items"]}
        valid_ids = set(
            Question.objects.filter(survey=survey, pk__in=question_ids).values_list(
                "id", flat=True
            )
        )
        if question_ids != valid_ids:
            raise ValidationError("Один или несколько вопросов не принадлежат этому опросу.")

        with transaction.atomic():
            bulk_update_question_order(serializer.validated_data["items"])

        return Response({"detail": "Порядок вопросов обновлён."})


class ReorderOptionsView(APIView):
    """Переупорядочивание вариантов ответа."""

    permission_classes = [IsSurveyCreator]

    def post(self, request: Request, question_id: int) -> Response:
        question = get_object_or_404(Question, pk=question_id)
        if question.survey.author != request.user:
            raise PermissionDenied()
        if has_responses(question.survey):
            raise ValidationError(
                "Опрос заблокирован для редактирования: по нему уже есть ответы."
            )

        serializer = ReorderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        item_ids = {item["id"] for item in serializer.validated_data["items"]}
        valid_ids = set(
            AnswerOption.objects.filter(question=question).values_list("id", flat=True)
        )
        if not item_ids.issubset(valid_ids):
            raise ValidationError("Один или несколько вариантов не принадлежат этому вопросу.")

        with transaction.atomic():
            bulk_update_option_order(serializer.validated_data["items"])

        return Response({"detail": "Порядок вариантов обновлён."})


@extend_schema(
    responses={
        200: NextQuestionSerializer,
        204: None,
    }
)
class NextQuestionView(APIView):
    """Следующий неотвеченный вопрос в опросе."""

    permission_classes = [IsSurveyTaker]

    def get(self, request: Request, survey_id: int) -> Response:
        survey = get_survey_by_id(survey_id)
        session = get_or_create_session(user=request.user, survey=survey)

        if session.completed_at:
            return Response(status=status.HTTP_204_NO_CONTENT)

        question = get_next_unanswered_question(session=session, survey=survey)

        if question is None:
            mark_session_complete(session)
            return Response(status=status.HTTP_204_NO_CONTENT)

        serializer = NextQuestionSerializer(
            question,
            context={"session": session, "request": request},
        )
        return Response(serializer.data)


class SubmitAnswerView(APIView):
    """Отправка ответа на вопрос опроса."""

    permission_classes = [IsSurveyTaker]

    def post(self, request: Request, survey_id: int) -> Response:
        survey = get_survey_by_id(survey_id)
        session = get_or_create_session(user=request.user, survey=survey)

        if session.completed_at:
            raise ValidationError("Этот опрос уже завершён.")

        serializer = SubmitAnswerSerializer(
            data=request.data,
            context={"survey_id": survey_id},
        )
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        question = get_object_or_404(Question, pk=data["question_id"])
        submit_answer(
            session=session,
            question=question,
            selected_option_ids=data["selected_option_ids"],
            text_answer=data["text_answer"],
        )

        # Проверяем, завершён ли опрос после этого ответа
        next_q = get_next_unanswered_question(session=session, survey=survey)
        if next_q is None:
            mark_session_complete(session)

        return Response(
            {
                "completed": next_q is None,
                "next_question_url": (
                    request.build_absolute_uri(f"/api/surveys/{survey_id}/next-question/")
                    if next_q
                    else None
                ),
            },
            status=status.HTTP_201_CREATED,
        )


class SurveyProgressView(APIView):
    """Прогресс текущей сессии участника в опросе."""

    permission_classes = [IsSurveyTaker]

    def get(self, request: Request, survey_id: int) -> Response:
        survey = get_survey_by_id(survey_id)
        session = get_or_create_session(user=request.user, survey=survey)

        total = Question.objects.filter(survey=survey).count()
        answered = session.answers.count()

        serializer = SurveyProgressSerializer(
            {
                "answered": answered,
                "total": total,
                "completed_at": session.completed_at,
            }
        )
        return Response(serializer.data)
