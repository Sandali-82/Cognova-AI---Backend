from apps.rag_chat.models import NoteChunk
from ai_core.embeddings import generate_embedding
from ai_core.gemini_client import generate_content
from pgvector.django import L2Distance


def chunk_text(text, chunk_size=500, overlap=50):
    """Split document text into overlapping chunks for embedding."""
    words = text.split()
    chunks = []
    start = 0

    while start < len(words):
        end = start + chunk_size
        chunk = " ".join(words[start:end])
        chunks.append(chunk)
        start += chunk_size - overlap

    return chunks


def process_document_for_rag(document):
    """Chunk the document text, generate embeddings, and store as NoteChunks."""
    # Clear old chunks if reprocessing
    NoteChunk.objects.filter(document=document).delete()

    chunks = chunk_text(document.extracted_text)

    for index, chunk in enumerate(chunks):
        embedding = generate_embedding(chunk)
        NoteChunk.objects.create(
            document=document,
            chunk_text=chunk,
            chunk_index=index,
            embedding=embedding
        )


def get_relevant_chunks(document, question, top_k=3):
    """Retrieve the top_k most relevant chunks for a question using vector similarity."""
    question_embedding = generate_embedding(question)

    chunks = NoteChunk.objects.filter(document=document).order_by(
        L2Distance('embedding', question_embedding)
    )[:top_k]

    return chunks


def answer_question(document, question):
    """RAG pipeline: retrieve relevant chunks, then generate an answer using them as context."""
    relevant_chunks = get_relevant_chunks(document, question)
    context = "\n\n".join([chunk.chunk_text for chunk in relevant_chunks])

    prompt = f"""Answer the following question based ONLY on the provided context from the student's notes.
If the answer isn't in the context, say so honestly.

Context:
{context}

Question: {question}
"""
    return generate_content(prompt)