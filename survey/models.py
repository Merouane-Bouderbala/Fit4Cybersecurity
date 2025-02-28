from __future__ import annotations

import uuid
from typing import Any

from django.db import models
from django.db.models import Sum
from django.utils.translation import gettext_lazy as _
from django_countries import countries

from csskp.settings import CUSTOM
from csskp.settings import LANGUAGE_CODE
from csskp.settings import LANGUAGES
from survey.globals import ANSWER_TYPES
from survey.globals import QUESTION_TYPES
from survey.globals import SERVICE_TARGETS

# import global constants

# Create your models here.

# REMEMBER: use models.UUIDField for every object

"""
There are 3 types of questions:
 1. Multiple choice
 2. Single Choice
 3. Slider - integer (minimum int to max int - single steps)

Each question belongs to a section
Each question has a Service Category - helps with assigning companies later
Each question has multiple answers assigned to it
 - for multiple choices for examples
Each question has a type (see above)
Each question has only a question ID - multilanguage
"""

LOCAL_DEFAULT_LANG = LANGUAGE_CODE
SURVEY_STATUS_IN_PROGRESS = 1
SURVEY_STATUS_UNDER_REVIEW = 2
SURVEY_STATUS_FINISHED = 3
CONTEXT_SECTION_LABEL = "__context"


class RightMixin:
    @staticmethod
    def _fields_base_write():
        return set()

    @staticmethod
    def _fields_base_read():
        return {"id"}

    @classmethod
    def fields_base_write(cls):
        return cls._fields_base_write()

    @classmethod
    def fields_base_read(cls):
        return cls._fields_base_write().union(cls._fields_base_read())

    def dump(self):
        dict = {k: getattr(self, k) for k in self.fields_base_read()}
        # if hasattr(self, "__dump__"):
        #     dict = self.__dump__()
        for key, value in dict.items():
            if isinstance(value, models.Model):
                if hasattr(value, "dump"):
                    dict[key] = value.dump()
                else:
                    dict[key] = str(value)
            elif value.__class__.__name__ == "ManyRelatedManager":
                if hasattr(value, "__dump__"):
                    dict[key] = [elem.__dump__() for elem in value.all()]
                else:
                    dict[key] = [str(elem) for elem in value.all()]
        return dict


class ActiveModelManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_active=True)


class SurveyQuestionServiceCategory(models.Model):
    # QuestionCatID

    label = models.TextField()

    def __str__(self):
        return self.label


class SurveySection(models.Model):
    # Section ID
    # Section title

    label = models.TextField()

    def __repr__(self):
        return self.label

    def __str__(self):
        return self.label


class SurveyQuestion(models.Model, RightMixin):
    # Question id --> translation in other table
    # QuestionCatID
    # Section ID
    all_objects = models.Manager()
    objects = ActiveModelManager()

    service_category = models.ForeignKey(
        SurveyQuestionServiceCategory, on_delete=models.CASCADE
    )
    section = models.ForeignKey(SurveySection, on_delete=models.CASCADE)
    label = models.TextField()
    tooltip = models.TextField(null=False, blank=True, default="")
    qtype = models.CharField(
        max_length=2, choices=QUESTION_TYPES, default=QUESTION_TYPES[0][0]
    )
    qindex = models.IntegerField(unique=True)
    maxPoints = models.IntegerField(default=10)
    answers_order = models.CharField(max_length=100, default="aindex")
    is_active = models.BooleanField(default=True)

    @staticmethod
    def _fields_base_read():
        return {
            "label",
            "section",
            "service_category",
            "qtype",
            "qindex",
            "maxPoints",
        }

    def __str__(self):
        return self.label

    def is_context(self) -> bool:
        return self.section.label == CONTEXT_SECTION_LABEL


class SurveyQuestionAnswer(models.Model, RightMixin):
    # Answer id --> translation in other table
    # Question id --> can be 1-question to multi-answers
    all_objects = models.Manager()
    objects = ActiveModelManager()

    question = models.ForeignKey(SurveyQuestion, on_delete=models.CASCADE)
    label = models.TextField()
    value = models.CharField(max_length=50, null=True, blank=True, default=None)
    tooltip = models.TextField(null=False, blank=True, default="")
    aindex = models.IntegerField()
    uniqueAnswer = models.BooleanField(default=False)
    score = models.IntegerField(default=0)
    bonus_points = models.IntegerField(default=0)
    atype = models.CharField(
        max_length=2, choices=ANSWER_TYPES, default=ANSWER_TYPES[0][0]
    )
    dependant_answers = models.ManyToManyField("self", blank=True)
    is_active = models.BooleanField(default=True)

    @staticmethod
    def _fields_base_read():
        return {
            "label",
            "tooltip",
            "aindex",
            "uniqueAnswer",
            "score",
            "bonus_points",
            "atype",
            "dependant_answers",
        }

    def __str__(self):
        return self.label

    class Meta:
        unique_together = ("aindex", "question")


