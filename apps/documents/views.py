from rest_framework import viewsets, permissions, views
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.authentication import SessionAuthentication

from .models import Document
from .serializers import DocumentSerializer
from .services import extract_text_from_pdf

class DocumentViewSet(viewsets.ModelViewSet):
    serializer_class = DocumentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Document.objects.filter(user=self.request.user).order_by('-uploaded_at')

    def perform_create(self, serializer):
        document = serializer.save(user=self.request.user)
        extracted = extract_text_from_pdf(document.file.path)
        document.extracted_text = extracted
        document.save()


class CsrfExemptSessionAuthentication(SessionAuthentication):
    def enforce_csrf(self, request):
        return  # Skip CSRF check for this authentication class


class CurrentUserTokenView(views.APIView):
    authentication_classes = [CsrfExemptSessionAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        token, created = Token.objects.get_or_create(user=request.user)
        return Response({
            "token": token.key,
            "username": request.user.username
        })