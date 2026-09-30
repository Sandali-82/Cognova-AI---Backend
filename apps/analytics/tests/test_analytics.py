from datetime import timedelta

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from apps.analytics.services import (
    get_overall_stats,
    get_score_trend,
    get_subject_performance,
)
from apps.documents.models import Document
from apps.quizzes.models import Quiz, QuizAttempt

pytestmark = pytest.mark.django_db


def make_quiz(document, title="Quiz"):
    return Quiz.objects.create(document=document, title=title)


def make_document(user, subject):
    return Document.objects.create(
        user=user,
        title=f"{subject} notes",
        subject=subject,
        file="documents/x.pdf",
        extracted_text="text",
    )


def make_attempt(user, quiz, score, total, days_ago=0):
    attempt = QuizAttempt.objects.create(
        user=user, quiz=quiz, score=score, total_questions=total
    )
    # attempted_at is auto_now_add, so use update() to control the ordering
    QuizAttempt.objects.filter(pk=attempt.pk).update(
        attempted_at=timezone.now() - timedelta(days=days_ago)
    )
    return attempt


# ---------- Score trend ----------

def test_score_trend_empty_for_new_user(user):
    assert get_score_trend(user) == []


def test_score_trend_is_ordered_oldest_first_with_percentages(user, document):
    quiz = make_quiz(document, "Quiz A")
    make_attempt(user, quiz, 2, 2, days_ago=1)  # newer
    make_attempt(user, quiz, 1, 2, days_ago=5)  # older

    trend = get_score_trend(user)

    assert [t["percentage"] for t in trend] == [50.0, 100.0]
    assert trend[0]["quiz_title"] == "Quiz A"


def test_score_trend_handles_zero_questions(user, document):
    make_attempt(user, make_quiz(document), 0, 0)
    assert get_score_trend(user)[0]["percentage"] == 0


def test_score_trend_only_includes_own_attempts(user, other_user, document):
    quiz = make_quiz(document)
    make_attempt(user, quiz, 1, 2)
    make_attempt(other_user, quiz, 2, 2)

    trend = get_score_trend(user)

    assert len(trend) == 1
    assert trend[0]["score"] == 1


# ---------- Overall stats ----------

def test_overall_stats_empty_for_new_user(user):
    assert get_overall_stats(user) == {
        "total_attempts": 0,
        "average_percentage": 0,
        "best_quiz": None,
        "weakest_quiz": None,
    }


def test_overall_stats_values(user, document):
    strong = make_quiz(document, "Strong Quiz")
    weak = make_quiz(document, "Weak Quiz")
    make_attempt(user, strong, 3, 4)  # 75%
    make_attempt(user, weak, 1, 2)    # 50%

    stats = get_overall_stats(user)

    assert stats["total_attempts"] == 2
    # Pooled percentage: 4 correct out of 6 questions in total.
    # (The mean of the per-quiz percentages would be 62.5 instead.)
    assert stats["average_percentage"] == 66.7
    assert stats["best_quiz"] == {"quiz_title": "Strong Quiz", "percentage": 75.0}
    assert stats["weakest_quiz"] == {"quiz_title": "Weak Quiz", "percentage": 50.0}


def test_overall_stats_only_counts_own_attempts(user, other_user, document):
    quiz = make_quiz(document)
    make_attempt(user, quiz, 1, 2)
    make_attempt(other_user, quiz, 2, 2)

    stats = get_overall_stats(user)

    assert stats["total_attempts"] == 1
    assert stats["average_percentage"] == 50.0


# ---------- Subject performance ----------

def test_subject_performance_groups_and_sorts_weakest_first(user):
    bio = make_document(user, "Biology")
    chem = make_document(user, "Chemistry")
    phys = make_document(user, "Physics")
    make_attempt(user, make_quiz(bio), 1, 2)
    make_attempt(user, make_quiz(bio), 3, 4)   # Biology pooled: 4/6 = 66.7
    make_attempt(user, make_quiz(chem), 2, 2)  # Chemistry: 100
    make_attempt(user, make_quiz(phys), 0, 2)  # Physics: 0

    result = get_subject_performance(user)

    assert result == [
        {"subject": "Physics", "average_percentage": 0.0},
        {"subject": "Biology", "average_percentage": 66.7},
        {"subject": "Chemistry", "average_percentage": 100.0},
    ]


@pytest.mark.parametrize("empty_subject", [None, ""])
def test_subject_performance_labels_missing_subject_uncategorized(user, empty_subject):
    doc = make_document(user, empty_subject)
    make_attempt(user, make_quiz(doc), 1, 2)

    result = get_subject_performance(user)

    assert result == [{"subject": "Uncategorized", "average_percentage": 50.0}]


# ---------- Dashboard endpoint ----------

def test_dashboard_returns_all_sections(auth_client, user, document):
    make_attempt(user, make_quiz(document), 2, 2)

    res = auth_client.get("/api/analytics/dashboard/")

    assert res.status_code == 200
    assert {"overall_stats", "score_trend", "subject_performance"} <= set(res.data)


def test_dashboard_requires_authentication():
    res = APIClient().get("/api/analytics/dashboard/")
    assert res.status_code in (401, 403)