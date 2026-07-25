from rest_framework import serializers
from Guestapp.models import Student

class StudentSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = Student
        fields = '__all__'


from Teacherapp.models import Tuition, Enrollment

class TuitionSerializer(serializers.ModelSerializer):
    is_enrolled = serializers.SerializerMethodField()

    class Meta:
        model = Tuition
        fields = '__all__'

    def get_is_enrolled(self, obj):
        user = self.context['request'].user

        if hasattr(user, 'student'):
            return Enrollment.objects.filter(
                student=user.student,
                tuition=obj
            ).exists()
        return False
    
from communityapp.models import Community

class CommunitySerializer(serializers.ModelSerializer):
    member_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Community
        fields = '__all__'


from communityapp.models import Post

class PostSerializer(serializers.ModelSerializer):
    likes_count = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = '__all__'

    def get_likes_count(self, obj):
        return obj.likes.count()