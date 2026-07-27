from django.urls import path
from .views import QuestionDeckListView, QuestionDeckDetailView, QuestionListCreateView, QuestionDetailView, QuestionOptionListView, QuestionOptionDetailView, ListQuestionDeckView

urlpatterns = [
    path('decks-list/', ListQuestionDeckView.as_view(), name='list-question-deck'),
    path('decks/', QuestionDeckListView.as_view(), name='question-deck-list'),
    path('decks/<int:pk>/', QuestionDeckDetailView.as_view(), name='question-deck-detail'),
    path('questions/', QuestionListCreateView.as_view(), name='question-list'),
    path('questions/<int:pk>/', QuestionDetailView.as_view(), name='question-detail'),
    path('options/', QuestionOptionListView.as_view(), name='question-option-list'),
    path('options/<int:pk>/', QuestionOptionDetailView.as_view(), name='question-option-detail'),
]