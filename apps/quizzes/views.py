from rest_framework import views, permissions, status
from rest_framework.response import Response
from apps.documents.models import Document
from .models import Quiz, QuizQuestion, QuizAttempt
from .serializers import QuizSerializer, QuizAttemptSerializer
from .services import generate_quiz_questions


class GenerateQuizView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, document_id):
        try:
            document = Document.objects.get(id=document_id, user=request.user)
        except Document.DoesNotExist:
            return Response({"error": "Document not found"}, status=status.HTTP_404_NOT_FOUND)

        if not document.extracted_text:
            return Response({"error": "No extracted text available for this document"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            questions_data = generate_quiz_questions(document.extracted_text)
        except Exception as e:
            return Response({"error": f"Quiz generation failed: {str(e)}"}, status=status.HTTP_502_BAD_GATEWAY)

        quiz = Quiz.objects.create(document=document, title=f"Quiz - {document.title}")

        for q in questions_data:
            QuizQuestion.objects.create(
                quiz=quiz,
                question_text=q['question_text'],
                option_a=q['option_a'],
                option_b=q['option_b'],
                option_c=q['option_c'],
                option_d=q['option_d'],
                correct_option=q['correct_option'],
                explanation=q.get('explanation', '')
            )

        serializer = QuizSerializer(quiz)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class SubmitQuizView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, quiz_id):
        try:
            quiz = Quiz.objects.get(id=quiz_id)
        except Quiz.DoesNotExist:
            return Response({"error": "Quiz not found"}, status=status.HTTP_404_NOT_FOUND)

        answers = request.data.get('answers')
        if not answers or not isinstance(answers, dict):
            return Response({"error": "Answers must be provided as an object mapping question IDs to selected options"}, status=status.HTTP_400_BAD_REQUEST)

        questions = quiz.questions.all()
        if not questions.exists():
            return Response({"error": "This quiz has no questions"}, status=status.HTTP_400_BAD_REQUEST)

        score = 0
        feedback = []

        for question in questions:
            selected = answers.get(str(question.id))
            is_correct = selected == question.correct_option
            if is_correct:
                score += 1

            feedback.append({
                "question_id": question.id,
                "question_text": question.question_text,
                "selected_option": selected,
                "correct_option": question.correct_option,
                "is_correct": is_correct,
                "explanation": question.explanation
            })

        attempt = QuizAttempt.objects.create(
            user=request.user,
            quiz=quiz,
            score=score,
            total_questions=questions.count()
        )

        return Response({
            "attempt_id": attempt.id,
            "score": score,
            "total_questions": questions.count(),
            "feedback": feedback
        }, status=status.HTTP_200_OK)