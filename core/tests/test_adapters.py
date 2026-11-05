from types import SimpleNamespace

from core.adapters import CustomAccountAdapter


def test_confirmation_url_points_to_the_configured_frontend(settings):
    settings.FRONTEND_URL = "https://app.example.com"
    confirmation = SimpleNamespace(key="abc123")

    url = CustomAccountAdapter().get_email_confirmation_url(
        request=None, emailconfirmation=confirmation
    )

    assert url == "https://app.example.com/verify-email/abc123"