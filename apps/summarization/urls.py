from django.urls import path
from .views import GenerateSummaryView

urlpatterns = [
    path('documents/<int:document_id>/summarize/', GenerateSummaryView.as_view(), name='generate-summary'),
]