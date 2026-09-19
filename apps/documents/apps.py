from django.apps import AppConfig

class DocumentsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.documents'

    def ready(self):
        from django.contrib.auth.signals import user_logged_in
        from rest_framework.authtoken.models import Token

        def create_token(sender, request, user, **kwargs):
            Token.objects.get_or_create(user=user)

        user_logged_in.connect(create_token)
