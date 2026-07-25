from django.contrib.auth import logout

# Logout API for teachers (and any authenticated user)
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

class TeacherLogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        logout(request)
        return Response({'detail': 'Successfully logged out.'})
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.shortcuts import get_object_or_404

from django.contrib.auth.models import User
from Guestapp.models import ClassTeacher, Student, UserProfile

# ✅ Academic models — live here
from .models import CoursePayment, StudyRequest, Tuition, Task
from .serializers import StudyRequestSerializer, TuitionSerializer, TuitionDetailSerializer, TaskSerializer

# ✅ Social models — single source of truth in communityapp
from communityapp.models import Post, Reply, Report
from communityapp.serializers import PostSerializer, ReplySerializer


def build_chat_person_payload(role, profile_obj):
    user = profile_obj.user
    name = getattr(profile_obj, 'name', '') or user.get_full_name() or user.username or user.email
    short_name = ''.join(part[:1] for part in name.split()[:2]).upper() or name[:2].upper() or role[:2].upper()

    payload = {
        'id': user.id,
        'user_id': user.id,
        'role': role,
        'name': name,
        'short_name': short_name,
        'email': user.email,
        'title': '',
        'school_id': getattr(profile_obj, 'school_id', None),
        'college_id': getattr(profile_obj, 'college_id', None),
        'department_id': getattr(profile_obj, 'department_id', None),
    }

    if role == 'teacher':
        payload['title'] = 'Teacher'
    else:
        class_label = getattr(getattr(profile_obj, 'class_name', None), 'name', None)
        course_label = getattr(getattr(profile_obj, 'course', None), 'name', None)
        payload['title'] = class_label or course_label or 'Student'
        payload['class_name_id'] = getattr(profile_obj, 'class_name_id', None)
        payload['course_id'] = getattr(profile_obj, 'course_id', None)

    return payload


class ChatContextView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            user_profile = UserProfile.objects.get(user=request.user)
        except UserProfile.DoesNotExist:
            return Response({'error': 'User role not assigned'}, status=404)

        role = user_profile.role

        if role == 'teacher':
            try:
                teacher = ClassTeacher.objects.select_related(
                    'user', 'school', 'college', 'department'
                ).get(user=request.user)
            except ClassTeacher.DoesNotExist:
                return Response({'error': 'Teacher profile not found'}, status=404)

            students = Student.objects.select_related(
                'user', 'class_name', 'school', 'college', 'course', 'department'
            ).filter(
                enrollment__tuition__teacher=teacher
            ).distinct()

            contacts = [build_chat_person_payload('student', student) for student in students]
            current_user = build_chat_person_payload('teacher', teacher)

        elif role == 'student':
            try:
                student = Student.objects.select_related(
                    'user', 'class_name', 'school', 'college', 'course', 'department'
                ).get(user=request.user)
            except Student.DoesNotExist:
                return Response({'error': 'Student profile not found'}, status=404)

            teachers = ClassTeacher.objects.select_related(
                'user', 'school', 'college', 'department'
            ).filter(
                tuitions__enrollments__student=student
            ).distinct()

            contacts = [build_chat_person_payload('teacher', teacher) for teacher in teachers]
            current_user = build_chat_person_payload('student', student)

        else:
            return Response({'current_user': None, 'contacts': []})

        return Response({
            'current_user': current_user,
            'contacts': contacts,
        })


def get_teacher_for_user(user):
    return ClassTeacher.objects.select_related('user').filter(user=user).first()


def get_student_for_user(user):
    return Student.objects.select_related('user').filter(user=user).first()


