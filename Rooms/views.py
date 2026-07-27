from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from django.contrib.auth.models import User
from .models import Room
from .serializers import RoomSerializer, RoomListSerializer, UserSerializer
from .permissions import IsAdminOrReadOnly


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [AllowAny]


class RoomCreateView(generics.CreateAPIView):
    queryset = Room.objects.all()
    serializer_class = RoomSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(host=self.request.user)


class RoomListView(generics.ListAPIView):
    queryset = Room.objects.all()
    serializer_class = RoomListSerializer
    permission_classes = [IsAuthenticated]

class RoomDetailView(generics.RetrieveAPIView):
    queryset = Room.objects.prefetch_related('members').all()
    serializer_class = RoomSerializer   
    permission_classes = [IsAuthenticated]
