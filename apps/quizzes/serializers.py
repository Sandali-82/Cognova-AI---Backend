from rest_framework import serializers
from .models import Quiz, QuizQuestion, QuizAttempt


class QuizQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuizQuestion
        fields = ['id', 'question_text', 'option_a', 'option_b', 'option_c', 'option_d']
        # correct_option and explanation excluded here - not sent to frontend before attempt


class QuizSerializer(serializers.ModelSerializer):
    questions = QuizQuestionSerializer(many=True, read_only=True)

    class Meta:
        model = Quiz
        fields = ['id', 'document', 'title', 'created_at', 'questions']


class QuizAttemptSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuizAttempt
        fields = ['id', 'user', 'quiz', 'score', 'total_questions', 'attempted_at']
        read_only_fields = ['user', 'score', 'attempted_at']