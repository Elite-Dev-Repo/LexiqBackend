from rest_framework import serializers
from .models import QuestionDeck, Question, QuestionOption

class QuestionOptionSerializer(serializers.ModelSerializer):
    is_correct = serializers.SerializerMethodField()
    class Meta:
        model = QuestionOption
        fields = ['id', 'option_text', 'is_correct']

    def get_is_correct(self, obj):
        answer = obj.question.word
        return obj.option_text == answer


class QuestionSerializer(serializers.ModelSerializer):
    options = QuestionOptionSerializer(many=True, read_only=True)
    
    class Meta:
        model = Question
        fields = ['id', 'deck', 'word', 'definition', 'usage_example', 'difficulty', 'options']


class QuestionDeckSerializer(serializers.ModelSerializer):
    questions = QuestionSerializer(many=True, read_only=True)
    
    class Meta:
        model = QuestionDeck
        fields = ['id', 'name', 'description', 'questions']

class QuestionDeckListSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuestionDeck
        fields = ['id', 'name', 'description']