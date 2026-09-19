from pypdf import PdfReader

def extract_text_from_pdf(file_path):
    """Extract text from a PDF file using PyPDF2."""
    try:
        reader = PdfReader(file_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""
        return text.strip()
    except Exception as e:
        return f"[Text extraction failed: {str(e)}]"