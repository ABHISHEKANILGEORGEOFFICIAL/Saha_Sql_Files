from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

from Adminapp.models import Classes, School, College, Course, Subject
from Guestapp.models import ClassTeacher, Student
from communityapp.models import Post



# ─────────────────────────────────────────────
# TUITION
# ─────────────────────────────────────────────

class Tuition(models.Model):
    teacher = models.ForeignKey(
        ClassTeacher, on_delete=models.CASCADE, related_name='tuitions'
    )

    title = models.CharField(max_length=255)

    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    class_level = models.ForeignKey(Classes, on_delete=models.SET_NULL, null=True, blank=True)

    school = models.ForeignKey(School, on_delete=models.SET_NULL, null=True, blank=True)
    college = models.ForeignKey(College, on_delete=models.SET_NULL, null=True, blank=True)
    course = models.ForeignKey(Course, on_delete=models.SET_NULL, null=True, blank=True)

    description = models.TextField(blank=True)

    max_students = models.PositiveIntegerField(null=True, blank=True)

    days = models.JSONField(default=list, blank=True)
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        if self.school and self.college:
            raise ValidationError("Cannot assign both school and college.")

        if self.subject.type == 'school' and not self.school:
            raise ValidationError("School subject must have a school assigned.")

        if self.subject.type == 'college' and not self.college:
            raise ValidationError("College subject must have a college assigned.")

    def __str__(self):
        return self.title


# ─────────────────────────────────────────────
# ENROLLMENT
# ─────────────────────────────────────────────

class Enrollment(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    tuition = models.ForeignKey(Tuition, on_delete=models.CASCADE, related_name='enrollments')

    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('student', 'tuition')


# ─────────────────────────────────────────────
# RECORDED CLASS
# ─────────────────────────────────────────────

class RecordedClass(models.Model):
    tuition = models.ForeignKey(Tuition, on_delete=models.CASCADE, related_name='recordings')

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    video_url = models.URLField(blank=True, null=True)
    media_file = models.FileField(upload_to='recordings/', blank=True, null=True)

    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)


# ─────────────────────────────────────────────
# TASK
# ─────────────────────────────────────────────

class Task(models.Model):
    TASK_TYPES = [
        ('homework', 'Homework'),
        ('assignment', 'Assignment'),
        ('seminar', 'Seminar'),
        ('testpaper', 'Test Paper'),
    ]

    tuition = models.ForeignKey(Tuition, on_delete=models.CASCADE, related_name='tasks')

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    task_type = models.CharField(max_length=20, choices=TASK_TYPES)

    attachment = models.FileField(upload_to='tasks/', blank=True, null=True)

    due_date = models.DateField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)


# ─────────────────────────────────────────────
# SUBMISSION
# ─────────────────────────────────────────────

class Submission(models.Model):
    STATUS_CHOICES = [
        ('submitted', 'Submitted'),
        ('graded', 'Graded'),
        ('pending', 'Pending'),
    ]

    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='submissions')
    student = models.ForeignKey(Student, on_delete=models.CASCADE)

    content = models.TextField(blank=True)
    attachment = models.FileField(upload_to='submissions/', blank=True, null=True)

    marks = models.IntegerField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='submitted')

    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('task', 'student')


# ─────────────────────────────────────────────
# ATTENDANCE
# ─────────────────────────────────────────────

