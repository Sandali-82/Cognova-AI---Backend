from dj_rest_auth.registration.views import RegisterView
from dj_rest_auth.views import LoginView
from rest_framework.authentication import SessionAuthentication


class CsrfExemptSessionAuthentication(SessionAuthentication):
    def enforce_csrf(self, request):
        return


class NoCsrfRegisterView(RegisterView):
    authentication_classes = [CsrfExemptSessionAuthentication]


class NoCsrfLoginView(LoginView):
    authentication_classes = [CsrfExemptSessionAuthentication]