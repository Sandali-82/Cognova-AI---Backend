from dj_rest_auth.registration.views import RegisterView
from dj_rest_auth.views import LoginView
from rest_framework.authentication import SessionAuthentication
from django.db import connection
from django.http import JsonResponse


class CsrfExemptSessionAuthentication(SessionAuthentication):
    def enforce_csrf(self, request):
        return


class NoCsrfRegisterView(RegisterView):
    authentication_classes = [CsrfExemptSessionAuthentication]


class NoCsrfLoginView(LoginView):
    authentication_classes = [CsrfExemptSessionAuthentication]

def health(request):
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")
    return JsonResponse({"status": "ok"})