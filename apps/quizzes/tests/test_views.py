from unittest.mock import patch

import pytest
from rest_framework.test import APIClient

from apps.documents.models import Document
from apps.quizzes.models import Quiz, QuizQuestion, QuizAttempt

MOCK_QUESTIONS = [
    {
        "question_text": "Q1",
        "option_a": "A", "option_b": "B", "option_c": "C", "option_d": "D",
        "correct_option": "a",
        "explanation": "Because A.",
    },
    {
        "question_text": "Q2",
        "option_a": "A", "option_b": "B", "option_c": "C", "option_d": "D",
        "correct_option": "b",
        "explanation": "Because B.",
    },
]


# ---------- Generate quiz ----------

@pytest.mark.django_db
@patch("apps.quizzes.views.generate_quiz_questions", return_value=MOCK_QUESTIONS)
def test_generate_quiz_creates_quiz_and_questions(mock_gen, auth_client, document):
    res = auth_client.post(f"/api/documents/{document.id}/generate-quiz/")

    assert res.status_code == 201
    assert Quiz.objects.count() == 1
    assert QuizQuestion.objects.count() == 2
    mock_gen.assert_called_once_with(document.extracted_text)


@pytest.mark.django_db
@patch("apps.quizzes.views.generate_quiz_questions", return_value=MOCK_QUESTIONS)
def test_generate_quiz_hides_answers_in_response(mock_gen, auth_client, document):
    res = auth_client.post(f"/api/documents/{document.id}/generate-quiz/")

    for question in res.data["questions"]:
        assert "correct_option" not in question
        assert "explanation" not in question


@pytest.mark.django_db
def test_generate_quiz_404_for_other_users_document(auth_client, other_user):
    other_doc = Document.objects.create(
        user=other_user, title="Secret", file="documents/x.pdf", extracted_text="text"
    )
    res = auth_client.post(f"/api/documents/{other_doc.id}/generate-quiz/")
    assert res.status_code == 404


@pytest.mark.django_db
def test_generate_quiz_400_without_extracted_text(auth_client, user):
    doc = Document.objects.create(
        user=user, title="Empty", file="documents/x.pdf", extracted_text=""
    )
    res = auth_client.post(f"/api/documents/{doc.id}/generate-quiz/")
    assert res.status_code == 400


@pytest.mark.django_db
@patch("apps.quizzes.views.generate_quiz_questions", side_effect=Exception("Gemini down"))
def test_generate_quiz_502_when_generation_fails(mock_gen, auth_client, document):
    res = auth_client.post(f"/api/documents/{document.id}/generate-quiz/")

    assert res.status_code == 502
    assert Quiz.objects.count() == 0  # nothing saved on failure


@pytest.mark.django_db
def test_generate_quiz_requires_authentication(document):
    res = APIClient().post(f"/api/documents/{document.id}/generate-quiz/")
    assert res.status_code in (401, 403)


# ---------- Submit quiz ----------

def _answers(quiz, selections):
    """Build the {question_id: option} payload in question order."""
    questions = list(quiz.questions.order_by("id"))
    return {str(q.id): sel for q, sel in zip(questions, selections) if sel is not None}


@pytest.mark.django_db
def test_submit_all_correct(auth_client, quiz):
    payload = {"answers": _answers(quiz, ["a", "b", "c"])}
    res = auth_client.post(f"/api/quizzes/{quiz.id}/submit/", payload, format="json")

    assert res.status_code == 200
    assert res.data["score"] == 3
    assert res.data["total_questions"] == 3
    assert all(f["is_correct"] for f in res.data["feedback"])


@pytest.mark.django_db
def test_submit_partial_score_and_feedback(auth_client, quiz):
    # Q1 correct, Q2 wrong (picked "a" instead of "b"), Q3 correct
    payload = {"answers": _answers(quiz, ["a", "a", "c"])}
    res = auth_client.post(f"/api/quizzes/{quiz.id}/submit/", payload, format="json")

    assert res.status_code == 200
    assert res.data["score"] == 2
    wrong = [f for f in res.data["feedback"] if not f["is_correct"]]
    assert len(wrong) == 1
    assert wrong[0]["selected_option"] == "a"
    assert wrong[0]["correct_option"] == "b"
    assert wrong[0]["explanation"] == "Explanation for Q2"


@pytest.mark.django_db
def test_submit_unanswered_question_counts_as_incorrect(auth_client, quiz):
    payload = {"answers": _answers(quiz, ["a", None, None])}
    res = auth_client.post(f"/api/quizzes/{quiz.id}/submit/", payload, format="json")

    assert res.status_code == 200
    assert res.data["score"] == 1
    unanswered = [f for f in res.data["feedback"] if f["selected_option"] is None]
    assert len(unanswered) == 2


@pytest.mark.django_db
def test_submit_saves_attempt_for_current_user(auth_client, user, quiz):
    payload = {"answers": _answers(quiz, ["a", "b", "c"])}
    res = auth_client.post(f"/api/quizzes/{quiz.id}/submit/", payload, format="json")

    attempt = QuizAttempt.objects.get(id=res.data["attempt_id"])
    assert attempt.user == user
    assert attempt.score == 3
    assert attempt.total_questions == 3


@pytest.mark.django_db
@pytest.mark.parametrize("bad_answers", [{}, [], "abc", None])
def test_submit_400_for_invalid_answers(auth_client, quiz, bad_answers):
    res = auth_client.post(
        f"/api/quizzes/{quiz.id}/submit/", {"answers": bad_answers}, format="json"
    )
    assert res.status_code == 400
    assert QuizAttempt.objects.count() == 0


@pytest.mark.django_db
def test_submit_404_for_missing_quiz(auth_client):
    res = auth_client.post(
        "/api/quizzes/99999/submit/", {"answers": {"1": "a"}}, format="json"
    )
    assert res.status_code == 404


@pytest.mark.django_db
def test_submit_400_for_quiz_without_questions(auth_client, document):
    empty_quiz = Quiz.objects.create(document=document, title="Empty")
    res = auth_client.post(
        f"/api/quizzes/{empty_quiz.id}/submit/", {"answers": {"1": "a"}}, format="json"
    )
    assert res.status_code == 400


@pytest.mark.django_db
def test_submit_rejects_other_users_quiz(other_user, quiz):
    client = APIClient()
    client.force_authenticate(user=other_user)
    payload = {"answers": _answers(quiz, ["a", "b", "c"])}
    res = client.post(f"/api/quizzes/{quiz.id}/submit/", payload, format="json")
    assert res.status_code in (403, 404)