from ai_core.gemini_client import generate_content

def generate_summary(document_text):
    """Generate a bullet-point summary from note content."""
    prompt = f"""Summarize the following study notes into clear, concise bullet points. 
Focus on key concepts, definitions, and important facts. Keep it well-organized for quick revision.

Notes:
{document_text}
"""
    return generate_content(prompt)