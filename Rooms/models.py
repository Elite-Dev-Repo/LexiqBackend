from django.db import models
from django.contrib.auth.models import User
from QuestionsDirectory.models import QuestionDeck
# Create your models here.


class Room(models.Model):
    STATUS_CHOICES = (
        ('LOBBY', 'In Lobby'),
        ('IN_PROGRESS', 'Game In Progress'),
        ('FINISHED', 'Finished'),
    )
    code = models.CharField(max_length=10, unique=True)
    host = models.ForeignKey(User, on_delete=models.CASCADE, related_name='rooms')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='LOBBY')
    question_deck = models.ForeignKey(QuestionDeck, on_delete=models.SET_NULL, null=True, blank=True)
    time_limit = models.IntegerField(default=10)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.code


class RoomMember(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='members')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='room_members')
    score = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.username} in Room {self.room.code}"


