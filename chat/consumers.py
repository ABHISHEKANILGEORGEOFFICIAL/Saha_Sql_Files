import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q

from communityapp.models import Follow

from .models import Message


def get_room_name(user1_id, user2_id):
    return f"{min(user1_id, user2_id)}_{max(user1_id, user2_id)}"


@database_sync_to_async
def is_valid_chat(user, other_user_id):
    accepted_exists = Follow.objects.filter(
        Q(follower=user, following_id=other_user_id) |
        Q(follower_id=other_user_id, following=user),
        status='accepted',
    ).exists()

    if accepted_exists:
        return True

    return (
        Follow.objects.filter(follower=user, following_id=other_user_id).exists()
        and Follow.objects.filter(follower_id=other_user_id, following=user).exists()
    )


class ChatConsumer(AsyncWebsocketConsumer):
 
    async def connect(self):
        user = self.scope.get("user")
 
        if not user or user.is_anonymous:
            await self.close()
            return
 
        self.user = user
        self.room_name = self.scope["url_route"]["kwargs"].get("room_name")
 
        if not self.room_name or "_" not in self.room_name:
            await self.close()
            return
 
        try:
            user1_id, user2_id = map(int, self.room_name.split("_"))
        except ValueError:
            await self.close()
            return
 
        # Security: user must be one of the two parties in the room
        if self.user.id not in [user1_id, user2_id]:
            await self.close()
            return

        other_user_id = user2_id if self.user.id == user1_id else user1_id
        if not await is_valid_chat(self.user, other_user_id):
            await self.close()
            return
 
        self.room_group_name = f"chat_{self.room_name}"
 
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()
 
    async def disconnect(self, close_code):
        if hasattr(self, "room_group_name"):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
 
    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            action = data.get("action")
 
            # ── Mark messages as read ──
            if action == "mark_read":
                user1_id, user2_id = map(int, self.room_name.split("_"))
                other_user_id = user2_id if self.user.id == user1_id else user1_id
                await self.mark_messages_as_read(other_user_id)
                return
 
            # ── Send a message ──
            message = data.get("message", "").strip()
            if not message:
                return
 
            sender = self.user
            user1_id, user2_id = map(int, self.room_name.split("_"))
            receiver_id = user2_id if sender.id == user1_id else user1_id
 
            try:
                receiver_user = await database_sync_to_async(
                    User.objects.get
                )(id=receiver_id)
            except ObjectDoesNotExist:
                return
 
            # Save to DB
            msg = await database_sync_to_async(Message.objects.create)(
                sender=sender,
                receiver=receiver_user,
                content=message,
            )
            # Mark sender as having read their own message
            await database_sync_to_async(msg.readBy.add)(sender)
 
            # Broadcast to both participants
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "chat_message",
                    "message": message,
                    "sender": sender.get_full_name() or sender.username,
                    "sender_id": sender.id,
                    "timestamp": msg.timestamp.isoformat(),
                    "msg_id": msg.id,
                }
            )
 
        except Exception:
            pass  # Silent fail; add logging here if needed
 
    @database_sync_to_async
    def mark_messages_as_read(self, other_user_id):
        messages = Message.objects.filter(
            sender_id=other_user_id,
            receiver=self.user
        )
        for msg in messages:
            msg.readBy.add(self.user)
 
    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            "message":   event["message"],
            "sender":    event["sender"],
            "sender_id": event["sender_id"],
            "timestamp": event["timestamp"],
            "msg_id":    event["msg_id"],
        }))