from django.db import models
from django.contrib.auth.models import User
from Adminapp.models import Classes, College, Course, Department, School, Subject
from django.core.exceptions import ValidationError

class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('teacher', 'Teacher'), 
        ('student', 'Student'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)

    def __str__(self):
        return f"{self.user.username} - {self.role}"


class ClassTeacher(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    name = models.CharField(max_length=100)
    gender = models.CharField(max_length=10)

    school = models.ForeignKey(School, on_delete=models.SET_NULL, null=True, blank=True)
    college = models.ForeignKey(College, on_delete=models.SET_NULL, null=True, blank=True)

    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)

    previous_institute = models.CharField(max_length=200, null=True, blank=True)
    years_of_experience = models.PositiveIntegerField(null=True, blank=True)
    achievements = models.TextField(null=True, blank=True)

    def clean(self):
        # ❗ enforce either school OR college
        if self.school and self.college:
            raise ValidationError("Teacher cannot belong to both school and college")

    def __str__(self):
        return self.user.username
    
from django.db import models
from django.contrib.auth.models import User
from Adminapp.models import Classes, School, College, Course, Department


from django.core.exceptions import ValidationError

class Student(models.Model):
    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
        ('others', 'Others'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)

    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)

    class_name = models.ForeignKey(Classes, on_delete=models.SET_NULL, null=True, blank=True)
    school = models.ForeignKey(School, on_delete=models.SET_NULL, null=True, blank=True)

    college = models.ForeignKey(College, on_delete=models.SET_NULL, null=True, blank=True)
    course = models.ForeignKey(Course, on_delete=models.SET_NULL, null=True, blank=True)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        if self.school and self.college:
            raise ValidationError("Student cannot belong to both school and college")

    def __str__(self):
        return self.user.username