import json
from ai_core.gemini_client import generate_content


def generate_quiz_questions(document_text, num_questions=5):
    """Generate MCQ questions from document text using Gemini. Returns a list of dicts."""
    prompt = f"""Based on the following study notes, create {num_questions} multiple-choice questions to test understanding.

Return ONLY a valid JSON array (no markdown formatting, no code blocks, no extra text) in exactly this format:
[
  {{
    "question_text": "...",
    "option_a": "...",
    "option_b": "...",
    "option_c": "...",
    "option_d": "...",
    "correct_option": "a",
    "explanation": "..."
  }}
]

The "correct_option" must be one of: a, b, c, d.
The "explanation" should briefly explain why the correct answer is right.

Notes:
{document_text}
"""
    raw_response = generate_content(prompt)
    cleaned = _clean_json_response(raw_response)
    return json.loads(cleaned)


def _clean_json_response(text):
    """Strip markdown code fences if Gemini wraps the JSON in ```json ... ``` """
    text = text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    return text.strip()