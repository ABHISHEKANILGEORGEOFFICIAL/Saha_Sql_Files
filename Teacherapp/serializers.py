from rest_framework import serializers

from Guestapp.models import ClassTeacher, Student
from Adminapp.models import Classes, School, College, Course, Subject

# ✅ Academic models only — live in Teacherapp
from .models import (
    Tuition, Enrollment, RecordedClass,
    Task, Submission, AttendanceSession, Attendance,
    TeacherSubject, Position, StudyRequest,
)

# ✅ Social models — single source of truth in communityapp
from communityapp.models import Post, Reply


# ── MINI SERIALIZERS ──────────────────────────────────────────────────────────

class ClassTeacherMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model  = ClassTeacher
        fields = ['id', 'name']


class StudentMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Student
        fields = ['id', 'user']


# ── ACADEMIC ──────────────────────────────────────────────────────────────────

class TeacherSubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model  = TeacherSubject
        fields = '__all__'


class TuitionSerializer(serializers.ModelSerializer):
    teacher = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model  = Tuition
        fields = '__all__'

    def validate(self, data):
        subject = data.get('subject')
        school  = data.get('school')
        college = data.get('college')

        if school and college:
            raise serializers.ValidationError("Cannot assign both school and college.")
        if subject:
            if subject.type == 'school' and not school:
                raise serializers.ValidationError("School subject requires a school.")
            if subject.type == 'college' and not college:
                raise serializers.ValidationError("College subject requires a college.")
        return data


class TuitionDetailSerializer(serializers.ModelSerializer):
    teacher    = ClassTeacherMiniSerializer(read_only=True)
    tasks      = serializers.SerializerMethodField()
    recordings = serializers.SerializerMethodField()

    class Meta:
        model  = Tuition
        fields = '__all__'

    def get_tasks(self, obj):
        return {
            'assignments': TaskSerializer(
                obj.tasks.filter(task_type='assignment'), many=True).data,
            'homeworks':   TaskSerializer(
                obj.tasks.filter(task_type='homework'),   many=True).data,
            'seminars':    TaskSerializer(
                obj.tasks.filter(task_type='seminar'),    many=True).data,
            'testpapers':  TaskSerializer(
                obj.tasks.filter(task_type='testpaper'),  many=True).data,
        }

    def get_recordings(self, obj):
        return RecordedClassSerializer(obj.recordings.all(), many=True).data


class EnrollmentSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Enrollment
        fields = '__all__'


class RecordedClassSerializer(serializers.ModelSerializer):
    class Meta:
        model  = RecordedClass
        fields = '__all__'


class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Task
        fields = '__all__'


class SubmissionSerializer(serializers.ModelSerializer):
    student = StudentMiniSerializer(read_only=True)

    class Meta:
        model  = Submission
        fields = '__all__'


class AttendanceSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model  = AttendanceSession
        fields = '__all__'


class AttendanceSerializer(serializers.ModelSerializer):
    student = StudentMiniSerializer(read_only=True)

    class Meta:
        model  = Attendance
        fields = '__all__'


class PositionSerializer(serializers.ModelSerializer):
    student = StudentMiniSerializer(read_only=True)

    class Meta:
        model  = Position
        fields = '__all__'


class TeacherDashboardSerializer(serializers.Serializer):
    total_students      = serializers.IntegerField()
    total_tuitions      = serializers.IntegerField()
    total_tasks         = serializers.IntegerField()
    pending_submissions = serializers.IntegerField()


class StudyRequestSerializer(serializers.ModelSerializer):
    student_user_id = serializers.IntegerField(source='student.user_id', read_only=True)
    teacher_user_id = serializers.IntegerField(source='teacher.user_id', read_only=True)
    student_name = serializers.SerializerMethodField()
    teacher_name = serializers.SerializerMethodField()

    class Meta:
        model = StudyRequest
        fields = [
            'id',
            'student',
            'teacher',
            'student_user_id',
            'teacher_user_id',
            'student_name',
            'teacher_name',
            'message',
            'source_app',
            'status',
            'created_at',
            'responded_at',
        ]
        read_only_fields = ['status', 'created_at', 'responded_at']

    def get_student_name(self, obj):
        user = obj.student.user
        return user.get_full_name() or user.username or user.email

    def get_teacher_name(self, obj):
        return obj.teacher.name or obj.teacher.user.get_full_name() or obj.teacher.user.username


# ── SOCIAL (read from communityapp) ──────────────────────────────────────────
# These are defined here for use in Teacherapp views/urls,
# but the underlying models are communityapp.Post / communityapp.Reply.

class ReplySerializer(serializers.ModelSerializer):
    class Meta:
        model  = Reply
        fields = '__all__'