class SurveyAnswerQuestionMap(models.Model):
    # Used to define answers -> questions sequences.
    # For ex. answer ID 1 can be linked with multiple questions (IDs: 2, 3, 4)
    #  with specific order (1, 2, 3). That means, if user selected answer ID 1
    # it leads him/her to the sequence of linked questions (IDs 2, 3, 4)
    # In case if sub answers has defined sequence (e.g. question ID 3 has an answer 10,
    # which is linked to question ID 7), then sub question (ID 7) will be displayed before
    #  the rest of the questions in that sequence (before ID 4).

    answer = models.ForeignKey(SurveyQuestionAnswer, on_delete=models.CASCADE)
    question = models.ForeignKey(
        SurveyQuestion,
        on_delete=models.CASCADE,
    )
    branch = models.SmallIntegerField(null=False, default=0)
    level = models.SmallIntegerField(null=False, default=1)
    order = models.IntegerField()

    class Meta:
        unique_together = ("answer", "question", "branch")

    def __str__(self):
        return str(self.answer) + "_" + str(self.question)


class SurveyUser(models.Model):
    # user ID - Hash or UUID
    # Sector
    # OtherSector Description
    # number of employees

    user_id = models.UUIDField(default=uuid.uuid4, unique=True)
    chosen_lang = models.CharField(
        max_length=2, choices=LANGUAGES, default=LOCAL_DEFAULT_LANG
    )
    current_question = models.ForeignKey(SurveyQuestion, on_delete=models.CASCADE)
    status = models.SmallIntegerField(default=SURVEY_STATUS_IN_PROGRESS)
    created_at = models.DateField(auto_now_add=True, blank=True)
    updated_at = models.DateField(auto_now=True, blank=True)

    def __str__(self):
        return str(self.user_id)

    def is_survey_in_progress(self) -> bool:
        return self.status == SURVEY_STATUS_IN_PROGRESS

    def is_survey_under_review(self) -> bool:
        return self.status == SURVEY_STATUS_UNDER_REVIEW

    def is_survey_finished(self) -> bool:
        return self.status == SURVEY_STATUS_FINISHED

    def get_all_context_answers(self) -> dict[str, Any]:
        result = {}
        user_answers = self.surveyuseranswer_set.filter(
            answer__question__section__label=CONTEXT_SECTION_LABEL
        )
        for user_answer in user_answers:
            if user_answer.answer.question.qtype == "CL":
                value = _(dict(countries)[user_answer.uvalue])
            else:
                value = _(user_answer.answer.label)
            result[_(user_answer.answer.question.label)] = value

        return result

    def __get_context_answer_by_question_label(
        self, question_label: str
    ) -> SurveyUserAnswer | None:
        try:
            return self.surveyuseranswer_set.get(
                answer__question__section__label=CONTEXT_SECTION_LABEL,
                answer__question__label=question_label,
            )
        except SurveyUserAnswer.DoesNotExist:
            return None

    def get_employees_number_code(self) -> str:
        try:
            number_employees_question_label = SurveyQuestion.objects.get(
                label="How many employees?", section__label=CONTEXT_SECTION_LABEL
            ).label
        except SurveyQuestion.DoesNotExist:
            return ""

        user_answer = self.__get_context_answer_by_question_label(
            number_employees_question_label
        )

        return user_answer.uvalue if user_answer is not None else ""

    def get_employees_number_label(self) -> str:
        try:
            number_employees_question_label = SurveyQuestion.objects.get(
                label="How many employees?", section__label=CONTEXT_SECTION_LABEL
            ).label
        except SurveyQuestion.DoesNotExist:
            return ""

        user_answer = self.__get_context_answer_by_question_label(
            number_employees_question_label
        )

        return user_answer.answer.label if user_answer is not None else ""

    def get_sector_label(self) -> str:
        try:
            sector_question_label = SurveyQuestion.objects.get(
                label="What is your sector?", section__label=CONTEXT_SECTION_LABEL
            ).label
        except SurveyQuestion.DoesNotExist:
            return ""

        user_answer = self.__get_context_answer_by_question_label(sector_question_label)

        return user_answer.answer.label if user_answer is not None else ""

    def get_country_code(self) -> str:
        try:
            country_question_label = SurveyQuestion.objects.get(
                label__contains="your country", section__label=CONTEXT_SECTION_LABEL
            ).label
        except SurveyUser.DoesNotExist:
            return ""

        user_answer = self.__get_context_answer_by_question_label(
            country_question_label
        )

        return user_answer.uvalue if user_answer is not None else ""

    def get_evaluations_by_section(self, max_evaluations_per_section) -> list[int]:
        user_evaluations: list[int] = []
        chart_exclude_sections = ["__context"]

        if "chart_exclude_sections" in CUSTOM.keys():
            chart_exclude_sections = (
                chart_exclude_sections + CUSTOM["chart_exclude_sections"]
            )

        user_answers = (
            SurveyUserAnswer.objects.exclude(
                answer__question__section__label__in=chart_exclude_sections
            )
            .filter(user=self, uvalue=1)
            .values("answer__question__section_id")
            .order_by("answer__question__section_id")
            .annotate(score=Sum("answer__score"))
        )

        for answer in user_answers:
            if max_evaluations_per_section[answer["answer__question__section_id"]] > 0:
                user_evaluations.append(
                    round(
                        answer["score"]
                        * 100
                        / max_evaluations_per_section[
                            answer["answer__question__section_id"]
                        ]
                    )
                )
            else:
                user_evaluations.append(0)

        return user_evaluations

    def get_evaluations_by_category(self, max_evaluations_per_category) -> list[int]:
        user_evaluations: list[int] = []
        chart_exclude_sections = ["__context"]

        if "chart_exclude_sections" in CUSTOM.keys():
            chart_exclude_sections = (
                chart_exclude_sections + CUSTOM["chart_exclude_sections"]
            )

        user_answers = (
            SurveyUserAnswer.objects.exclude(
                answer__question__section__label__in=chart_exclude_sections
            )
            .filter(user=self, uvalue=1)
            .values("answer__question__service_category_id")
            .order_by("answer__question__service_category_id")
            .annotate(score=Sum("answer__score"))
        )

        for answer in user_answers:
            if (
                max_evaluations_per_category[
                    answer["answer__question__service_category_id"]
                ]
                > 0
            ):
                user_evaluations.append(
                    round(
                        answer["score"]
                        * 100
                        / max_evaluations_per_category[
                            answer["answer__question__service_category_id"]
                        ]
                    )
                )
            else:
                user_evaluations.append(0)

        return user_evaluations