class AttendanceSession(models.Model):
    tuition = models.ForeignKey(Tuition, on_delete=models.CASCADE)

    date = models.DateField()
    topic = models.CharField(max_length=255, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('tuition', 'date')


class Attendance(models.Model):
    STATUS_CHOICES = [
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('late', 'Late'),
    ]

    session = models.ForeignKey(AttendanceSession, on_delete=models.CASCADE, related_name='records')
    student = models.ForeignKey(Student, on_delete=models.CASCADE)

    status = models.CharField(max_length=10, choices=STATUS_CHOICES)

    class Meta:
        unique_together = ('session', 'student')


# ─────────────────────────────────────────────
# TEACHER SUBJECT
# ─────────────────────────────────────────────

class TeacherSubject(models.Model):
    teacher = models.ForeignKey(ClassTeacher, on_delete=models.CASCADE, related_name='subjects')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('teacher', 'subject')


# ─────────────────────────────────────────────
# POSITION
# ─────────────────────────────────────────────

class Position(models.Model):
    POSITION_CHOICES = [
        ('leader', 'Class Leader'),
        ('assistant', 'Assistant'),
        ('monitor', 'Monitor'),
    ]

    teacher = models.ForeignKey(ClassTeacher, on_delete=models.CASCADE)
    student = models.ForeignKey(Student, on_delete=models.CASCADE)

    position = models.CharField(max_length=50, choices=POSITION_CHOICES)
    custom_position = models.CharField(max_length=100, blank=True)

    school = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)

    can_create_community = models.BooleanField(default=False)

    assigned_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateField(null=True, blank=True)

    is_active = models.BooleanField(default=True)

    # NOTE: Post and Reply have been removed from this app.
    # All social/feed functionality lives in communityapp.
    # Import from communityapp.models import Post, Reply if needed in views.


# ─────────────────────────────────────────────
# STUDY REQUEST (future mobile chat onboarding)
# ─────────────────────────────────────────────

class StudyRequest(models.Model):
    STATUS_PENDING = 'pending'
    STATUS_ACCEPTED = 'accepted'
    STATUS_REJECTED = 'rejected'

    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_ACCEPTED, 'Accepted'),
        (STATUS_REJECTED, 'Rejected'),
    ]

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='study_requests')
    teacher = models.ForeignKey(ClassTeacher, on_delete=models.CASCADE, related_name='incoming_study_requests')

    message = models.TextField(blank=True)
    source_app = models.CharField(max_length=64, default='mobile')

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    responded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    responded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def like_count(self):
        return self.likes.count()


from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils.text import slugify
from uuid import uuid4
from pathlib import Path
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator

# 🔥 IMPORT YOUR EXISTING MODELS
from Guestapp.models import ClassTeacher, Student
from Adminapp.models import Subject, Course as AcademicCourse


# ─────────────────────────────────────────────────────────────
# 🎓 TEACHER COURSE (RECORDED COURSE SYSTEM)
# ─────────────────────────────────────────────────────────────

