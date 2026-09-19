from django.db.models import Avg, Count
from apps.quizzes.models import QuizAttempt


def get_score_trend(user):
    """Score percentage over time, ordered by attempt date."""
    attempts = QuizAttempt.objects.filter(user=user).order_by('attempted_at')

    return [
        {
            "quiz_id": attempt.quiz_id,
            "quiz_title": attempt.quiz.title,
            "score": attempt.score,
            "total_questions": attempt.total_questions,
            "percentage": round((attempt.score / attempt.total_questions) * 100, 1) if attempt.total_questions else 0,
            "attempted_at": attempt.attempted_at
        }
        for attempt in attempts
    ]


def get_overall_stats(user):
    """Summary stats: total attempts, average score percentage, best/worst quiz."""
    attempts = QuizAttempt.objects.filter(user=user)

    if not attempts.exists():
        return {
            "total_attempts": 0,
            "average_percentage": 0,
            "best_quiz": None,
            "weakest_quiz": None
        }

    stats = attempts.aggregate(
        total_attempts=Count('id'),
        avg_score=Avg('score'),
        avg_total=Avg('total_questions')
    )

    avg_percentage = round((stats['avg_score'] / stats['avg_total']) * 100, 1) if stats['avg_total'] else 0

    # Annotate each attempt with percentage to find best/worst
    scored = [
        {
            "quiz_title": a.quiz.title,
            "percentage": (a.score / a.total_questions) * 100 if a.total_questions else 0
        }
        for a in attempts
    ]
    best = max(scored, key=lambda x: x['percentage'])
    weakest = min(scored, key=lambda x: x['percentage'])

    return {
        "total_attempts": stats['total_attempts'],
        "average_percentage": avg_percentage,
        "best_quiz": best,
        "weakest_quiz": weakest
    }

# Grouping by subject to identify weak topics, useful for dashboard insights
def get_subject_performance(user):
    """Average score percentage grouped by subject, to identify weak topics."""
    attempts = QuizAttempt.objects.filter(user=user).select_related('quiz__document')

    subject_scores = {}
    for attempt in attempts:
        subject = attempt.quiz.document.subject or "Uncategorized"
        if subject not in subject_scores:
            subject_scores[subject] = {"total_score": 0, "total_questions": 0}
        subject_scores[subject]["total_score"] += attempt.score
        subject_scores[subject]["total_questions"] += attempt.total_questions

    result = [
        {
            "subject": subject,
            "average_percentage": round((data["total_score"] / data["total_questions"]) * 100, 1) if data["total_questions"] else 0
        }
        for subject, data in subject_scores.items()
    ]

    # weakest subjects first, so the dashboard highlights what to focus on
    result.sort(key=lambda x: x['average_percentage'])
    return result