import pytest
from django.contrib.auth.models import User
from rest_framework.test import APIClient

from apps.documents.models import Document
from apps.quizzes.models import Quiz, QuizQuestion


@pytest.fixture
def user(db):
    return User.objects.create_user(username="tester", password="pass12345")


@pytest.fixture
def other_user(db):
    return User.objects.create_user(username="other", password="pass12345")


@pytest.fixture
def auth_client(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.fixture
def document(user):
    # The file path is just a string here, so no real file is written to disk
    return Document.objects.create(
        user=user,
        title="Biology Notes",
        subject="Biology",
        file="documents/test.pdf",
        extracted_text="Mitochondria is the powerhouse of the cell.",
    )


@pytest.fixture
def quiz(document):
    quiz = Quiz.objects.create(document=document, title="Quiz - Biology Notes")
    for text, correct in [("Q1", "a"), ("Q2", "b"), ("Q3", "c")]:
        QuizQuestion.objects.create(
            quiz=quiz,
            question_text=text,
            option_a="A",
            option_b="B",
            option_c="C",
            option_d="D",
            correct_option=correct,
            explanation=f"Explanation for {text}",
        )
    return quiz