from django.db import models
from django.contrib.auth.models import User 

# Create your models here.

class GlobalChat(models.Model):
    name = models.CharField(max_length=100, default="Global Chat")
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Message(models.Model):
    chat = models.ForeignKey(GlobalChat, on_delete=models.CASCADE, related_name='messages', default=1)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user}: {self.message}"
