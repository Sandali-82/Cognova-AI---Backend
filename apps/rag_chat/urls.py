from django.urls import path
from .views import ProcessDocumentForRAGView, ChatWithDocumentView

urlpatterns = [
    path('documents/<int:document_id>/process-for-chat/', ProcessDocumentForRAGView.as_view(), name='process-for-chat'),
    path('documents/<int:document_id>/chat/', ChatWithDocumentView.as_view(), name='chat-with-document'),
]