from django.urls import path
from .views import GlobalChatView, MessageView

urlpatterns = [
    path('global-chat/', GlobalChatView.as_view(), name='global-chat'),
    path('messages/', MessageView.as_view(), name='messages'),
]