class PostSerializer(serializers.ModelSerializer):
    like_count  = serializers.SerializerMethodField()
    reply_count = serializers.SerializerMethodField()
    author_name = serializers.SerializerMethodField()

    # ✅ Send clean author_id
    author_id = serializers.IntegerField(source="author.id", read_only=True)

    # ✅ Optional (VERY useful for frontend)
    author_username = serializers.CharField(source="author.username", read_only=True)
    author_email    = serializers.CharField(source="author.email", read_only=True)

    # ✅ Keep original (if needed)
    author = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Post
        fields = [
            'id',

            # 🔥 IMPORTANT (frontend depends on this)
            'author_id',

            # Optional but useful
            'author',
            'author_name',
            'author_username',
            'author_email',

            'title',
            'content',
            'post_type',
            'image',
            'is_pinned',
            'is_removed',

            'like_count',
            'reply_count',
            'created_at',
        ]
        read_only_fields = ['author', 'created_at']

    def get_like_count(self, obj):
        return obj.likes.count()

    def get_reply_count(self, obj):
        return obj.replies.count()

    def get_author_name(self, obj):
        try:
            return obj.author.classteacher.name
        except Exception:
            return obj.author.get_full_name() or obj.author.username


class ReplySerializer(serializers.ModelSerializer):
    class Meta:
        model  = Reply
        fields = '__all__'


from rest_framework import serializers
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
    StudentCourseCollectionItem
)


# ─────────────────────────────────────────────────────────────
# 🎓 TEACHER COURSE
# ─────────────────────────────────────────────────────────────
class TeacherCourseSerializer(serializers.ModelSerializer):
    teacher_name = serializers.CharField(
      source='teacher.name',
      read_only=True
    )
    subject_name = serializers.CharField(
        source='subject.subject_name',
        read_only=True
    )

    class Meta:
        model = TeacherCourse
        fields = '__all__'
        read_only_fields = ['teacher']

    def validate(self, data):
        teacher = (
            self.context.get("teacher")
            or data.get("teacher")
            or getattr(self.instance, "teacher", None)
        )

        subject = data.get(
            "subject",
            getattr(self.instance, "subject", None)
        )

        academic_course = data.get(
            "academic_course",
            getattr(self.instance, "academic_course", None)
        )

        tuition = data.get(
            "tuition",
            getattr(self.instance, "tuition", None)
        )

        temp = TeacherCourse(
            teacher=teacher,
            subject=subject,
            academic_course=academic_course,
            tuition=tuition,
            title=data.get("title", getattr(self.instance, "title", "")),
            description=data.get("description", getattr(self.instance, "description", "")),
            thumbnail=data.get("thumbnail", getattr(self.instance, "thumbnail", None)),
            is_paid=data.get("is_paid", getattr(self.instance, "is_paid", False)),
            price=data.get("price", getattr(self.instance, "price", 0)),
            duration_hours=data.get("duration_hours", getattr(self.instance, "duration_hours", 1)),
            level=data.get("level", getattr(self.instance, "level", "beginner")),
            is_active=data.get("is_active", getattr(self.instance, "is_active", True)),
        )

        try:
            temp.clean()
        except Exception as e:
            raise serializers.ValidationError(str(e))

        return data

# ─────────────────────────────────────────────────────────────
# 📂 COURSE SECTION
# ─────────────────────────────────────────────────────────────

class CourseSectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = CourseSection
        fields = '__all__'


# ─────────────────────────────────────────────────────────────
# 🎥 COURSE VIDEO
# ─────────────────────────────────────────────────────────────

class CourseVideoSerializer(serializers.ModelSerializer):
    file_name = serializers.ReadOnlyField()

    class Meta:
        model = CourseVideo
        fields = '__all__'
        read_only_fields = ['slug', 'created_at']


# ─────────────────────────────────────────────────────────────
# 📝 COURSE NOTES
# ─────────────────────────────────────────────────────────────

class CourseNoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = CourseNote
        fields = '__all__'


# ─────────────────────────────────────────────────────────────
# 📚 COURSE ASSIGNMENT
# ─────────────────────────────────────────────────────────────

class CourseAssignmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = CourseAssignment
        fields = '__all__'


# ─────────────────────────────────────────────────────────────
# 📤 ASSIGNMENT SUBMISSION
# ─────────────────────────────────────────────────────────────

class CourseAssignmentSubmissionSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.user.username', read_only=True)

    class Meta:
        model = CourseAssignmentSubmission
        fields = '__all__'
        read_only_fields = ['score', 'feedback']


# ─────────────────────────────────────────────────────────────
# 📊 COURSE ENROLLMENT
# ─────────────────────────────────────────────────────────────

class CourseEnrollmentSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.user.username', read_only=True)

    class Meta:
        model = CourseEnrollment
        fields = '__all__'

    def validate(self, data):
        instance = CourseEnrollment(**data)
        instance.clean()
        return data
