from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.surveys.api.views import (
    AvailableSurveysView,
    NextQuestionView,
    QuestionViewSet,
    ReorderOptionsView,
    ReorderQuestionsView,
    SubmitAnswerView,
    SurveyProgressView,
    SurveyStatsView,
    SurveyViewSet,
)

router = DefaultRouter()
router.register(r"surveys", SurveyViewSet, basename="survey")

question_list = QuestionViewSet.as_view({"get": "list", "post": "create"})
question_detail = QuestionViewSet.as_view(
    {"get": "retrieve", "patch": "partial_update", "delete": "destroy"}
)

urlpatterns = [
    path("surveys/available/", AvailableSurveysView.as_view(), name="survey-available"),
    path("", include(router.urls)),
    # Для участников
    path(
        "surveys/<int:survey_id>/next-question/",
        NextQuestionView.as_view(),
        name="survey-next-question",
    ),
    path("surveys/<int:survey_id>/answer/", SubmitAnswerView.as_view(), name="survey-answer"),
    path(
        "surveys/<int:survey_id>/progress/",
        SurveyProgressView.as_view(),
        name="survey-progress",
    ),
    # Для создателей — управление вопросами
    path("surveys/<int:survey_id>/stats/", SurveyStatsView.as_view(), name="survey-stats"),
    path("surveys/<int:survey_id>/questions/", question_list, name="question-list"),
    path("surveys/<int:survey_id>/questions/<int:pk>/", question_detail, name="question-detail"),
    path(
        "surveys/<int:survey_id>/questions/reorder/",
        ReorderQuestionsView.as_view(),
        name="question-reorder",
    ),
    path(
        "questions/<int:question_id>/options/reorder/",
        ReorderOptionsView.as_view(),
        name="option-reorder",
    ),
]