class TeacherCourse(models.Model):
    teacher = models.ForeignKey(
        ClassTeacher,
        on_delete=models.CASCADE,
        related_name='courses'
    )

    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)

    # Optional academic mapping (BSc, etc.)
    academic_course = models.ForeignKey(
        AcademicCourse,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    # Optional: link to live tuition
    tuition = models.ForeignKey(
        'Tuition',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    title = models.CharField(max_length=300)
    description = models.TextField()

    thumbnail = models.ImageField(upload_to='course_thumbnails/', null=True, blank=True)

    is_paid = models.BooleanField(default=False)
    price = models.DecimalField(max_digits=8, decimal_places=2, default=0)

    duration_hours = models.PositiveIntegerField(default=0)

    level = models.CharField(
        max_length=20,
        choices=[
            ('beginner', 'Beginner'),
            ('intermediate', 'Intermediate'),
            ('advanced', 'Advanced')
        ],
        default='beginner'
    )

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        # 🔥 subject vs teacher validation
        if self.subject.type == "school" and not self.teacher.school:
            raise ValidationError("School subject must have a school teacher")

        if self.subject.type == "college" and not self.teacher.college:
            raise ValidationError("College subject must have a college teacher")

    def __str__(self):
        return self.title


# ─────────────────────────────────────────────────────────────
# 📂 COURSE SECTION
# ─────────────────────────────────────────────────────────────

class CourseSection(models.Model):
    course = models.ForeignKey(
        TeacherCourse,
        on_delete=models.CASCADE,
        related_name='sections'
    )

    title = models.CharField(max_length=255)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['sort_order']
        unique_together = ('course', 'sort_order')

    def __str__(self):
        return f"{self.course.title} - {self.title}"


# ─────────────────────────────────────────────────────────────
# 🎥 COURSE VIDEO
# ─────────────────────────────────────────────────────────────

def course_video_upload_path(instance, filename):
    return f"course_videos/{instance.course.id}/{filename}"


class CourseVideo(models.Model):
    section = models.ForeignKey(
        CourseSection,
        on_delete=models.CASCADE,
        related_name='videos'
    )

    course = models.ForeignKey(
        TeacherCourse,
        on_delete=models.CASCADE,
        related_name='videos'
    )

    title = models.CharField(max_length=300)
    slug = models.SlugField(blank=True)

    description = models.TextField(blank=True)

    video_url = models.URLField(blank=True)
    media_file = models.FileField(
        upload_to=course_video_upload_path,
        null=True,
        blank=True
    )

    duration_minutes = models.PositiveIntegerField(default=0)
    sort_order = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['sort_order', 'created_at']
        unique_together = ('course', 'slug')

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title) or uuid4().hex[:6]
            slug = base_slug
            counter = 1

            while CourseVideo.objects.filter(course=self.course, slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1

            self.slug = slug

        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

    @property
    def file_name(self):
        return Path(self.media_file.name).name if self.media_file else ""


# ─────────────────────────────────────────────────────────────
# 📝 COURSE NOTES
# ─────────────────────────────────────────────────────────────

class CourseNote(models.Model):
    course = models.ForeignKey(
        TeacherCourse,
        on_delete=models.CASCADE,
        related_name='notes'
    )

    section = models.ForeignKey(
        CourseSection,
        on_delete=models.CASCADE,
        related_name='notes',
        null=True,
        blank=True
    )

    title = models.CharField(max_length=300)
    content = models.TextField(blank=True)

    attachment = models.FileField(
        upload_to='course_notes/',
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


# ─────────────────────────────────────────────────────────────
# 📚 COURSE ASSIGNMENT
# ─────────────────────────────────────────────────────────────

class CourseAssignment(models.Model):
    course = models.ForeignKey(
        TeacherCourse,
        on_delete=models.CASCADE,
        related_name='assignments'
    )

    section = models.ForeignKey(
        CourseSection,
        on_delete=models.CASCADE,
        related_name='assignments',
        null=True,
        blank=True
    )

    title = models.CharField(max_length=300)
    description = models.TextField(blank=True)

    attachment = models.FileField(
        upload_to='course_assignments/',
        null=True,
        blank=True
    )

    due_date = models.DateField(null=True, blank=True)
    max_score = models.PositiveIntegerField(default=100)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


# ─────────────────────────────────────────────────────────────
# 📤 ASSIGNMENT SUBMISSION
# ─────────────────────────────────────────────────────────────

class CourseAssignmentSubmission(models.Model):
    assignment = models.ForeignKey(
        CourseAssignment,
        on_delete=models.CASCADE,
        related_name='submissions'
    )

    student = models.ForeignKey(Student, on_delete=models.CASCADE)

    content = models.TextField(blank=True)

    attachment = models.FileField(
        upload_to='assignment_submissions/',
        null=True,
        blank=True
    )

    score = models.PositiveIntegerField(null=True, blank=True)
    feedback = models.TextField(blank=True)

    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('assignment', 'student')


# ─────────────────────────────────────────────────────────────
# 📊 COURSE ENROLLMENT
# ─────────────────────────────────────────────────────────────

class CourseEnrollment(models.Model):
    course = models.ForeignKey(
        TeacherCourse,
        on_delete=models.CASCADE,
        related_name='enrollments'
    )

    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name='course_enrollments'
    )

    progress_percent = models.PositiveIntegerField(default=0)

    enrolled_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('course', 'student')

    def clean(self):
        # 🔥 enforce school/college separation
        if self.student.school and self.course.teacher.college:
            raise ValidationError("School student cannot enroll in college course")

        if self.student.college and self.course.teacher.school:
            raise ValidationError("College student cannot enroll in school course")
        
# ─────────────────────────────────────────────────────────────
# 💳 COURSE PAYMENT
# ─────────────────────────────────────────────────────────────

class CoursePayment(models.Model):
    PAYMENT_METHOD_CHOICES = [
        ('upi', 'UPI'),
        ('card', 'Card'),
        ('bank', 'Bank Transfer'),
        ('cash', 'Cash'),
    ]

    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('success', 'Success'),
        ('failed', 'Failed'),
    ]

    course = models.ForeignKey(
        TeacherCourse,
        on_delete=models.CASCADE,
        related_name='payments'
    )

    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name='course_payments'
    )

    amount = models.DecimalField(max_digits=8, decimal_places=2)

    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHOD_CHOICES
    )

    status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default='pending'
    )

    transaction_id = models.CharField(max_length=100, blank=True)

    paid_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('course', 'student')

    def __str__(self):
        return f"{self.student} - {self.course} - {self.status}"


