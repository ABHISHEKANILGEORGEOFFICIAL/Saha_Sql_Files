from django.contrib.auth.models import User
from django.db import models
from django.db.models import Q

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from communityapp.models import Follow
from communityapp.serializers import SimpleUserSerializer

from .models import Message
from .serializers import MessageSerializer, UnreadCountSerializer


def get_accepted_contact_ids(user):
    following_ids = Follow.objects.filter(
        follower=user,
        status='accepted',
    ).values_list('following_id', flat=True)

    follower_ids = Follow.objects.filter(
        following=user,
        status='accepted',
    ).values_list('follower_id', flat=True)

    return set(following_ids).union(follower_ids)


def get_chat_contact_ids(user):
    accepted_ids = get_accepted_contact_ids(user)
    outgoing_ids = set(
        Follow.objects.filter(follower=user).values_list('following_id', flat=True)
    )
    incoming_ids = set(
        Follow.objects.filter(following=user).values_list('follower_id', flat=True)
    )

    return accepted_ids.union(outgoing_ids.intersection(incoming_ids))


def has_chat_access(user, other_user_id):
    try:
        target_id = int(other_user_id)
    except (TypeError, ValueError):
        return False
    return target_id in get_chat_contact_ids(user)


# Endpoint to get unread message count for notifications
@api_view(['GET'])
def unread_message_count(request):
    user = request.user
    unread_count = Message.objects.filter(receiver=user).exclude(readBy=user).count()
    data = {'user_id': user.id, 'unread_count': unread_count}
    serializer = UnreadCountSerializer(data)
    return Response(serializer.data)


class ChatContextView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        contact_ids = get_chat_contact_ids(user)

        contacts = User.objects.filter(
            id__in=contact_ids
        ).exclude(id=user.id)

        data = {
            "current_user": SimpleUserSerializer(user).data,
            "contacts": SimpleUserSerializer(contacts, many=True).data,
        }

        return Response(data)

class MessageListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, user_id):
        # Get all messages between the current user and the specified user
        user = request.user
        if not has_chat_access(user, user_id):
            return Response({'error': 'Chat access denied.'}, status=status.HTTP_403_FORBIDDEN)

        messages = Message.objects.filter(
            (models.Q(sender=user) & models.Q(receiver_id=user_id)) |
            (models.Q(sender_id=user_id) & models.Q(receiver=user))
        ).order_by('timestamp')
        serializer = MessageSerializer(messages, many=True)
        return Response(serializer.data)

class RoomMessageListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, room_name):
        try:
            user1, user2 = map(int, room_name.split("_"))
        except (AttributeError, TypeError, ValueError):
            return Response({'error': 'Invalid room name.'}, status=status.HTTP_400_BAD_REQUEST)

        if request.user.id not in {user1, user2}:
            return Response({'error': 'Chat access denied.'}, status=status.HTTP_403_FORBIDDEN)

        other_user_id = user2 if request.user.id == user1 else user1
        if not has_chat_access(request.user, other_user_id):
            return Response({'error': 'Chat access denied.'}, status=status.HTTP_403_FORBIDDEN)

        messages = Message.objects.filter(
            sender_id__in=[user1, user2],
            receiver_id__in=[user1, user2]
        ).order_by('timestamp')

        serializer = MessageSerializer(messages, many=True)
        return Response(serializer.data)


    def post(self, request, user_id):
        # Send a message to the specified user
        user = request.user
        if not has_chat_access(user, user_id):
            return Response({'error': 'Chat access denied.'}, status=status.HTTP_403_FORBIDDEN)

        receiver = User.objects.get(id=user_id)
        content = request.data.get('content')
        if not content:
            return Response({'error': 'Content is required.'}, status=status.HTTP_400_BAD_REQUEST)
        message = Message.objects.create(sender=user, receiver=receiver, content=content)
        serializer = MessageSerializer(message)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

@api_view(['GET'])
def get_messages(request, room_name):
    user_ids = room_name.split("_")
    user1 = int(user_ids[0])
    user2 = int(user_ids[1])

    messages = Message.objects.filter(
        sender_id__in=[user1, user2],
        receiver_id__in=[user1, user2]
    ).order_by('timestamp')

    serializer = MessageSerializer(messages, many=True)
    return Response(serializer.data)