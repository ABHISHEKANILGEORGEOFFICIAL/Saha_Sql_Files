from django.shortcuts import render
      
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
# Create your views here.

from communityapp.models import CommunityPermissionRequest, Post
from studentapp.serializers import PostSerializer, TuitionSerializer

class StudentProfile(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not hasattr(request.user, "student"):
            return Response({"error": "Not a student"}, status=403)

        user = request.user
        student = user.student

        # 🔹 counts
        posts_count = Post.objects.filter(author=user).count()

        # if no follow system → keep 0
        followers_count = 0
        following_count = 0

        return Response({
            "username": user.username,
            "fullName": user.get_full_name() or user.username,
            "role": "Student",
            "avatarUrl": None,

            # 🔥 dynamic avatar
            "firstName": user.username[:1].upper(),

            # 🔥 counts
            "posts": posts_count,
            "followers": followers_count,
            "following": following_count,

            # 🔹 optional existing student data
            "gender": student.gender,
        })


        
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Q

class StudentTuitionFeed(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        student = request.user.student

        # Available tuitions
        available = Tuition.objects.filter(
            Q(school=student.school) |
            Q(college=student.college) |
            Q(course=student.course) |
            Q(department=student.department) |
            Q(subject__in=student.subjects.all())
        ).distinct()

        # My enrolled tuitions
        enrollments = Enrollment.objects.filter(student=student)
        my_tuitions = [e.tuition for e in enrollments]

        return Response({
            "my_tuitions": TuitionSerializer(my_tuitions, many=True).data,
            "available_tuitions": TuitionSerializer(available, many=True).data,
            "subject_filters": []  # optional for now
        })
    
from rest_framework import status
from django.shortcuts import get_object_or_404
from Guestapp.models import ClassTeacher

class RequestCommunity(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        student = request.user.student

        teacher_id = request.data.get('teacher')
        community_name = request.data.get('community_name')
        description = request.data.get('description')

        # ✅ Validate
        if not teacher_id or not community_name:
            return Response(
                {"error": "Teacher and community name required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        teacher = get_object_or_404(ClassTeacher, id=teacher_id)

        # ✅ Prevent duplicate requests
        if CommunityPermissionRequest.objects.filter(
            student=student,
            community_name=community_name,
            status="pending"
        ).exists():
            return Response(
                {"error": "Request already pending"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # ✅ Create request
        CommunityPermissionRequest.objects.create(
            student=student,
            teacher=teacher,
            community_name=community_name,
            description=description
        )

        return Response({"message": "Request sent"}, status=201)
    
from communityapp.models import Community, CommunityMembership

from rest_framework import status

class JoinCommunity(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, community_id):
        user = request.user
        community = get_object_or_404(Community, id=community_id)

        membership, created = CommunityMembership.objects.get_or_create(
            user=user,
            community=community,
            defaults={'role': 'member'}
        )

        if not created:
            return Response(
                {"message": "Already a member"},
                status=status.HTTP_200_OK
            )

        return Response(
            {"message": "Joined community"},
            status=status.HTTP_201_CREATED
        )
    
class CreatePost(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = PostSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save(author=request.user)
            return Response(serializer.data)

        return Response(serializer.errors, status=400)


class LikePost(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, post_id):
        post = get_object_or_404(Post, id=post_id)

        user = request.user

        if user in post.likes.all():
            post.likes.remove(user)
            return Response({"message": "Unliked"})
        else:
            post.likes.add(user)
            return Response({"message": "Liked"})


class StudentFeed(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        posts = Post.objects.all().order_by('-created_at')

        serializer = PostSerializer(posts, many=True)

        return Response(serializer.data)


from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404

from Teacherapp.models import Task, Submission,Enrollment, Tuition
from Guestapp.models import Student 


# 🔹 LIST TASKS FOR STUDENT
class StudentTaskList(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        student = request.user.student

        tuitions = student.enrollment_set.values_list('tuition_id', flat=True)

        tasks = Task.objects.filter(
            tuition_id__in=tuitions
        ).order_by('-created_at')

        data = []

        for task in tasks:
            submission = Submission.objects.filter(
                task=task,
                student=student
            ).first()

            data.append({
                "id": task.id,
                "title": task.title,
                "type": task.get_task_type_display(),  # ✅ correct
                "due_date": task.due_date,
                "submitted": submission is not None,
                "status": submission.status if submission else "pending",
            })

        return Response(data)

# 🔹 TASK DETAIL + EXISTING SUBMISSION
class StudentTaskDetail(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, id):
        student = request.user.student
        task = get_object_or_404(Task, id=id)

        submission = Submission.objects.filter(
            task=task,
            student=student
        ).first()

        return Response({
            "task": {
                "id": task.id,
                "title": task.title,
                "description": task.description,
                "type": task.get_task_type_display(),  # ✅ correct
                "due_date": task.due_date,
                "attachment": task.attachment.url if task.attachment else None,
                "attachment_name": task.attachment.name if task.attachment else None,
                "tuition_title": task.tuition.title,
            },
            "existing": {
                "content": submission.content,
                "marks": submission.marks,          # ✅ fixed
                "status": submission.status,
            } if submission else None
        })

# 🔹 SUBMIT / UPDATE TASK
class SubmitTask(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, id):
        student = request.user.student
        task = get_object_or_404(Task, id=id)

        content = request.data.get("content")
        file = request.FILES.get("attachment")

        submission, created = Submission.objects.get_or_create(
            task=task,
            student=student
        )

        submission.content = content

        if file:
            submission.attachment = file

        submission.status = "submitted"
        submission.save()

        return Response({"message": "Submitted successfully"})




