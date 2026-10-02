from datetime import timedelta
from io import BytesIO
from unittest.mock import patch

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from pypdf import PdfWriter
from rest_framework.test import APIClient

from apps.documents.models import Document

pytestmark = pytest.mark.django_db

LIST_URL = "/api/documents/"
MAX_BYTES = 10 * 1024 * 1024


def detail_url(document_id):
    return f"{LIST_URL}{document_id}/"


@pytest.fixture(autouse=True)
def temp_media_root(settings, tmp_path):
    # Uploaded test files go to a temporary folder, not the real documents/ folder
    settings.MEDIA_ROOT = str(tmp_path)


@pytest.fixture
def mock_extract():
    with patch(
        "apps.documents.views.extract_text_from_pdf", return_value="Extracted text"
    ) as mock:
        yield mock


def make_pdf_bytes():
    """A real, readable (blank) one-page PDF."""
    writer = PdfWriter()
    writer.add_blank_page(width=200, height=200)
    buffer = BytesIO()
    writer.write(buffer)
    return buffer.getvalue()


def pdf_file(name="notes.pdf", content=None):
    if content is None:
        content = make_pdf_bytes()
    return SimpleUploadedFile(name, content, content_type="application/pdf")


# ---------- Upload ----------

def test_upload_creates_document_and_stores_extracted_text(auth_client, user, mock_extract):
    res = auth_client.post(
        LIST_URL,
        {"title": "Biology", "subject": "Science", "file": pdf_file()},
        format="multipart",
    )

    assert res.status_code == 201
    doc = Document.objects.get()
    assert doc.user == user
    assert doc.title == "Biology"
    assert doc.subject == "Science"
    assert doc.extracted_text == "Extracted text"
    mock_extract.assert_called_once()
    assert mock_extract.call_args[0][0].endswith(".pdf")


def test_upload_stores_the_complete_file(auth_client, mock_extract):
    # Guards the file.seek(0) after validation; without it an empty file is saved
    content = make_pdf_bytes()
    auth_client.post(
        LIST_URL, {"title": "T", "file": pdf_file(content=content)}, format="multipart"
    )

    doc = Document.objects.get()
    with doc.file.open("rb") as saved:
        assert saved.read() == content


def test_upload_ignores_client_supplied_extracted_text(auth_client, mock_extract):
    auth_client.post(
        LIST_URL,
        {"title": "T", "file": pdf_file(), "extracted_text": "HACKED"},
        format="multipart",
    )
    assert Document.objects.get().extracted_text == "Extracted text"


def test_upload_ignores_client_supplied_user(auth_client, user, other_user, mock_extract):
    res = auth_client.post(
        LIST_URL,
        {"title": "T", "file": pdf_file(), "user": other_user.id},
        format="multipart",
    )

    assert res.status_code == 201
    assert Document.objects.get().user == user


def test_subject_is_optional(auth_client, mock_extract):
    res = auth_client.post(
        LIST_URL, {"title": "T", "file": pdf_file()}, format="multipart"
    )

    assert res.status_code == 201
    assert not Document.objects.get().subject


def test_upload_accepts_uppercase_pdf_extension(auth_client, mock_extract):
    res = auth_client.post(
        LIST_URL, {"title": "T", "file": pdf_file("NOTES.PDF")}, format="multipart"
    )
    assert res.status_code == 201


def test_upload_rejects_non_pdf(auth_client, mock_extract):
    txt = SimpleUploadedFile("notes.txt", b"hello", content_type="text/plain")
    res = auth_client.post(LIST_URL, {"title": "T", "file": txt}, format="multipart")

    assert res.status_code == 400
    assert "file" in res.data
    assert Document.objects.count() == 0
    mock_extract.assert_not_called()


def test_upload_rejects_text_file_renamed_to_pdf(auth_client, mock_extract):
    fake = pdf_file("notes.pdf", content=b"just plain text, not a pdf")
    res = auth_client.post(LIST_URL, {"title": "T", "file": fake}, format="multipart")

    assert res.status_code == 400
    assert "file" in res.data
    assert Document.objects.count() == 0
    mock_extract.assert_not_called()