# ─────────────────────────────────────────────────────────────
# 🎓 COURSE CERTIFICATE
# ─────────────────────────────────────────────────────────────

class CourseCertificate(models.Model):
    course = models.ForeignKey(
        TeacherCourse,
        on_delete=models.CASCADE,
        related_name='certificates'
    )

    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name='certificates'
    )

    certificate_id = models.CharField(max_length=64, unique=True, blank=True)

    issued_at = models.DateTimeField(auto_now_add=True)

    certificate_file = models.FileField(
        upload_to='certificates/',
        null=True,
        blank=True
    )

    def save(self, *args, **kwargs):
        if not self.certificate_id:
            self.certificate_id = f"CERT-{uuid4().hex.upper()}"
        super().save(*args, **kwargs)

    class Meta:
        unique_together = ('course', 'student')


# ─────────────────────────────────────────────────────────────
# ⭐ COURSE REVIEW
# ─────────────────────────────────────────────────────────────

class CourseReview(models.Model):
    course = models.ForeignKey(
        TeacherCourse,
        on_delete=models.CASCADE,
        related_name='reviews'
    )

    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name='course_reviews'
    )

    rating = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )

    comment = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('course', 'student')

    def __str__(self):
        return f"{self.student.user.username} - {self.course.title} - {self.rating}"


class CourseReviewReply(models.Model):
    review = models.OneToOneField(
        CourseReview,
        on_delete=models.CASCADE,
        related_name='teacher_reply'
    )

    teacher = models.ForeignKey(
        ClassTeacher,
        on_delete=models.CASCADE,
        related_name='review_replies'
    )

    reply = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Reply by {self.teacher.user.username}"

# ─────────────────────────────────────────────────────────────
# 💬 COURSE COMMENTS (THREADS)
# ─────────────────────────────────────────────────────────────

class CourseComment(models.Model):
    course = models.ForeignKey(
        TeacherCourse,
        on_delete=models.CASCADE,
        related_name='comments'
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE)

    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='replies'
    )

    content = models.TextField()

    is_deleted = models.BooleanField(default=False)

    is_instructor_reply = models.BooleanField(default=False)
    is_answered = models.BooleanField(default=False)

    likes = models.ManyToManyField(
        User,
        blank=True,
        related_name="liked_course_comments"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        if self.parent and self.parent.is_deleted:
            raise ValidationError("Cannot reply to deleted comment")

    def __str__(self):
        return f"{self.user.username} - {self.course.title}"
    

# ─────────────────────────────────────────────────────────────
# 📁 STUDENT COURSE COLLECTION
# ─────────────────────────────────────────────────────────────

class StudentCourseCollection(models.Model):
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name="course_collections"
    )

    name = models.CharField(max_length=120)
    description = models.TextField(blank=True)

    is_default = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("student", "name")
        ordering = ["-updated_at"]

    def __str__(self):
        return f"{self.student.user.username} - {self.name}"


class StudentCourseCollectionItem(models.Model):
    collection = models.ForeignKey(
        StudentCourseCollection,
        on_delete=models.CASCADE,
        related_name="items"
    )

    course = models.ForeignKey(
        TeacherCourse,
        on_delete=models.CASCADE,
        related_name="saved_in_collections"
    )

    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("collection", "course")
        ordering = ["-added_at"]

    def clean(self):
        if not self.course.is_active:
            raise ValidationError("Only active courses can be saved to collections.")

    def __str__(self):
        return f"{self.collection.name} - {self.course.title}"