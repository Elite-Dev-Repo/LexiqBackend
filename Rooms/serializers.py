from rest_framework import serializers
from .models import Room, RoomMember
from django.contrib.auth.models import User
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
import secrets
import random

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['username'] = user.username
        return token

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password']
        extra_kwargs = {"password": {"write_only": True}}

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user

class RoomMemberSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = RoomMember
        fields = ['id', 'room', 'user', 'score', 'created_at']

class RoomListSerializer(serializers.ModelSerializer):
    host = UserSerializer(read_only=True)
    member_count = serializers.SerializerMethodField()

    class Meta:
        model = Room
        fields = ['id', 'code', 'host', 'time_limit', 'status', 'created_at', 'member_count']

    def get_member_count(self, obj):
        return obj.members.count()
       

class RoomSerializer(serializers.ModelSerializer):
    host = UserSerializer(read_only=True)
    code = serializers.CharField(read_only=True)
    members = RoomMemberSerializer(many=True, read_only=True)

    class Meta:
        model = Room
        fields = ['id', 'code', 'host', 'time_limit', 'status', 'question_deck', 'created_at', 'members']

    def _generate_code(self):
        letters = secrets.token_urlsafe(3).upper()[:3]
        num_list = []
        for _ in range(3):
            num = random.randint(0, 9)
            num_list.append(num)
        code = f"QUIZ-{letters}{''.join(map(str, num_list))}"
        if not Room.objects.filter(code=code).exists():
            return code
        return None

    def create(self, validated_data):
        code = self._generate_code()
        if not code:
            raise serializers.ValidationError("Could not generate a unique room code.")
        validated_data['code'] = code
        return super().create(validated_data)
































