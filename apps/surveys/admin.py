from django.contrib import admin

from apps.surveys.models import AnswerOption, Question, Survey, SurveySession, UserAnswer


class AnswerOptionInline(admin.TabularInline):
    model = AnswerOption
    extra = 3
    fields = ["order", "text"]
    ordering = ["order"]


class QuestionInline(admin.StackedInline):
    model = Question
    extra = 1
    fields = ["order", "text", "question_type"]
    ordering = ["order"]
    show_change_link = True


@admin.register(Survey)
class SurveyAdmin(admin.ModelAdmin):
    list_display = ["title", "author", "is_active", "created_at"]
    list_filter = ["is_active", "created_at"]
    search_fields = ["title", "author__username"]
    inlines = [QuestionInline]
    readonly_fields = ["created_at", "updated_at"]


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ["survey", "order", "question_type", "text"]
    list_filter = ["question_type", "survey"]
    inlines = [AnswerOptionInline]


@admin.register(SurveySession)
class SurveySessionAdmin(admin.ModelAdmin):
    list_display = ["user", "survey", "started_at", "completed_at"]
    list_filter = ["completed_at"]
    search_fields = ["user__username", "survey__title"]
    readonly_fields = ["started_at"]


@admin.register(UserAnswer)
class UserAnswerAdmin(admin.ModelAdmin):
    list_display = ["session", "question", "answered_at"]
    search_fields = ["session__user__username"]
    readonly_fields = ["answered_at"]
