from allauth.socialaccount.signals import social_account_added, social_account_updated
from django.dispatch import receiver
from rest_framework.authtoken.models import Token


@receiver(social_account_added)
@receiver(social_account_updated)
def create_token_for_social_user(sender, request, sociallogin, **kwargs):
    """Ensure a DRF token exists whenever a user logs in via Google."""
    Token.objects.get_or_create(user=sociallogin.user)