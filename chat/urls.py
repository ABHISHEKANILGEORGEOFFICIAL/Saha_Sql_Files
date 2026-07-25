from django.urls import path
from .views import (
    ChatContextView,
    MessageListView,
    RoomMessageListView,
    unread_message_count,
)

urlpatterns = [
    # Chat context: current user + mutual contacts
    path('context/', ChatContextView.as_view(), name='chat-context'),

    # Message history by user_id (REST: send & receive)
    path('messages/', MessageListView.as_view(), name='chat-messages'),
    path('messages/<int:user_id>/', MessageListView.as_view(), name='chat-messages-user'),

    # Message history by room name — used by WebSocket frontend to preload
    path('messages/<str:room_name>/', RoomMessageListView.as_view(), name='chat-messages-room'),

    # Unread count for notification badge
    path('unread/', unread_message_count, name='chat-unread-count'),
]