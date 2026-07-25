from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Message


class UserFullNameField(serializers.RelatedField):
    def to_representation(self, value):
        full_name = value.get_full_name()
        return full_name if full_name else value.username

class MessageSerializer(serializers.ModelSerializer):
    sender = serializers.SerializerMethodField()
    receiver = serializers.SerializerMethodField()
    sender_id = serializers.IntegerField(source='sender.id', read_only=True)
    receiver_id = serializers.IntegerField(source='receiver.id', read_only=True)
 
    class Meta:
        model = Message
        fields = ['id', 'sender', 'sender_id', 'receiver', 'receiver_id', 'content', 'timestamp']
 
    def get_sender(self, obj):
        full_name = obj.sender.get_full_name()
        return full_name if full_name else obj.sender.username
 
    def get_receiver(self, obj):
        full_name = obj.receiver.get_full_name()
        return full_name if full_name else obj.receiver.username
 
 
class UnreadCountSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()
    unread_count = serializers.IntegerField()
