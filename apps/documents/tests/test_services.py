from unittest.mock import MagicMock, patch

from pypdf import PdfWriter

from apps.documents.services import extract_text_from_pdf


def fake_page(text):
    page = MagicMock()
    page.extract_text.return_value = text
    return page


@patch("apps.documents.services.PdfReader")
def test_joins_text_from_all_pages(mock_reader):
    mock_reader.return_value.pages = [fake_page("Hello "), fake_page("World")]
    assert extract_text_from_pdf("any.pdf") == "Hello World"


@patch("apps.documents.services.PdfReader")
def test_page_without_text_is_treated_as_empty(mock_reader):
    # pypdf returns None/"" for image-only pages
    mock_reader.return_value.pages = [fake_page(None), fake_page("Text")]
    assert extract_text_from_pdf("any.pdf") == "Text"


@patch("apps.documents.services.PdfReader")
def test_result_is_stripped(mock_reader):
    mock_reader.return_value.pages = [fake_page("  padded text  \n")]
    assert extract_text_from_pdf("any.pdf") == "padded text"


def test_blank_pdf_returns_empty_string(tmp_path):
    writer = PdfWriter()
    writer.add_blank_page(width=200, height=200)
    path = tmp_path / "blank.pdf"
    with open(path, "wb") as f:
        writer.write(f)

    assert extract_text_from_pdf(str(path)) == ""


def test_corrupt_file_returns_failure_message(tmp_path):
    path = tmp_path / "broken.pdf"
    path.write_bytes(b"this is not a pdf")

    assert extract_text_from_pdf(str(path)).startswith("[Text extraction failed:")


def test_missing_file_returns_failure_message(tmp_path):
    result = extract_text_from_pdf(str(tmp_path / "does-not-exist.pdf"))
    assert result.startswith("[Text extraction failed:")