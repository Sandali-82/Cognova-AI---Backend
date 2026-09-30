import json
from unittest.mock import patch

import pytest

from apps.quizzes.services import generate_quiz_questions

SAMPLE_QUESTIONS = [
    {
        "question_text": "What is the powerhouse of the cell?",
        "option_a": "Mitochondria",
        "option_b": "Nucleus",
        "option_c": "Ribosome",
        "option_d": "Golgi body",
        "correct_option": "a",
        "explanation": "Mitochondria produce most of the cell's ATP.",
    }
]


@patch("apps.quizzes.services.generate_content")
def test_parses_plain_json(mock_gen):
    mock_gen.return_value = json.dumps(SAMPLE_QUESTIONS)
    result = generate_quiz_questions("some notes")
    assert result == SAMPLE_QUESTIONS


@patch("apps.quizzes.services.generate_content")
def test_strips_markdown_code_fences(mock_gen):
    mock_gen.return_value = "```json\n" + json.dumps(SAMPLE_QUESTIONS) + "\n```"
    result = generate_quiz_questions("some notes")
    assert result == SAMPLE_QUESTIONS


@patch("apps.quizzes.services.generate_content")
def test_raises_on_invalid_json(mock_gen):
    mock_gen.return_value = "Sorry, I cannot help with that."
    with pytest.raises(json.JSONDecodeError):
        generate_quiz_questions("some notes")


@patch("apps.quizzes.services.generate_content")
def test_document_text_is_included_in_prompt(mock_gen):
    mock_gen.return_value = json.dumps(SAMPLE_QUESTIONS)
    generate_quiz_questions("UNIQUE_MARKER_TEXT")
    prompt = mock_gen.call_args[0][0]
    assert "UNIQUE_MARKER_TEXT" in prompt