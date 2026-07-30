from rest_framework import serializers
from .models import Message, GlobalChat

class MessageSerializer(serializers.ModelSerializer):
    user = serializers.CharField(source='user.username', read_only=True)
    class Meta:
        model = Message
        fields = ['user', 'message', 'timestamp']
        read_only_fields = ['user', 'timestamp']

        def create(self, obj):
            timestamp = obj.timestamp.isoformat()
            return self.save(timestamp=timestamp)

class GlobalChatSerializer(serializers.ModelSerializer):
    messages = MessageSerializer(many=True, read_only=True)
    class Meta:
        model = GlobalChat
        fields = ['id', 'name', 'messages']