from rest_framework import serializers
from .models import Message, GlobalChat

class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ['user', 'message', 'timestamp']

class GlobalChatSerializer(serializers.ModelSerializer):
    messages = MessageSerializer(many=True, read_only=True)
    class Meta:
        model = GlobalChat
        fields = ['id', 'name', 'timestamp', 'messages']