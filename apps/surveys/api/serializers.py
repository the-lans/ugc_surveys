from django.contrib.auth import get_user_model
from rest_framework import serializers

from apps.surveys.constants import MAX_ANSWER_OPTIONS, QuestionType
from apps.surveys.db.surveys import has_responses
from apps.surveys.models import AnswerOption, Question, Survey, SurveySession

User = get_user_model()


class AnswerOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnswerOption
        fields = ["id", "text", "order"]


class AnswerOptionCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnswerOption
        fields = ["id", "text", "order"]

    def validate_order(self, value: int) -> int:
        if value < 1:
            raise serializers.ValidationError("Порядок должен быть больше 0.")
        return value


class QuestionSerializer(serializers.ModelSerializer):
    options = AnswerOptionSerializer(many=True, read_only=True)

    class Meta:
        model = Question
        fields = ["id", "text", "question_type", "order", "options"]


class QuestionCreateSerializer(serializers.ModelSerializer):
    options = AnswerOptionCreateSerializer(many=True, required=False)

    class Meta:
        model = Question
        fields = ["id", "text", "question_type", "order", "options"]

    def validate(self, attrs: dict) -> dict:
        qtype = attrs.get("question_type", QuestionType.SINGLE)
        options = attrs.get("options", [])

        if qtype == QuestionType.TEXT and options:
            raise serializers.ValidationError(
                "Вопрос типа 'text' не должен иметь вариантов ответа."
            )
        if qtype != QuestionType.TEXT and len(options) > MAX_ANSWER_OPTIONS:
            raise serializers.ValidationError(
                f"Максимальное количество вариантов: {MAX_ANSWER_OPTIONS}."
            )
        return attrs

    def create(self, validated_data: dict) -> Question:
        options_data = validated_data.pop("options", [])
        question = Question.objects.create(**validated_data)
        if options_data:
            AnswerOption.objects.bulk_create(
                [AnswerOption(question=question, **opt) for opt in options_data]
            )
        return question


class SurveyListSerializer(serializers.ModelSerializer):
    author = serializers.StringRelatedField()
    question_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Survey
        fields = ["id", "title", "author", "created_at", "is_active", "question_count"]


class SurveyDetailSerializer(serializers.ModelSerializer):
    author = serializers.StringRelatedField()
    questions = QuestionSerializer(many=True, read_only=True)
    is_locked = serializers.SerializerMethodField()

    class Meta:
        model = Survey
        fields = ["id", "title", "author", "created_at", "updated_at", "is_active", "is_locked", "questions"]

    def get_is_locked(self, obj: Survey) -> bool:
        return has_responses(obj)


class SurveyCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Survey
        fields = ["id", "title"]

    def create(self, validated_data: dict) -> Survey:
        validated_data["author"] = self.context["request"].user
        return Survey.objects.create(**validated_data)


class NextQuestionSerializer(serializers.Serializer):
    """Ответ на запрос следующего вопроса."""

    question_id = serializers.IntegerField(source="id")
    text = serializers.CharField()
    question_type = serializers.CharField()
    order = serializers.IntegerField()
    options = AnswerOptionSerializer(many=True)
    session_progress = serializers.SerializerMethodField()

    def get_session_progress(self, obj: Question) -> dict:
        session: SurveySession = self.context["session"]
        total = Question.objects.filter(survey=obj.survey).count()
        answered = session.answers.count()
        return {"answered": answered, "total": total}


class SubmitAnswerSerializer(serializers.Serializer):
    """Данные для отправки ответа на вопрос."""

    question_id = serializers.IntegerField()
    selected_option_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        default=list,
    )
    text_answer = serializers.CharField(required=False, allow_blank=True, default="")

    def validate_question_id(self, value: int) -> int:
        survey_id = self.context.get("survey_id")
        if not Question.objects.filter(pk=value, survey_id=survey_id).exists():
            raise serializers.ValidationError("Вопрос не найден в данном опросе.")
        return value


class ReorderItemSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    order = serializers.IntegerField(min_value=1)


class ReorderSerializer(serializers.Serializer):
    items = ReorderItemSerializer(many=True)

    def validate_items(self, items: list[dict]) -> list[dict]:
        orders = [item["order"] for item in items]
        if len(orders) != len(set(orders)):
            raise serializers.ValidationError("Порядковые номера должны быть уникальными.")
        return items


class SurveyProgressSerializer(serializers.Serializer):
    answered = serializers.IntegerField()
    total = serializers.IntegerField()
    completed_at = serializers.DateTimeField(allow_null=True)