# ─────────────────────────────────────────────────────────────
# 💳 COURSE PAYMENT
# ─────────────────────────────────────────────────────────────

class CoursePaymentSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.user.username', read_only=True)
    course_title = serializers.CharField(source='course.title', read_only=True)

    class Meta:
        model = CoursePayment
        fields = '__all__'
        read_only_fields = ['amount', 'status', 'transaction_id', 'paid_at', 'created_at']

# ─────────────────────────────────────────────────────────────
# 🎓 COURSE CERTIFICATE
# ─────────────────────────────────────────────────────────────

class CourseCertificateSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.user.username', read_only=True)

    class Meta:
        model = CourseCertificate
        fields = '__all__'
        read_only_fields = ['certificate_id', 'issued_at']


# ─────────────────────────────────────────────────────────────
# ⭐ COURSE REVIEW
# ─────────────────────────────────────────────────────────────


class CourseReviewReplySerializer(serializers.ModelSerializer):
    teacher_name = serializers.CharField(source='teacher.user.username', read_only=True)

    class Meta:
        model = CourseReviewReply
        fields = '__all__'
        read_only_fields = ['teacher', 'review', 'created_at']

class CourseReviewSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.user.username', read_only=True)
    teacher_reply = CourseReviewReplySerializer(read_only=True)

    class Meta:
        model = CourseReview
        fields = '__all__'
        read_only_fields = ['student', 'course', 'created_at']


# ─────────────────────────────────────────────────────────────
# 💬 COURSE COMMENTS (THREAD SYSTEM)
# ─────────────────────────────────────────────────────────────

class CourseCommentSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    replies = serializers.SerializerMethodField()
    likes_count = serializers.SerializerMethodField()
    role = serializers.SerializerMethodField()

    class Meta:
        model = CourseComment
        fields = '__all__'
        read_only_fields = [
            'user',
            'course',
            'is_deleted',
            'is_instructor_reply',
            'created_at',
        ]

    def get_replies(self, obj):
        children = obj.replies.filter(is_deleted=False).order_by('created_at')
        return CourseCommentSerializer(
            children,
            many=True,
            context=self.context
        ).data

    def get_likes_count(self, obj):
        return obj.likes.count()

    def get_role(self, obj):
        if hasattr(obj.user, 'classteacher'):
            return "teacher"
        if hasattr(obj.user, 'student'):
            return "student"
        return "user"

# ─────────────────────────────────────────────────────────────
# 🚀 FULL COURSE (DETAIL VIEW SERIALIZER)
# ─────────────────────────────────────────────────────────────

class FullCourseSerializer(serializers.ModelSerializer):
    teacher_name = serializers.CharField(
        source='teacher.name',
        read_only=True
    )

    subject_name = serializers.CharField(
        source='subject.subject_name',
        read_only=True
    )

    sections = CourseSectionSerializer(many=True, read_only=True)
    videos = CourseVideoSerializer(many=True, read_only=True)
    notes = CourseNoteSerializer(many=True, read_only=True)
    assignments = CourseAssignmentSerializer(many=True, read_only=True)
    reviews = CourseReviewSerializer(many=True, read_only=True)

    class Meta:
        model = TeacherCourse
        fields = '__all__'

# ─────────────────────────────────────────────────────────────
# 📁 STUDENT COURSE COLLECTIONS
# ─────────────────────────────────────────────────────────────

class StudentCourseCollectionItemSerializer(serializers.ModelSerializer):
    course = TeacherCourseSerializer(read_only=True)

    course_id = serializers.PrimaryKeyRelatedField(
        source="course",
        queryset=TeacherCourse.objects.filter(is_active=True),
        write_only=True
    )

    course_title = serializers.CharField(source="course.title", read_only=True)
    course_thumbnail = serializers.ImageField(source="course.thumbnail", read_only=True)
    teacher_name = serializers.CharField(source="course.teacher.name", read_only=True)
    subject_name = serializers.CharField(source="course.subject.subject_name", read_only=True)

    class Meta:
        model = StudentCourseCollectionItem
        fields = [
            "id",
            "collection",
            "course",
            "course_id",
            "course_title",
            "course_thumbnail",
            "teacher_name",
            "subject_name",
            "added_at",
        ]
        read_only_fields = ["collection", "added_at"]


class StudentCourseCollectionSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source="student.user.username", read_only=True)
    items = StudentCourseCollectionItemSerializer(many=True, read_only=True)
    items_count = serializers.SerializerMethodField()

    class Meta:
        model = StudentCourseCollection
        fields = [
            "id",
            "student",
            "student_name",
            "name",
            "description",
            "is_default",
            "items",
            "items_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["student", "created_at", "updated_at"]

    def get_items_count(self, obj):
        return obj.items.count()