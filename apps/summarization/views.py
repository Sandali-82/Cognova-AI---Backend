from rest_framework import views, permissions, status
from rest_framework.response import Response
from apps.documents.models import Document
from .models import Summary
from .serializers import SummarySerializer
from .services import generate_summary

class GenerateSummaryView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, document_id):
        try:
            document = Document.objects.get(id=document_id, user=request.user)
        except Document.DoesNotExist:
            return Response({"error": "Document not found"}, status=status.HTTP_404_NOT_FOUND)

        if not document.extracted_text:
            return Response({"error": "No extracted text available for this document"}, status=status.HTTP_400_BAD_REQUEST)

        summary_content = generate_summary(document.extracted_text)

        summary, created = Summary.objects.update_or_create(
            document=document,
            defaults={"content": summary_content}
        )

        serializer = SummarySerializer(summary)
        return Response(serializer.data, status=status.HTTP_200_OK)
