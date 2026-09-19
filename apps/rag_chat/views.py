from rest_framework import views, permissions, status
from rest_framework.response import Response
from apps.documents.models import Document
from .models import ChatMessage
from .serializers import ChatMessageSerializer
from .services import process_document_for_rag, answer_question


class ProcessDocumentForRAGView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, document_id):
        try:
            document = Document.objects.get(id=document_id, user=request.user)
        except Document.DoesNotExist:
            return Response({"error": "Document not found"}, status=status.HTTP_404_NOT_FOUND)

        if not document.extracted_text:
            return Response({"error": "No extracted text available for this document"}, status=status.HTTP_400_BAD_REQUEST)

        process_document_for_rag(document)

        return Response({"message": "Document processed for chat successfully"}, status=status.HTTP_200_OK)


class ChatWithDocumentView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, document_id):
        try:
            document = Document.objects.get(id=document_id, user=request.user)
        except Document.DoesNotExist:
            return Response({"error": "Document not found"}, status=status.HTTP_404_NOT_FOUND)

        question = request.data.get('question')
        if not question:
            return Response({"error": "Question is required"}, status=status.HTTP_400_BAD_REQUEST)

        answer = answer_question(document, question)

        chat_message = ChatMessage.objects.create(
            user=request.user,
            document=document,
            question=question,
            answer=answer
        )

        serializer = ChatMessageSerializer(chat_message)
        return Response(serializer.data, status=status.HTTP_200_OK)