class StudyRequestIncomingList(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        teacher = get_teacher_for_user(request.user)
        if not teacher:
            return Response({'error': 'Only teachers can view incoming study requests.'}, status=403)

        requests = StudyRequest.objects.select_related(
            'student__user', 'teacher__user', 'responded_by'
        ).filter(teacher=teacher)
        return Response(StudyRequestSerializer(requests, many=True).data)


class StudyRequestOutgoingList(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        student = get_student_for_user(request.user)
        if not student:
            return Response({'error': 'Only students can view outgoing study requests.'}, status=403)

        requests = StudyRequest.objects.select_related(
            'student__user', 'teacher__user', 'responded_by'
        ).filter(student=student)
        return Response(StudyRequestSerializer(requests, many=True).data)


class StudyRequestListCreate(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        teacher = get_teacher_for_user(request.user)
        if teacher:
            requests = StudyRequest.objects.select_related(
                'student__user', 'teacher__user', 'responded_by'
            ).filter(teacher=teacher)
            return Response(StudyRequestSerializer(requests, many=True).data)

        student = get_student_for_user(request.user)
        if student:
            requests = StudyRequest.objects.select_related(
                'student__user', 'teacher__user', 'responded_by'
            ).filter(student=student)
            return Response(StudyRequestSerializer(requests, many=True).data)

        return Response({'error': 'User must be a student or teacher profile.'}, status=403)

    def post(self, request):
        student = get_student_for_user(request.user)
        if not student:
            return Response({'error': 'Only students can create study requests.'}, status=403)

        teacher_user_id = request.data.get('teacher_user_id')
        teacher_profile_id = request.data.get('teacher')
        message = (request.data.get('message') or '').strip()
        source_app = (request.data.get('source_app') or 'mobile').strip() or 'mobile'

        teacher = None
        if teacher_user_id:
            teacher = ClassTeacher.objects.select_related('user').filter(user_id=teacher_user_id).first()
        if not teacher and teacher_profile_id:
            teacher = ClassTeacher.objects.select_related('user').filter(id=teacher_profile_id).first()

        if not teacher:
            return Response({'error': 'Target teacher not found.'}, status=404)

        existing_pending = StudyRequest.objects.filter(
            student=student,
            teacher=teacher,
            status=StudyRequest.STATUS_PENDING,
        ).first()
        if existing_pending:
            return Response(StudyRequestSerializer(existing_pending).data)

        study_request = StudyRequest.objects.create(
            student=student,
            teacher=teacher,
            message=message,
            source_app=source_app,
        )
        return Response(StudyRequestSerializer(study_request).data, status=201)


class StudyRequestDecision(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, request_id):
        teacher = get_teacher_for_user(request.user)
        if not teacher:
            return Response({'error': 'Only teachers can respond to study requests.'}, status=403)

        status_value = (request.data.get('status') or '').strip().lower()
        if status_value not in {StudyRequest.STATUS_ACCEPTED, StudyRequest.STATUS_REJECTED}:
            return Response({'error': 'status must be accepted or rejected'}, status=400)

        study_request = StudyRequest.objects.select_related(
            'student__user', 'teacher__user', 'responded_by'
        ).filter(id=request_id, teacher=teacher).first()
        if not study_request:
            return Response({'error': 'Study request not found.'}, status=404)

        study_request.status = status_value
        study_request.responded_by = request.user
        study_request.responded_at = timezone.now()
        study_request.save(update_fields=['status', 'responded_by', 'responded_at'])

        return Response(StudyRequestSerializer(study_request).data)


# ── TUITION ──────────────────────────────────────────────────────────────────

class TuitionListCreate(APIView):
    def get(self, request):
        teacher_id = request.query_params.get('teacher')
        tuitions = Tuition.objects.filter(teacher_id=teacher_id) if teacher_id else Tuition.objects.all()
        return Response(TuitionSerializer(tuitions, many=True).data)

    def post(self, request):
        # Resolve ClassTeacher from authenticated user
        try:
            teacher = ClassTeacher.objects.get(user=request.user)
        except ClassTeacher.DoesNotExist:
            return Response(
                {'error': 'No teacher profile found for this user.'},
                status=400
            )
        except Exception:
            # Fallback: accept teacher_id from body (useful when auth is not enforced)
            teacher_id = request.data.get('teacher')
            if not teacher_id:
                return Response(
                    {'error': 'teacher id is required when not authenticated.'},
                    status=400
                )
            try:
                teacher = ClassTeacher.objects.get(id=teacher_id)
            except ClassTeacher.DoesNotExist:
                return Response({'error': 'Teacher not found.'}, status=400)

        payload = request.data.copy()
        subject_id = payload.get('subject')
        if subject_id:
            subject = get_object_or_404(Tuition._meta.get_field('subject').remote_field.model, pk=subject_id)
            if subject.type == 'school' and not teacher.school_id:
                return Response(
                    {'error': 'Your teacher profile does not have a school assigned. Choose a college subject or contact admin.'},
                    status=400,
                )
            if subject.type == 'college' and not teacher.college_id:
                return Response(
                    {'error': 'Your teacher profile does not have a college assigned. Choose a school subject or contact admin.'},
                    status=400,
                )

        if teacher.school_id and not payload.get('school'):
            payload['school'] = teacher.school_id
        if teacher.college_id and not payload.get('college'):
            payload['college'] = teacher.college_id

        serializer = TuitionSerializer(data=payload)
        if serializer.is_valid():
            serializer.save(teacher=teacher)
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)


class TuitionDetail(APIView):
    def get_object(self, id):
        return Tuition.objects.get(id=id)

    def get(self, request, id):
        return Response(TuitionDetailSerializer(self.get_object(id)).data)

    def put(self, request, id):
        serializer = TuitionSerializer(self.get_object(id), data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

    def delete(self, request, id):
        self.get_object(id).delete()
        return Response({"message": "Deleted"})


# ── TASK (per-tuition, per-type) ──────────────────────────────────────────────

VALID_TASK_TYPES = ('homework', 'assignment', 'seminar', 'testpaper')


class TuitionTaskList(APIView):
    """
    GET  api/tuition/<tuition_id>/tasks/              → all tasks for the tuition
    POST api/tuition/<tuition_id>/tasks/              → create a task for the tuition
    """
    def get(self, request, tuition_id):
        tasks = Task.objects.filter(tuition_id=tuition_id)
        return Response(TaskSerializer(tasks, many=True).data)

    def post(self, request, tuition_id):
        data = request.data.copy()
        data['tuition'] = tuition_id
        serializer = TaskSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)


class TuitionTaskByType(APIView):
    """
    GET  api/tuition/<tuition_id>/tasks/<task_type>/  → tasks filtered by type
         task_type: homework | assignment | seminar | testpaper
    """
    def get(self, request, tuition_id, task_type):
        if task_type not in VALID_TASK_TYPES:
            return Response(
                {'error': f'Invalid task type. Choose from: {", ".join(VALID_TASK_TYPES)}'},
                status=400
            )
        tasks = Task.objects.filter(tuition_id=tuition_id, task_type=task_type)
        return Response(TaskSerializer(tasks, many=True).data)


class TaskDetail(APIView):
    """
    GET    api/task/<id>/   → retrieve a single task
    PUT    api/task/<id>/   → update
    DELETE api/task/<id>/   → delete
    """
    def get_object(self, id):
        return Task.objects.get(id=id)

    def get(self, request, id):
        return Response(TaskSerializer(self.get_object(id)).data)

    def put(self, request, id):
        serializer = TaskSerializer(self.get_object(id), data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

    def delete(self, request, id):
        self.get_object(id).delete()
        return Response({"message": "Task deleted"})


# ── POSTS (Teacher Wall / Feed) ───────────────────────────────────────────────
# Posts with community=None are standalone teacher-wall posts.
# Posts with community set belong to a community feed.
# Both cases use communityapp.models.Post — one unified model.

class PostList(APIView):
    """
    GET  api/teacher/posts/
    Returns all standalone (non-community) posts newest-first.
    """
    def get(self, request):
        posts = Post.objects.filter(community__isnull=True, is_removed=False).order_by('-created_at')  # ← add is_removed=False
        return Response(PostSerializer(posts, many=True, context={'request': request}).data)


class CreatePost(APIView):
    """
    POST api/teacher/posts/create/
    Creates a standalone teacher-wall post (community=None).
    """
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def post(self, request):
        data = request.data.copy()

        # Resolve author
        if request.user.is_authenticated:
            author = request.user
        else:
            author_id = data.get('author_id') or data.get('author')
            if author_id:
                try:
                    author = User.objects.get(id=author_id)
                except User.DoesNotExist:
                    return Response({'error': 'Author not found'}, status=400)
            else:
                author = User.objects.filter(is_superuser=True).first() or User.objects.first()
                if not author:
                    return Response({'error': 'No users exist. Create a user first.'}, status=400)

        post = Post(
            author=author,
            title=data.get('title', ''),
            content=data.get('content', ''),
            post_type=data.get('post_type', 'post'),
            community=None,         # ← standalone: not tied to any community
        )

        image = request.FILES.get('image')
        if image:
            post.image = image

        post.save()
        return Response(PostSerializer(post, context={'request': request}).data, status=201)


class PostDetail(APIView):
    """
    GET api/teacher/posts/<id>/
    Returns a single post together with its replies.
    """
    def get(self, request, id):
        post = Post.objects.get(id=id)
        return Response({
            "post":    PostSerializer(post, context={'request': request}).data,
            "replies": ReplySerializer(post.replies.all(), many=True).data,
        })


class AddReply(APIView):
    """
    POST api/teacher/posts/<id>/reply/
    """
    def post(self, request, id):
        data = {
            "post":    id,
            "author":  request.user.id if request.user.is_authenticated else None,
            "content": request.data.get('content'),
        }
        serializer = ReplySerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)


class ToggleLike(APIView):
    """
    POST api/teacher/posts/<id>/like/
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, id):
        post = Post.objects.get(id=id)
        from django.db import IntegrityError

        through_model = Post.likes.through
        removed, _ = through_model.objects.filter(
            post_id=post.id,
            user_id=request.user.id,
        ).delete()

        if removed:
            liked = False
        else:
            try:
                through_model.objects.create(post_id=post.id, user_id=request.user.id)
            except IntegrityError:
                # Concurrent like request created it first.
                pass
            liked = True

        like_count = through_model.objects.filter(post_id=post.id).count()
        return Response({
            "liked": liked,
            "liked_by_me": liked,
            "likes": like_count,
            "like_count": like_count,
            "post_id": post.id,
        })


from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import uuid

from .models import (
    TeacherCourse,
    CourseSection,
    CourseVideo,
    CourseNote,
    CourseAssignment,
    CourseAssignmentSubmission,
    CourseEnrollment,
    CourseCertificate,
    CourseReview,
    CourseReviewReply,
    CourseComment,
    CoursePayment,
    StudentCourseCollection,
    StudentCourseCollectionItem,
)

from .serializers import (
    TeacherCourseSerializer,
    FullCourseSerializer,
    CourseSectionSerializer,
    CourseVideoSerializer,
    CourseNoteSerializer,
    CourseAssignmentSerializer,
    CourseAssignmentSubmissionSerializer,
    CourseEnrollmentSerializer,
    CourseCertificateSerializer,
    CourseReviewSerializer,
    CourseReviewReplySerializer,
    CourseCommentSerializer,
    CoursePaymentSerializer,
    StudentCourseCollectionSerializer,
    StudentCourseCollectionItemSerializer,
)

# ─────────────────────────────────────────────
# 🎓 COURSE API
# ─────────────────────────────────────────────

class TeacherCourseAPI(APIView):

    def get_teacher(self, request):
        try:
            return ClassTeacher.objects.get(user=request.user)
        except ClassTeacher.DoesNotExist:
            return None

    def get(self, request, pk=None):
        # ✅ TEACHER: show only own courses
        if hasattr(request.user, "classteacher"):
            teacher = request.user.classteacher

            if pk:
                try:
                    obj = TeacherCourse.objects.get(pk=pk, teacher=teacher)
                except TeacherCourse.DoesNotExist:
                    return Response(
                        {"error": "Course not found or permission denied"},
                        status=status.HTTP_404_NOT_FOUND
                    )

                return Response(FullCourseSerializer(obj).data)

            data = TeacherCourse.objects.filter(teacher=teacher).order_by("-created_at")
            return Response(TeacherCourseSerializer(data, many=True).data)

        # ✅ STUDENT: show all active courses
        if hasattr(request.user, "student"):
            if pk:
                try:
                    obj = TeacherCourse.objects.get(pk=pk, is_active=True)
                except TeacherCourse.DoesNotExist:
                    return Response(
                        {"error": "Course not found"},
                        status=status.HTTP_404_NOT_FOUND
                    )

                return Response(FullCourseSerializer(obj).data)

            data = TeacherCourse.objects.filter(is_active=True).order_by("-created_at")
            return Response(TeacherCourseSerializer(data, many=True).data)

        return Response(
            {"error": "User profile not found"},
            status=status.HTTP_400_BAD_REQUEST
        )

    def post(self, request):
        teacher = self.get_teacher(request)

        if not teacher:
            return Response(
                {"error": "Teacher profile not found"},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = TeacherCourseSerializer(
            data=request.data,
            context={"teacher": teacher}
        )

        if serializer.is_valid():
            serializer.save(teacher=teacher)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, pk):
        teacher = self.get_teacher(request)

        if not teacher:
            return Response(
                {"error": "Teacher profile not found"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            obj = TeacherCourse.objects.get(pk=pk, teacher=teacher)
        except TeacherCourse.DoesNotExist:
            return Response(
                {"error": "Course not found or permission denied"},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = TeacherCourseSerializer(
            obj,
            data=request.data,
            partial=True,
            context={"teacher": teacher}
        )

        if serializer.is_valid():
            serializer.save(teacher=teacher)
            return Response(serializer.data)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        teacher = self.get_teacher(request)

        if not teacher:
            return Response(
                {"error": "Teacher profile not found"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            obj = TeacherCourse.objects.get(pk=pk, teacher=teacher)
        except TeacherCourse.DoesNotExist:
            return Response(
                {"error": "Course not found or permission denied"},
                status=status.HTTP_404_NOT_FOUND
            )

        obj.delete()
        return Response({"message": "Deleted"}, status=status.HTTP_204_NO_CONTENT)

# ─────────────────────────────────────────────
# 📂 SECTION API
# ─────────────────────────────────────────────

class CourseSectionAPI(APIView):

    def get(self, request, pk=None):
        if pk:
            try:
                obj = CourseSection.objects.get(pk=pk)
            except CourseSection.DoesNotExist:
                return Response({'error': 'Not found'}, status=404)
            return Response(CourseSectionSerializer(obj).data)

        data = CourseSection.objects.all()
        return Response(CourseSectionSerializer(data, many=True).data)

    def post(self, request):
        serializer = CourseSectionSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)

    def put(self, request, pk):
        try:
            obj = CourseSection.objects.get(pk=pk)
        except CourseSection.DoesNotExist:
            return Response({'error': 'Not found'}, status=404)

        serializer = CourseSectionSerializer(obj, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

    def delete(self, request, pk):
        try:
            obj = CourseSection.objects.get(pk=pk)
        except CourseSection.DoesNotExist:
            return Response({'error': 'Not found'}, status=404)

        obj.delete()
        return Response({'message': 'Deleted'}, status=204)


# ─────────────────────────────────────────────
# 🎥 VIDEO API
# ─────────────────────────────────────────────

class CourseVideoAPI(APIView):

    def get(self, request, pk=None):
        if pk:
            try:
                obj = CourseVideo.objects.get(pk=pk)
            except CourseVideo.DoesNotExist:
                return Response({'error': 'Not found'}, status=404)
            return Response(CourseVideoSerializer(obj).data)

        data = CourseVideo.objects.all()
        return Response(CourseVideoSerializer(data, many=True).data)

    def post(self, request):
        serializer = CourseVideoSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)

    def put(self, request, pk):
        try:
            obj = CourseVideo.objects.get(pk=pk)
        except CourseVideo.DoesNotExist:
            return Response({'error': 'Not found'}, status=404)

        serializer = CourseVideoSerializer(obj, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

    def delete(self, request, pk):
        try:
            obj = CourseVideo.objects.get(pk=pk)
        except CourseVideo.DoesNotExist:
            return Response({'error': 'Not found'}, status=404)

        obj.delete()
        return Response({'message': 'Deleted'}, status=204)


# ─────────────────────────────────────────────
# 📝 NOTES API
# ─────────────────────────────────────────────

class CourseNoteAPI(APIView):

    def get(self, request, pk=None):
        if pk:
            try:
                obj = CourseNote.objects.get(pk=pk)
            except CourseNote.DoesNotExist:
                return Response({'error': 'Not found'}, status=404)
            return Response(CourseNoteSerializer(obj).data)

        data = CourseNote.objects.all()
        return Response(CourseNoteSerializer(data, many=True).data)

    def post(self, request):
        serializer = CourseNoteSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)

    def put(self, request, pk):
        try:
            obj = CourseNote.objects.get(pk=pk)
        except CourseNote.DoesNotExist:
            return Response({'error': 'Not found'}, status=404)

        serializer = CourseNoteSerializer(obj, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

    def delete(self, request, pk):
        try:
            obj = CourseNote.objects.get(pk=pk)
        except CourseNote.DoesNotExist:
            return Response({'error': 'Not found'}, status=404)

        obj.delete()
        return Response({'message': 'Deleted'}, status=204)


# ─────────────────────────────────────────────
# 📚 ASSIGNMENT API
# ─────────────────────────────────────────────

class CourseAssignmentAPI(APIView):

    def get(self, request, pk=None):
        if pk:
            try:
                obj = CourseAssignment.objects.get(pk=pk)
            except CourseAssignment.DoesNotExist:
                return Response({'error': 'Not found'}, status=404)
            return Response(CourseAssignmentSerializer(obj).data)

        data = CourseAssignment.objects.all()
        return Response(CourseAssignmentSerializer(data, many=True).data)

    def post(self, request):
        serializer = CourseAssignmentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)

    def put(self, request, pk):
        try:
            obj = CourseAssignment.objects.get(pk=pk)
        except CourseAssignment.DoesNotExist:
            return Response({'error': 'Not found'}, status=404)

        serializer = CourseAssignmentSerializer(obj, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

    def delete(self, request, pk):
        try:
            obj = CourseAssignment.objects.get(pk=pk)
        except CourseAssignment.DoesNotExist:
            return Response({'error': 'Not found'}, status=404)

        obj.delete()
        return Response({'message': 'Deleted'}, status=204)


# ─────────────────────────────────────────────
# 📤 SUBMISSION API
# ─────────────────────────────────────────────

class CourseAssignmentSubmissionAPI(APIView):

    def get(self, request, pk=None):
        if pk:
            try:
                obj = CourseAssignmentSubmission.objects.get(pk=pk)
            except CourseAssignmentSubmission.DoesNotExist:
                return Response({'error': 'Not found'}, status=404)
            return Response(CourseAssignmentSubmissionSerializer(obj).data)

        data = CourseAssignmentSubmission.objects.all()
        return Response(CourseAssignmentSubmissionSerializer(data, many=True).data)

    def post(self, request):
        serializer = CourseAssignmentSubmissionSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)

    def put(self, request, pk):
        try:
            obj = CourseAssignmentSubmission.objects.get(pk=pk)
        except CourseAssignmentSubmission.DoesNotExist:
            return Response({'error': 'Not found'}, status=404)

        serializer = CourseAssignmentSubmissionSerializer(obj, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

    def delete(self, request, pk):
        try:
            obj = CourseAssignmentSubmission.objects.get(pk=pk)
        except CourseAssignmentSubmission.DoesNotExist:
            return Response({'error': 'Not found'}, status=404)

        obj.delete()
        return Response({'message': 'Deleted'}, status=204)


# ─────────────────────────────────────────────
# 📊 ENROLLMENT API
# ─────────────────────────────────────────────

class CourseEnrollmentAPI(APIView):

    def get(self, request, pk=None):
        if pk:
            try:
                obj = CourseEnrollment.objects.get(pk=pk)
            except CourseEnrollment.DoesNotExist:
                return Response({'error': 'Not found'}, status=404)

            return Response(CourseEnrollmentSerializer(obj).data)

        # ✅ Only logged-in student's enrollments
        try:
            student = Student.objects.get(user=request.user)
        except Student.DoesNotExist:
            return Response(
                {'error': 'Student profile not found'},
                status=400
            )

        data = CourseEnrollment.objects.filter(student=student)

        return Response(
            CourseEnrollmentSerializer(data, many=True).data
        )

    def post(self, request):
        serializer = CourseEnrollmentSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)

        return Response(serializer.errors, status=400)

    def put(self, request, pk):
        try:
            obj = CourseEnrollment.objects.get(pk=pk)
        except CourseEnrollment.DoesNotExist:
            return Response({'error': 'Not found'}, status=404)

        serializer = CourseEnrollmentSerializer(
            obj,
            data=request.data,
            partial=True
        )

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)

        return Response(serializer.errors, status=400)

    def delete(self, request, pk):
        try:
            obj = CourseEnrollment.objects.get(pk=pk)
        except CourseEnrollment.DoesNotExist:
            return Response({'error': 'Not found'}, status=404)

        obj.delete()
        return Response({'message': 'Deleted'}, status=204)
    
# ─────────────────────────────────────────────
# 💳 PAYMENT API
# ─────────────────────────────────────────────

class CoursePaymentAPI(APIView):

    def get(self, request, pk=None):
        if pk:
            try:
                obj = CoursePayment.objects.get(pk=pk)
            except CoursePayment.DoesNotExist:
                return Response({'error': 'Payment not found'}, status=404)

            return Response(CoursePaymentSerializer(obj).data)

        data = CoursePayment.objects.all()
        return Response(CoursePaymentSerializer(data, many=True).data)

    def post(self, request):
        try:
            student = Student.objects.get(user=request.user)
        except Student.DoesNotExist:
            return Response(
                {"error": "Student profile not found"},
                status=status.HTTP_400_BAD_REQUEST
            )

        course_id = request.data.get("course")
        payment_method = request.data.get("payment_method")

        if not course_id:
            return Response({"error": "Course is required"}, status=400)

        if not payment_method:
            return Response({"error": "Payment method is required"}, status=400)

        try:
            course = TeacherCourse.objects.get(id=course_id, is_active=True)
        except TeacherCourse.DoesNotExist:
            return Response({"error": "Course not found"}, status=404)

        if CourseEnrollment.objects.filter(course=course, student=student).exists():
            return Response(
                {"message": "Already enrolled", "already_enrolled": True},
                status=200
            )

        amount = course.price if course.is_paid else 0

        payment, created = CoursePayment.objects.get_or_create(
            course=course,
            student=student,
            defaults={
                "amount": amount,
                "payment_method": payment_method,
                "status": "pending",
            }
        )

        payment.payment_method = payment_method
        payment.amount = amount
        payment.status = "success"
        payment.transaction_id = f"TXN-{timezone.now().strftime('%Y%m%d%H%M%S')}-{student.id}"
        payment.paid_at = timezone.now()
        payment.save()

        enrollment, enrollment_created = CourseEnrollment.objects.get_or_create(
            course=course,
            student=student,
            defaults={"progress_percent": 0}
        )

        return Response(
            {
                "message": "Payment successful and enrollment completed",
                "payment": CoursePaymentSerializer(payment).data,
                "enrollment": CourseEnrollmentSerializer(enrollment).data,
            },
            status=201
        )


# ─────────────────────────────────────────────
# 🎓 CERTIFICATE API
# ─────────────────────────────────────────────

class CourseCertificateAPI(APIView):

    # 🔍 GET (list or single)
    def get(self, request, pk=None):
        if pk:
            obj = get_object_or_404(CourseCertificate, pk=pk)
            serializer = CourseCertificateSerializer(obj)
            return Response(serializer.data)

        data = CourseCertificate.objects.all()
        serializer = CourseCertificateSerializer(data, many=True)
        return Response(serializer.data)

    # 🧠 CREATE CERTIFICATE (SMART LOGIC)
    def post(self, request):
        try:
            course_id = request.data.get("course")

            if not course_id:
                return Response(
                    {"error": "Course ID is required"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # ✅ get student
            student = request.user.student

            # ✅ check enrollment
            try:
                enrollment = CourseEnrollment.objects.get(
                    course_id=course_id,
                    student=student
                )
            except CourseEnrollment.DoesNotExist:
                return Response(
                    {"error": "You are not enrolled in this course"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # ✅ check completion
            # if enrollment.progress_percent < 100:
            #     return Response(
            #         {"error": "Complete the course to get certificate"},
            #         status=status.HTTP_400_BAD_REQUEST
            #     )

            # ✅ prevent duplicate certificate
            certificate, created = CourseCertificate.objects.get_or_create(
                course_id=course_id,
                student=student,
                defaults={
                    "certificate_id": f"CERT-{uuid.uuid4().hex[:10].upper()}"
                }
            )

            serializer = CourseCertificateSerializer(certificate)

            return Response({
                "message": "Certificate generated successfully",
                "certificate": serializer.data
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    # ❌ DELETE CERTIFICATE
    def delete(self, request, pk):
        try:
            obj = CourseCertificate.objects.get(pk=pk)
            obj.delete()
            return Response(
                {"message": "Certificate deleted"},
                status=status.HTTP_204_NO_CONTENT
            )
        except CourseCertificate.DoesNotExist:
            return Response(
                {"error": "Certificate not found"},
                status=status.HTTP_404_NOT_FOUND
            )


# ─────────────────────────────────────────────
# ⭐ REVIEW API
# ─────────────────────────────────────────────

class CourseReviewAPI(APIView):

    def get(self, request, course_id=None, pk=None):
        # Single review
        if pk:
            try:
                obj = CourseReview.objects.get(pk=pk)
            except CourseReview.DoesNotExist:
                return Response(
                    {'error': 'Review not found'},
                    status=status.HTTP_404_NOT_FOUND
                )

            return Response(
                CourseReviewSerializer(obj, context={'request': request}).data
            )

        # Course-wise reviews
        if course_id:
            data = CourseReview.objects.filter(
                course_id=course_id
            ).order_by('-created_at')

            return Response(
                CourseReviewSerializer(data, many=True, context={'request': request}).data
            )

        # Fallback: all reviews
        data = CourseReview.objects.all().order_by('-created_at')

        return Response(
            CourseReviewSerializer(data, many=True, context={'request': request}).data
        )

    def post(self, request, course_id=None):
        if not course_id:
            return Response(
                {'error': 'course_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            course = TeacherCourse.objects.get(id=course_id)
        except TeacherCourse.DoesNotExist:
            return Response(
                {'error': 'Course not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        if not hasattr(request.user, 'student'):
            return Response(
                {'error': 'Only students can review courses'},
                status=status.HTTP_403_FORBIDDEN
            )

        student = request.user.student

        is_enrolled = CourseEnrollment.objects.filter(
            course=course,
            student=student
        ).exists()

        if not is_enrolled:
            return Response(
                {'error': 'You must enroll in this course before reviewing'},
                status=status.HTTP_403_FORBIDDEN
            )

        already_reviewed = CourseReview.objects.filter(
            course=course,
            student=student
        ).exists()

        if already_reviewed:
            return Response(
                {'error': 'You have already reviewed this course'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = CourseReviewSerializer(data=request.data)

        if serializer.is_valid():
            review = serializer.save(
                course=course,
                student=student
            )

            return Response(
                CourseReviewSerializer(review, context={'request': request}).data,
                status=status.HTTP_201_CREATED
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        try:
            obj = CourseReview.objects.get(pk=pk)
        except CourseReview.DoesNotExist:
            return Response(
                {'error': 'Review not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        if not hasattr(request.user, 'student') or obj.student != request.user.student:
            return Response(
                {'error': 'You can delete only your own review'},
                status=status.HTTP_403_FORBIDDEN
            )

        obj.delete()

        return Response(
            {'message': 'Deleted'},
            status=status.HTTP_204_NO_CONTENT
        )


class CourseReviewReplyAPI(APIView):

    def post(self, request, review_id):
        try:
            review = CourseReview.objects.get(id=review_id)
        except CourseReview.DoesNotExist:
            return Response(
                {'error': 'Review not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        if not hasattr(request.user, 'classteacher'):
            return Response(
                {'error': 'Only teachers can reply to reviews'},
                status=status.HTTP_403_FORBIDDEN
            )

        teacher = request.user.classteacher

        if review.course.teacher != teacher:
            return Response(
                {'error': 'You can reply only to reviews of your own course'},
                status=status.HTTP_403_FORBIDDEN
            )

        if hasattr(review, 'teacher_reply'):
            return Response(
                {'error': 'You already replied to this review'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = CourseReviewReplySerializer(data=request.data)

        if serializer.is_valid():
            reply = serializer.save(
                review=review,
                teacher=teacher
            )

            return Response(
                CourseReviewReplySerializer(reply).data,
                status=status.HTTP_201_CREATED
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



# ─────────────────────────────────────────────
# 💬 COMMENT API
# ─────────────────────────────────────────────

class CourseCommentAPI(APIView):

    def get(self, request, course_id=None, pk=None):
        # Single comment detail
        if pk:
            try:
                obj = CourseComment.objects.get(pk=pk, is_deleted=False)
            except CourseComment.DoesNotExist:
                return Response({'error': 'Comment not found'}, status=status.HTTP_404_NOT_FOUND)

            return Response(CourseCommentSerializer(obj, context={'request': request}).data)

        # Course-wise comments
        if course_id:
            data = CourseComment.objects.filter(
                course_id=course_id,
                parent=None,
                is_deleted=False
            ).order_by('-created_at')

            return Response(
                CourseCommentSerializer(data, many=True, context={'request': request}).data
            )

        # Fallback: all top-level comments
        data = CourseComment.objects.filter(
            parent=None,
            is_deleted=False
        ).order_by('-created_at')

        return Response(
            CourseCommentSerializer(data, many=True, context={'request': request}).data
        )

    def post(self, request, course_id=None):
        if not course_id:
            return Response(
                {'error': 'course_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            course = TeacherCourse.objects.get(id=course_id)
        except TeacherCourse.DoesNotExist:
            return Response({'error': 'Course not found'}, status=status.HTTP_404_NOT_FOUND)

        serializer = CourseCommentSerializer(data=request.data)

        if serializer.is_valid():
            parent = serializer.validated_data.get('parent', None)

            # Check if logged-in user is this course teacher
            is_teacher = (
                hasattr(request.user, 'classteacher') and
                course.teacher == request.user.classteacher
            )

            # Check if logged-in user is enrolled student
            is_enrolled_student = False
            if hasattr(request.user, 'student'):
                is_enrolled_student = CourseEnrollment.objects.filter(
                    course=course,
                    student=request.user.student
                ).exists()

            if not is_teacher and not is_enrolled_student:
                return Response(
                    {'error': 'Only enrolled students or the course teacher can comment.'},
                    status=status.HTTP_403_FORBIDDEN
                )

            comment = serializer.save(
                user=request.user,
                course=course,
                is_instructor_reply=is_teacher
            )

            # If teacher replies to a question, mark parent question as answered
            if parent and is_teacher:
                parent.is_answered = True
                parent.save()

            return Response(
                CourseCommentSerializer(comment, context={'request': request}).data,
                status=status.HTTP_201_CREATED
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        try:
            obj = CourseComment.objects.get(pk=pk)
        except CourseComment.DoesNotExist:
            return Response({'error': 'Comment not found'}, status=status.HTTP_404_NOT_FOUND)

        # Only comment owner can delete
        if obj.user != request.user:
            return Response(
                {'error': 'You can delete only your own comment.'},
                status=status.HTTP_403_FORBIDDEN
            )

        obj.is_deleted = True
        obj.save()

        return Response({'message': 'Deleted'}, status=status.HTTP_204_NO_CONTENT)
    
# ─────────────────────────────────────────────
# 📁 STUDENT COURSE COLLECTION API
# ─────────────────────────────────────────────

class StudentCourseCollectionAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get_student(self, request):
        try:
            return Student.objects.get(user=request.user)
        except Student.DoesNotExist:
            return None

    def get(self, request, pk=None):
        student = self.get_student(request)

        if not student:
            return Response(
                {"error": "Student profile not found"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if pk:
            try:
                collection = StudentCourseCollection.objects.get(
                    pk=pk,
                    student=student
                )
            except StudentCourseCollection.DoesNotExist:
                return Response(
                    {"error": "Collection not found"},
                    status=status.HTTP_404_NOT_FOUND
                )

            return Response(StudentCourseCollectionSerializer(collection).data)

        collections = StudentCourseCollection.objects.filter(
            student=student
        ).order_by("-updated_at")

        return Response(
            StudentCourseCollectionSerializer(collections, many=True).data
        )

    def post(self, request):
        student = self.get_student(request)

        if not student:
            return Response(
                {"error": "Student profile not found"},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = StudentCourseCollectionSerializer(data=request.data)

        if serializer.is_valid():
            collection = serializer.save(student=student)
            return Response(
                StudentCourseCollectionSerializer(collection).data,
                status=status.HTTP_201_CREATED
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, pk):
        student = self.get_student(request)

        if not student:
            return Response(
                {"error": "Student profile not found"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            collection = StudentCourseCollection.objects.get(
                pk=pk,
                student=student
            )
        except StudentCourseCollection.DoesNotExist:
            return Response(
                {"error": "Collection not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = StudentCourseCollectionSerializer(
            collection,
            data=request.data,
            partial=True
        )

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        student = self.get_student(request)

        if not student:
            return Response(
                {"error": "Student profile not found"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            collection = StudentCourseCollection.objects.get(
                pk=pk,
                student=student
            )
        except StudentCourseCollection.DoesNotExist:
            return Response(
                {"error": "Collection not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        collection.delete()
        return Response(
            {"message": "Collection deleted"},
            status=status.HTTP_204_NO_CONTENT
        )


# ─────────────────────────────────────────────
# 📌 STUDENT COURSE COLLECTION ITEM API
# ─────────────────────────────────────────────

class StudentCourseCollectionItemAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get_student(self, request):
        try:
            return Student.objects.get(user=request.user)
        except Student.DoesNotExist:
            return None

    def get(self, request, collection_id=None):
        student = self.get_student(request)

        if not student:
            return Response(
                {"error": "Student profile not found"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            collection = StudentCourseCollection.objects.get(
                id=collection_id,
                student=student
            )
        except StudentCourseCollection.DoesNotExist:
            return Response(
                {"error": "Collection not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        items = StudentCourseCollectionItem.objects.filter(
            collection=collection
        ).order_by("-added_at")

        return Response(
            StudentCourseCollectionItemSerializer(items, many=True).data
        )

    def post(self, request, collection_id=None):
        student = self.get_student(request)

        if not student:
            return Response(
                {"error": "Student profile not found"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            collection = StudentCourseCollection.objects.get(
                id=collection_id,
                student=student
            )
        except StudentCourseCollection.DoesNotExist:
            return Response(
                {"error": "Collection not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = StudentCourseCollectionItemSerializer(data=request.data)

        if serializer.is_valid():
            course = serializer.validated_data["course"]

            if not course.is_active:
                return Response(
                    {"error": "Only active courses can be saved"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            item, created = StudentCourseCollectionItem.objects.get_or_create(
                collection=collection,
                course=course
            )

            if not created:
                return Response(
                    {
                        "message": "This course is already saved in this collection.",
                        "already_saved": True,
                        "item": StudentCourseCollectionItemSerializer(item).data,
                    },
                    status=status.HTTP_200_OK
                )

            return Response(
                StudentCourseCollectionItemSerializer(item).data,
                status=status.HTTP_201_CREATED
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk=None):
        student = self.get_student(request)

        if not student:
            return Response(
                {"error": "Student profile not found"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            item = StudentCourseCollectionItem.objects.get(
                pk=pk,
                collection__student=student
            )
        except StudentCourseCollectionItem.DoesNotExist:
            return Response(
                {"error": "Saved course not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        item.delete()

        return Response(
            {"message": "Course removed from collection"},
            status=status.HTTP_204_NO_CONTENT
        )
class DeletePost(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, id):
        post = get_object_or_404(Post, id=id)  # ← NO is_removed=False here
        if post.author != request.user:
            return Response({"error": "Permission denied."}, status=403)
        if post.is_removed:
            return Response({"error": "Post already deleted."}, status=400)
        post.is_removed = True
        post.save()
        return Response({"deleted": True, "post_id": id}, status=200)

class ReportPost(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, id):
        post = get_object_or_404(Post, id=id)
        reason = request.data.get('reason', '')
        if not reason:
            return Response({"error": "Reason required."}, status=400)
        Report.objects.create(
            post=post,
            reported_by=request.user,
            reason=reason,
            message=request.data.get('message', ''),
        )
        return Response({"success": True}, status=201)