def test_upload_rejects_corrupt_pdf(auth_client, mock_extract):
    corrupt = pdf_file("broken.pdf", content=b"%PDF-1.4 but nothing valid after the header")
    res = auth_client.post(LIST_URL, {"title": "Broken", "file": corrupt}, format="multipart")

    assert res.status_code == 400
    assert "file" in res.data
    assert Document.objects.count() == 0  # nothing saved, so no error text becomes "notes"
    mock_extract.assert_not_called()


def test_upload_requires_file(auth_client):
    res = auth_client.post(LIST_URL, {"title": "T"}, format="multipart")

    assert res.status_code == 400
    assert "file" in res.data


@pytest.mark.parametrize("bad_title", ["", "   "])
def test_upload_rejects_blank_title(auth_client, bad_title):
    res = auth_client.post(
        LIST_URL, {"title": bad_title, "file": pdf_file()}, format="multipart"
    )

    assert res.status_code == 400
    assert "title" in res.data
    assert Document.objects.count() == 0


def test_upload_requires_title(auth_client):
    res = auth_client.post(LIST_URL, {"file": pdf_file()}, format="multipart")

    assert res.status_code == 400
    assert "title" in res.data


@patch("apps.documents.serializers.PdfReader")  # the size boundary is tested here, not parsing
def test_upload_accepts_file_of_exactly_10mb(mock_reader, auth_client, mock_extract):
    big = pdf_file(content=b"0" * MAX_BYTES)
    res = auth_client.post(LIST_URL, {"title": "T", "file": big}, format="multipart")
    assert res.status_code == 201


def test_upload_rejects_file_over_10mb(auth_client, mock_extract):
    too_big = pdf_file(content=b"0" * (MAX_BYTES + 1))
    res = auth_client.post(LIST_URL, {"title": "T", "file": too_big}, format="multipart")

    assert res.status_code == 400
    assert "file" in res.data
    assert Document.objects.count() == 0


# ---------- Update ----------

def test_replacing_file_re_extracts_text(auth_client, document):
    with patch(
        "apps.documents.views.extract_text_from_pdf", return_value="New text"
    ) as mock:
        res = auth_client.patch(
            detail_url(document.id), {"file": pdf_file("new.pdf")}, format="multipart"
        )

    assert res.status_code == 200
    mock.assert_called_once()
    document.refresh_from_db()
    assert document.extracted_text == "New text"


def test_updating_title_does_not_re_extract_text(auth_client, document):
    original_text = document.extracted_text
    with patch("apps.documents.views.extract_text_from_pdf") as mock:
        res = auth_client.patch(
            detail_url(document.id), {"title": "Renamed"}, format="json"
        )

    assert res.status_code == 200
    mock.assert_not_called()
    document.refresh_from_db()
    assert document.title == "Renamed"
    assert document.extracted_text == original_text


# ---------- List / retrieve / delete ----------

def test_list_returns_only_own_documents_newest_first(auth_client, user, other_document):
    old = Document.objects.create(user=user, title="Old", file="documents/old.pdf")
    Document.objects.create(user=user, title="New", file="documents/new.pdf")
    # uploaded_at is auto_now_add, so use update() to control the ordering
    Document.objects.filter(pk=old.pk).update(
        uploaded_at=timezone.now() - timedelta(days=2)
    )

    res = auth_client.get(LIST_URL)

    assert res.status_code == 200
    assert [d["title"] for d in res.data] == ["New", "Old"]


def test_retrieve_own_document(auth_client, document):
    res = auth_client.get(detail_url(document.id))

    assert res.status_code == 200
    assert res.data["title"] == document.title


def test_retrieve_other_users_document_returns_404(auth_client, other_document):
    res = auth_client.get(detail_url(other_document.id))
    assert res.status_code == 404


def test_delete_own_document(auth_client, document):
    res = auth_client.delete(detail_url(document.id))

    assert res.status_code == 204
    assert not Document.objects.filter(pk=document.pk).exists()


def test_delete_other_users_document_returns_404(auth_client, other_document):
    res = auth_client.delete(detail_url(other_document.id))

    assert res.status_code == 404
    assert Document.objects.filter(pk=other_document.pk).exists()


# ---------- Authentication ----------

@pytest.mark.parametrize("method", ["get", "post"])
def test_requires_authentication(method):
    res = getattr(APIClient(), method)(LIST_URL)
    assert res.status_code in (401, 403)