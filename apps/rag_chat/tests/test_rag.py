from types import SimpleNamespace
from unittest.mock import patch

import pytest
from rest_framework.test import APIClient

from apps.documents.models import Document
from apps.rag_chat.models import ChatMessage, NoteChunk
from apps.rag_chat.services import (
    answer_question,
    chunk_text,
    get_relevant_chunks,
    process_document_for_rag,
)


# NOTE: verify these two paths against apps/rag_chat/urls.py
def process_url(document_id):
    return f"/api/documents/{document_id}/process-for-chat/"


def chat_url(document_id):
    return f"/api/documents/{document_id}/chat/"


def vec(first):
    """768-dim vector with one non-zero value, easy to reason about."""
    return [float(first)] + [0.0] * 767


def words(n):
    return " ".join(f"w{i}" for i in range(n))


# ---------- chunk_text (pure function, no database) ----------

def test_chunk_text_empty_returns_no_chunks():
    assert chunk_text("") == []


def test_chunk_text_short_text_is_single_chunk():
    assert chunk_text("a few words here") == ["a few words here"]


def test_chunk_text_splits_with_overlap():
    chunks = chunk_text(words(1200))  # defaults: size 500, overlap 50

    assert len(chunks) == 3
    first, second = chunks[0].split(), chunks[1].split()
    assert len(first) == 500
    assert first[-50:] == second[:50]  # the overlapping words


def test_chunk_text_covers_every_word():
    text = words(1234)
    covered = set(" ".join(chunk_text(text)).split())
    assert covered == set(text.split())

def test_chunk_text_has_no_redundant_trailing_chunk():
    # The 2nd chunk (words 450-949) already reaches the end of 950 words,
    # but a 3rd chunk with words 900-949 is still added.
    assert len(chunk_text(words(950))) == 2


# ---------- process_document_for_rag ----------

@pytest.mark.django_db
@patch("apps.rag_chat.services.generate_embedding", return_value=vec(1))
def test_process_document_creates_chunks_with_embeddings(mock_embed, user):
    doc = Document.objects.create(
        user=user, title="Long", file="documents/l.pdf", extracted_text=words(1200)
    )

    process_document_for_rag(doc)

    chunks = list(NoteChunk.objects.filter(document=doc))
    assert [c.chunk_index for c in chunks] == [0, 1, 2]
    assert len(chunks[0].embedding) == 768
    assert mock_embed.call_count == 3


@pytest.mark.django_db
@patch("apps.rag_chat.services.generate_embedding", return_value=vec(1))
def test_reprocessing_replaces_old_chunks(mock_embed, user):
    doc = Document.objects.create(
        user=user, title="Long", file="documents/l.pdf", extracted_text=words(1200)
    )

    process_document_for_rag(doc)
    process_document_for_rag(doc)

    assert NoteChunk.objects.filter(document=doc).count() == 3


# ---------- get_relevant_chunks (real pgvector query) ----------

@pytest.mark.django_db
@patch("apps.rag_chat.services.generate_embedding", return_value=vec(4))
def test_get_relevant_chunks_orders_by_distance_and_limits(mock_embed, document, other_document):
    # Question vector is at 4: "closest" (5) is 1 away, "medium" (1) is 3 away, "far" (10) is 6 away
    NoteChunk.objects.create(document=document, chunk_text="medium", chunk_index=0, embedding=vec(1))
    NoteChunk.objects.create(document=document, chunk_text="closest", chunk_index=1, embedding=vec(5))
    NoteChunk.objects.create(document=document, chunk_text="far", chunk_index=2, embedding=vec(10))
    # A perfect match, but it belongs to another document, so it must be excluded
    NoteChunk.objects.create(document=other_document, chunk_text="other doc", chunk_index=0, embedding=vec(4))

    result = get_relevant_chunks(document, "question", top_k=2)

    assert [c.chunk_text for c in result] == ["closest", "medium"]
    mock_embed.assert_called_once_with("question")


