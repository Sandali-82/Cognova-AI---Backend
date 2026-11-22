# Cognova AI - Backend

[![Backend CI](https://github.com/Sandali-82/Cognova-AI---Backend/actions/workflows/backend-ci.yml/badge.svg)](https://github.com/Sandali-82/Cognova-AI---Backend/actions/workflows/backend-ci.yml)

*Notes In. Knowledge Out.*

AI-powered study assistant backend built with Django, PostgreSQL (pgvector), and the Google Gemini API.

**Live demo:** https://cognova-ai-frontend.onrender.com
**Frontend repository:** https://github.com/Sandali-82/cognova-ai-frontend

> The backend runs on a free Render instance, so the first request after a period of inactivity can take up to a minute while the service wakes up.

## Features

- Google OAuth and email/password authentication with email verification
- PDF document upload with text extraction
- AI-powered summarization
- AI-generated quizzes with scoring and feedback
- RAG-based chat with documents (pgvector semantic search)
- Score analytics dashboard with subject-wise performance tracking
- Gemini API client with retry, exponential backoff, and model fallback

## Tech Stack

- Backend Framework: Django + Django REST Framework
- Database: PostgreSQL with the pgvector extension (Supabase in production)
- Authentication: django-allauth (Google OAuth 2.0), dj-rest-auth, DRF Token Authentication
- AI: Google Gemini API (generation + embeddings)
- PDF Processing: pypdf
- Email: Brevo (via django-anymail)
- Testing: pytest, pytest-django (Gemini API mocked)
- CI/CD: GitHub Actions, deployed on Render

## Project Structure

- apps/documents - Document upload, PDF text extraction
- apps/summarization - AI summarization
- apps/quizzes - Quiz generation, submission, scoring
- apps/rag_chat - RAG-based chat (pgvector)
- apps/analytics - Score analytics and subject performance
- ai_core - Shared Gemini API client with retry/fallback logic
- core - Django project settings and URL configuration

## Local Setup

1. Clone the repository

2. Create a virtual environment and install dependencies

        python -m venv venv
        venv\Scripts\activate
        pip install -r requirements.txt -r requirements-dev.txt

3. Set up PostgreSQL with the pgvector extension available

4. Create a .env file in the project root with the following variables

        DEBUG=True
        SECRET_KEY=your_secret_key
        DB_NAME=your_db_name
        DB_USER=your_db_user
        DB_PASSWORD=your_db_password
        DB_HOST=localhost
        DB_PORT=5432
        GOOGLE_CLIENT_ID=your_google_client_id
        GOOGLE_CLIENT_SECRET=your_google_client_secret
        GEMINI_API_KEY=your_gemini_api_key
        BREVO_API_KEY=your_brevo_api_key
        DEFAULT_FROM_EMAIL=your_sender_email

5. Run migrations

        python manage.py migrate

6. Start the server

        python manage.py runserver

## Running Tests

    pytest

The Gemini API is mocked in all tests, so no API key is needed to run them.

## Deployment

- The backend is deployed on Render and uses a Supabase PostgreSQL database.
- In production, set `DATABASE_URL` (instead of the `DB_*` variables), `SECRET_KEY`, `FRONTEND_URL`, and the Google, Gemini, and Brevo variables.
- `GET /api/health/` is a health check endpoint that runs a simple database query.
- A GitHub Actions workflow runs the test suite on every push, and a scheduled workflow pings the health endpoint so the free-tier database does not pause from inactivity.