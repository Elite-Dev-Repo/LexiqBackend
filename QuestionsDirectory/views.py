from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .permissions import IsAdminOrReadOnly
from .models import QuestionDeck, Question, QuestionOption
from .serializers import QuestionDeckSerializer, QuestionSerializer, QuestionOptionSerializer, QuestionDeckListSerializer

class QuestionDeckListView(generics.ListAPIView):
    queryset = QuestionDeck.objects.prefetch_related('questions').all()
    serializer_class = QuestionDeckSerializer
    permission_classes = [IsAdminOrReadOnly]

class ListQuestionDeckView(generics.ListAPIView):
    queryset = QuestionDeck.objects.all()
    serializer_class = QuestionDeckListSerializer
    permission_classes = [IsAdminOrReadOnly]

class QuestionDeckDetailView(generics.RetrieveAPIView):
    queryset = QuestionDeck.objects.prefetch_related('questions').all()
    serializer_class = QuestionDeckSerializer
    permission_classes = [IsAdminOrReadOnly]

class QuestionListCreateView(generics.ListCreateAPIView):
    queryset = Question.objects.prefetch_related('options').all()
    serializer_class = QuestionSerializer
    permission_classes = [IsAdminOrReadOnly]

class QuestionDetailView(generics.RetrieveAPIView):
    queryset = Question.objects.prefetch_related('options').all()
    serializer_class = QuestionSerializer
    permission_classes = [IsAdminOrReadOnly]

class QuestionOptionListView(generics.ListAPIView):
    queryset = QuestionOption.objects.all()
    serializer_class = QuestionOptionSerializer
    permission_classes = [IsAdminOrReadOnly]

class QuestionOptionDetailView(generics.RetrieveAPIView):
    queryset = QuestionOption.objects.all()
    serializer_class = QuestionOptionSerializer
    permission_classes = [IsAdminOrReadOnly]
