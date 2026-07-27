from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class QuestionDeck(models.Model):

    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    

    class Meta:
        verbose_name = "Question Deck"
        verbose_name_plural = "Question Decks"
        ordering = ['-created_at']
        
    def __str__(self):
        return self.name
    


class Question(models.Model):
    DIFFICULTY_CHOICES = (
        ('easy', 'Easy'),
        ('medium', 'Medium'),
        ('hard', 'Hard'),
    )

    deck = models.ForeignKey(QuestionDeck, on_delete=models.CASCADE, related_name='questions')
    word = models.CharField(max_length=100)
    definition = models.CharField(max_length=200)
    usage_example = models.CharField(max_length=200)
    difficulty = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    

    class Meta:
        verbose_name = "Question"
        verbose_name_plural = "Questions"
        ordering = ['-created_at']
        
    def __str__(self):
        return self.word


class QuestionOption(models.Model):
    question = models.ForeignKey(
        Question, 
        on_delete=models.CASCADE, 
        related_name="options"
    )
    option_text = models.CharField(max_length=255)
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.option_text} -> {'Correct' if self.is_correct else 'Incorrect'}"