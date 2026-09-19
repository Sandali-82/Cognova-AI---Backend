from django.urls import path
from .views import GenerateQuizView, SubmitQuizView

urlpatterns = [
    path('documents/<int:document_id>/generate-quiz/', GenerateQuizView.as_view(), name='generate-quiz'),
    path('quizzes/<int:quiz_id>/submit/', SubmitQuizView.as_view(), name='submit-quiz'),
]