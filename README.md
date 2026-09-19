# Cognova AI - Backend

*Notes In. Knowledge Out.*

AI-powered study assistant backend built with Django, PostgreSQL, and Google Gemini API.

## Features

- Google OAuth authentication
- PDF document upload with text extraction
- AI-powered summarization
- AI-generated quizzes with scoring and feedback
- RAG-based chat with documents (pgvector semantic search)
- Score analytics dashboard with subject-wise performance tracking

## Tech Stack

- Backend Framework: Django + Django REST Framework
- Database: PostgreSQL with pgvector extension
- Authentication: Google OAuth 2.0 (django-allauth) + DRF Token Authentication
- AI: Google Gemini API (generation + embeddings)
- PDF Processing: pypdf

## Project Structure

- apps/documents - Document upload, PDF text extraction
- apps/summarization - AI summarization
- apps/quizzes - Quiz generation, submission, scoring
- apps/rag_chat - RAG-based chat (pgvector)
- apps/analytics - Score analytics and subject performance
- ai_core - Shared Gemini API client with retry/fallback logic
- core - Django project settings

## Setup

1. Clone the repository

2. Create a virtual environment and install dependencies

        python -m venv venv
        venv\Scripts\activate
        pip install -r requirements.txt

3. Set up PostgreSQL with the pgvector extension enabled

4. Create a .env file in the project root with the following variables

        DB_NAME=your_db_name
        DB_USER=your_db_user
        DB_PASSWORD=your_db_password
        DB_HOST=localhost
        DB_PORT=5432
        GOOGLE_CLIENT_ID=your_google_client_id
        GOOGLE_CLIENT_SECRET=your_google_client_secret
        GEMINI_API_KEY=your_gemini_api_key

5. Run migrations

        python manage.py migrate

6. Start the server

        python manage.py runserver