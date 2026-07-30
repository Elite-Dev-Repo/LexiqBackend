from django.shortcuts import render
from .serializers import GlobalChatSerializer, MessageSerializer
from .models import GlobalChat, Message
from rest_framework import generics
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, IsAdminUser
# Create your views here.

class GlobalChatView(generics.ListAPIView):
    queryset = GlobalChat.objects.all()
    serializer_class = GlobalChatSerializer
    permission_classes = [IsAuthenticated]

class MessageView(generics.ListAPIView):
    queryset = Message.objects.all()
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]
