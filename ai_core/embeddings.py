import os
from google import genai
from google.genai import types

client = genai.Client(api_key=os.getenv('GEMINI_API_KEY'))

def generate_embedding(text):
    """Generate a vector embedding for the given text using Gemini's embedding model."""
    response = client.models.embed_content(
        model="gemini-embedding-001",
        contents=text,
        config=types.EmbedContentConfig(output_dimensionality=768)
    )
    return response.embeddings[0].values