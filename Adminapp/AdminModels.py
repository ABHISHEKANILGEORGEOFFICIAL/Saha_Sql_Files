from django.db import models
from django.core.exceptions import ValidationError


class Classes(models.Model):
    TYPE_CHOICES = [
        ('school', 'School'),
        ('college', 'College'),
    ]

    class_name = models.CharField(max_length=100)
    type = models.CharField(max_length=10, choices=TYPE_CHOICES)

    class Meta:
        unique_together = ('class_name', 'type')

    def __str__(self):
        return f"{self.class_name} ({self.type})"


class Stream(models.Model):
    """
    Streams are tied to specific school classes (e.g. Science → 11th, 12th).
    For classes like 10th that have no stream, subjects link directly to the class.
    """
    STREAM_CHOICES = [
        ('science', 'Science'),
        ('biology', 'Biology'),
        ('humanities', 'Humanities'),
        ('commerce', 'Commerce'),
        ('general', 'General'),       # used for classes like 10th (no stream split)
    ]

    stream_name = models.CharField(max_length=20, choices=STREAM_CHOICES)

    # Which school class(es) this stream applies to
    school_class = models.ForeignKey(
        'Classes',
        on_delete=models.CASCADE,
        related_name='streams',
        limit_choices_to={'type': 'school'},
    )

    class Meta:
        unique_together = ('stream_name', 'school_class')

    def clean(self):
        if self.school_class.type != 'school':
            raise ValidationError("Stream can only be linked to a school-type class.")

    def __str__(self):
        return f"{self.get_stream_name_display()} → {self.school_class.class_name}"


class State(models.Model):
    statename = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.statename


class District(models.Model):
    state = models.ForeignKey(State, on_delete=models.CASCADE, related_name='districts')
    district_name = models.CharField(max_length=100)

    class Meta:
        unique_together = ('state', 'district_name')

    def __str__(self):
        return f"{self.district_name} ({self.state.statename})"


class School(models.Model):
    school_name = models.CharField(max_length=200)
    state = models.ForeignKey(State, on_delete=models.CASCADE, related_name='schools')
    district = models.ForeignKey(District, on_delete=models.CASCADE, related_name='schools')

    class Meta:
        unique_together = ('school_name', 'district')

    def clean(self):
        if self.district.state != self.state:
            raise ValidationError("District does not belong to selected state.")

    def __str__(self):
        return f"{self.school_name} ({self.district.district_name})"


class College(models.Model):
    college_name = models.CharField(max_length=200)
    state = models.ForeignKey(State, on_delete=models.CASCADE, related_name='colleges')
    district = models.ForeignKey(District, on_delete=models.CASCADE, related_name='colleges')

    class Meta:
        unique_together = ('college_name', 'district')

    def clean(self):
        if self.district.state != self.state:
            raise ValidationError("District does not belong to selected state.")

    def __str__(self):
        return self.college_name


class Course(models.Model):
    YEAR_CHOICES = [
        (1, '1st Year'),
        (2, '2nd Year'),
        (3, '3rd Year'),
        (4, '4th Year'),
        (5, '5th Year'),
    ]

    department = models.ForeignKey('Department', on_delete=models.CASCADE, related_name='courses')
    course_name = models.CharField(max_length=200)
    year = models.IntegerField(choices=YEAR_CHOICES)

    class Meta:
        unique_together = ('department', 'course_name', 'year')

    def __str__(self):
        return f"{self.course_name} - Year {self.year} ({self.department.department_name})"


class Department(models.Model):
    department_name = models.CharField(max_length=200, unique=True)

    def __str__(self):
        return self.department_name


class Subject(models.Model):
    """
    Unified subject model supporting both school and college subjects.

    Rules:
    ──────────────────────────────────────────────────────────────────
    School subjects
            • Must have: school_class
      • 10th (or any class whose stream is 'general'): stream is NULL
      • 11th / 12th: stream is REQUIRED (Science / Biology / Humanities / etc.)
            • department and school must be NULL

    College subjects
      • Must have: department
      • school, school_class, stream must all be NULL
    ──────────────────────────────────────────────────────────────────
    """
    SUBJECT_TYPE_CHOICES = [
        ('school', 'School'),
        ('college', 'College'),
    ]

    subject_name = models.CharField(max_length=200)
    type = models.CharField(max_length=10, choices=SUBJECT_TYPE_CHOICES)

    # ── College fields ────────────────────────────────────────────
    department = models.ForeignKey(
        Department,
        on_delete=models.CASCADE,
        related_name='subjects',
        null=True,
        blank=True,
    )

    # ── School fields ─────────────────────────────────────────────
    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name='subjects',
        null=True,
        blank=True,
    )

    # Which class this subject belongs to (e.g. 10th, 11th, 12th)
    school_class = models.ForeignKey(
        Classes,
        on_delete=models.CASCADE,
        related_name='subjects',
        null=True,
        blank=True,
        limit_choices_to={'type': 'school'},
    )

    # Stream is required for classes that have streams (11th/12th),
    # and must be NULL for classes that don't (10th → general stream row).
    stream = models.ForeignKey(
        Stream,
        on_delete=models.SET_NULL,
        related_name='subjects',
        null=True,
        blank=True,
    )

    class Meta:
        unique_together = ('type', 'department', 'school_class', 'stream', 'subject_name')

    # ── Validation ────────────────────────────────────────────────
    def clean(self):
        if self.type == 'school':
            self._validate_school_subject()
        elif self.type == 'college':
            self._validate_college_subject()

    def _validate_school_subject(self):
        if not self.school_class:
            raise ValidationError("School subject requires a class (e.g. 10th, 11th).")
        if self.school_class.type != 'school':
            raise ValidationError("school_class must be a school-type class.")
        if self.department:
            raise ValidationError("School subject cannot have a department.")
        if self.school:
            raise ValidationError("School subject is class-based and cannot be tied to a specific school.")

        # Determine whether the class requires a stream
        has_stream_defined = Stream.objects.filter(school_class=self.school_class).exists()
        is_general_only = Stream.objects.filter(
            school_class=self.school_class,
            stream_name='general'
        ).exists() and Stream.objects.filter(school_class=self.school_class).count() == 1

        if has_stream_defined and not is_general_only:
            # Class like 11th/12th — stream is mandatory
            if not self.stream:
                raise ValidationError(
                    f"Class '{self.school_class.class_name}' has multiple streams. "
                    "A stream must be selected for this subject."
                )
            # Ensure the stream actually belongs to the chosen class
            if self.stream.school_class != self.school_class:
                raise ValidationError(
                    "The selected stream does not belong to the selected class."
                )
        else:
            # Class like 10th — no stream needed
            if self.stream:
                raise ValidationError(
                    f"Class '{self.school_class.class_name}' does not use streams. "
                    "Leave stream empty."
                )

    def _validate_college_subject(self):
        if not self.department:
            raise ValidationError("College subject requires a department.")
        if self.school:
            raise ValidationError("College subject cannot have a school.")
        if self.school_class:
            raise ValidationError("College subject cannot have a school_class.")
        if self.stream:
            raise ValidationError("College subject cannot have a stream.")

    # ── Display ───────────────────────────────────────────────────
    def __str__(self):
        if self.type == 'school':
            stream_part = f" [{self.stream.get_stream_name_display()}]" if self.stream else ""
            return f"{self.subject_name} | {self.school_class.class_name}{stream_part}"
        return f"{self.subject_name} ({self.department.department_name})"