class SurveyUserQuestionSequence(models.Model):
    user = models.ForeignKey(SurveyUser, on_delete=models.CASCADE)
    question = models.ForeignKey(
        SurveyQuestion,
        on_delete=models.CASCADE,
    )
    branch = models.SmallIntegerField(null=False, default=0)
    level = models.SmallIntegerField(null=False, default=1)
    index = models.IntegerField(default=1)
    has_been_answered = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return (
            str(self.question)
            + "_"
            + str(self.branch)
            + "_"
            + str(self.level)
            + "_"
            + str(self.index)
        )

    class Meta:
        unique_together = ("user", "question", "branch")


class SurveyUserAnswer(models.Model):
    # AnswerID
    # AnswerListID
    user = models.ForeignKey(SurveyUser, on_delete=models.CASCADE)
    answer = models.ForeignKey(SurveyQuestionAnswer, on_delete=models.CASCADE)
    # 0, 1 for true, false selections,
    # and real value (SurveyQuestionAnswer.value or country code) for qtype = SO|CL
    uvalue = models.CharField(default="0", max_length=100, null=False)
    content = models.TextField(null=False, blank=True, default="")

    def __str__(self):
        return str(self.answer)


class SurveyUserFeedback(models.Model):
    user = models.ForeignKey(SurveyUser, on_delete=models.CASCADE)
    question = models.ForeignKey(SurveyQuestion, on_delete=models.CASCADE, null=True)
    feedback = models.TextField(null=False, blank=True, default="")

    def __str__(self):
        return str(self.feedback)


class Recommendations(models.Model, RightMixin):
    label = models.TextField()
    min_e_count = models.CharField(max_length=2, default="a")
    max_e_count = models.CharField(max_length=2, default="z")
    sector = models.CharField(max_length=4, null=True, blank=True, default=None)
    forAnswer = models.ForeignKey(SurveyQuestionAnswer, on_delete=models.CASCADE)
    answerChosen = models.BooleanField(default=False)
    categories = models.ManyToManyField(SurveyQuestionServiceCategory, blank=True)

    @staticmethod
    def _fields_base_read():
        return {"label", "min_e_count", "max_e_count", "sector", "answerChosen"}

    def __str__(self):
        return self.label


class Company(models.Model):
    # company name
    # company contact email
    # company contact phone
    # company contact address
    # company special notes # what is important to know: "We only fix MACs ;)"
    name = models.CharField(max_length=128)
    contact_email = models.EmailField()
    contact_tel = models.TextField(max_length=32)
    contact_address_street = models.CharField(max_length=128)
    contact_address_city = models.CharField(max_length=64)
    contact_address_country = models.CharField(max_length=64)
    contact_address_number = models.IntegerField()
    contact_address_postcode = models.CharField(max_length=10)
    notes = models.TextField()


class CompanyService(models.Model):
    # SurveyQuestionServiceCategory connection
    # Company
    # for who are there services
    # SME
    # Corporate
    # private
    category = models.ForeignKey(
        SurveyQuestionServiceCategory, on_delete=models.CASCADE
    )
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    target = models.CharField(max_length=3, choices=SERVICE_TARGETS)
