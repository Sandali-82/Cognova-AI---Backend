from rest_framework import views, permissions
from rest_framework.response import Response
from .services import get_score_trend, get_overall_stats, get_subject_performance


class AnalyticsDashboardView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response({
            "overall_stats": get_overall_stats(request.user),
            "score_trend": get_score_trend(request.user),
            "subject_performance": get_subject_performance(request.user)
        })