# ---------- answer_question ----------

@patch("apps.rag_chat.services.generate_content", return_value="Mock answer")
@patch("apps.rag_chat.services.get_relevant_chunks")
def test_answer_question_uses_retrieved_chunks_as_context(mock_chunks, mock_gen):
    mock_chunks.return_value = [
        SimpleNamespace(chunk_text="CHUNK_ONE"),
        SimpleNamespace(chunk_text="CHUNK_TWO"),
    ]

    answer = answer_question(SimpleNamespace(), "What is X?")

    assert answer == "Mock answer"
    prompt = mock_gen.call_args[0][0]
    assert "CHUNK_ONE" in prompt
    assert "CHUNK_TWO" in prompt
    assert "What is X?" in prompt


# ---------- Process view ----------

@pytest.mark.django_db
@patch("apps.rag_chat.views.process_document_for_rag")
def test_process_view_processes_document(mock_process, auth_client, document):
    res = auth_client.post(process_url(document.id))

    assert res.status_code == 200
    mock_process.assert_called_once_with(document)


@pytest.mark.django_db
def test_process_view_404_for_other_users_document(auth_client, other_document):
    res = auth_client.post(process_url(other_document.id))
    assert res.status_code == 404


@pytest.mark.django_db
def test_process_view_400_without_extracted_text(auth_client, empty_document):
    res = auth_client.post(process_url(empty_document.id))
    assert res.status_code == 400


@pytest.mark.django_db
def test_process_view_requires_authentication(document):
    res = APIClient().post(process_url(document.id))
    assert res.status_code in (401, 403)


# ---------- Chat view ----------

@pytest.mark.django_db
@patch("apps.rag_chat.views.answer_question", return_value="Mock answer")
def test_chat_returns_answer_and_saves_message(mock_answer, auth_client, user, document):
    res = auth_client.post(
        chat_url(document.id), {"question": "  What is a cell?  "}, format="json"
    )

    assert res.status_code == 200
    assert res.data["answer"] == "Mock answer"
    mock_answer.assert_called_once_with(document, "What is a cell?")  # stripped
    message = ChatMessage.objects.get()
    assert message.user == user
    assert message.question == "What is a cell?"
    assert message.answer == "Mock answer"


@pytest.mark.django_db
@pytest.mark.parametrize(
    "payload",
    [{}, {"question": ""}, {"question": "   "}, {"question": "x" * 501}],
)
@patch("apps.rag_chat.views.answer_question")
def test_chat_400_for_invalid_question(mock_answer, auth_client, document, payload):
    res = auth_client.post(chat_url(document.id), payload, format="json")

    assert res.status_code == 400
    assert ChatMessage.objects.count() == 0
    mock_answer.assert_not_called()  # invalid input must never reach Gemini


@pytest.mark.django_db
@patch("apps.rag_chat.views.answer_question", return_value="ok")
def test_chat_accepts_question_of_exactly_500_characters(mock_answer, auth_client, document):
    res = auth_client.post(chat_url(document.id), {"question": "x" * 500}, format="json")
    assert res.status_code == 200


@pytest.mark.django_db
@patch("apps.rag_chat.views.answer_question")
def test_chat_404_for_other_users_document(mock_answer, auth_client, other_document):
    res = auth_client.post(chat_url(other_document.id), {"question": "Hi"}, format="json")

    assert res.status_code == 404
    mock_answer.assert_not_called()


@pytest.mark.django_db
def test_chat_requires_authentication(document):
    res = APIClient().post(chat_url(document.id), {"question": "Hi"}, format="json")
    assert res.status_code in (401, 403)


@pytest.mark.django_db
@patch("apps.rag_chat.views.answer_question", side_effect=Exception("Gemini down"))
def test_chat_returns_502_when_generation_fails(mock_answer, auth_client, document):
    res = auth_client.post(chat_url(document.id), {"question": "Hi"}, format="json")

    assert res.status_code == 502
    assert ChatMessage.objects.count() == 0