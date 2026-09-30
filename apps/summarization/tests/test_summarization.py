from unittest.mock import patch

import pytest
from rest_framework.test import APIClient

from apps.summarization.models import Summary
from apps.summarization.services import generate_summary


def summarize_url(document_id):
    return f"/api/documents/{document_id}/summarize/"


# ---------- Service ----------

@patch("apps.summarization.services.generate_content", return_value="- point")
def test_generate_summary_returns_model_output(mock_gen):
    assert generate_summary("some notes") == "- point"


@patch("apps.summarization.services.generate_content", return_value="- point")
def test_generate_summary_includes_notes_in_prompt(mock_gen):
    generate_summary("UNIQUE_MARKER_TEXT")
    prompt = mock_gen.call_args[0][0]
    assert "UNIQUE_MARKER_TEXT" in prompt


# ---------- View ----------

@pytest.mark.django_db
@patch("apps.summarization.views.generate_summary", return_value="## Mock Summary")
def test_summarize_creates_summary(mock_gen, auth_client, document):
    res = auth_client.post(summarize_url(document.id))

    assert res.status_code == 200
    assert res.data["content"] == "## Mock Summary"
    assert Summary.objects.get(document=document).content == "## Mock Summary"
    mock_gen.assert_called_once_with(document.extracted_text)


@pytest.mark.django_db
def test_resummarize_updates_existing_summary(auth_client, document):
    with patch("apps.summarization.views.generate_summary", return_value="first"):
        auth_client.post(summarize_url(document.id))
    with patch("apps.summarization.views.generate_summary", return_value="second"):
        res = auth_client.post(summarize_url(document.id))

    assert res.status_code == 200
    assert Summary.objects.filter(document=document).count() == 1
    assert Summary.objects.get(document=document).content == "second"


@pytest.mark.django_db
def test_summarize_404_for_other_users_document(auth_client, other_document):
    res = auth_client.post(summarize_url(other_document.id))
    assert res.status_code == 404


@pytest.mark.django_db
def test_summarize_400_without_extracted_text(auth_client, empty_document):
    res = auth_client.post(summarize_url(empty_document.id))
    assert res.status_code == 400


@pytest.mark.django_db
def test_summarize_requires_authentication(document):
    res = APIClient().post(summarize_url(document.id))
    assert res.status_code in (401, 403)


@pytest.mark.django_db
@patch("apps.summarization.views.generate_summary", side_effect=Exception("Gemini down"))
def test_summarize_returns_502_when_generation_fails(mock_gen, auth_client, document):
    res = auth_client.post(summarize_url(document.id))
    assert res.status_code == 502