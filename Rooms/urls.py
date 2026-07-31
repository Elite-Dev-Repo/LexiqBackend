from django.urls import path
from .views import RoomListView, RoomDetailView, RoomCreateView, RegisterView, UserDetailView

urlpatterns =[
    path('create-room/', RoomCreateView.as_view(), name='room-create-view'),
    path('rooms/', RoomListView.as_view(), name='room-list'),
    path('rooms/<int:pk>/', RoomDetailView.as_view(), name='room-detail'),
    path('register/', RegisterView.as_view(), name='register'),
    path('user/', UserDetailView.as_view(), name='user-detail'),
]