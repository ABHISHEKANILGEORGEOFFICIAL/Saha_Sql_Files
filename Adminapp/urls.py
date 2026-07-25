from django.urls import path
from .views import *

urlpatterns = [

    path('classes/', ClassAPI.as_view()),
    path('classes/<int:pk>/', ClassAPI.as_view()),

    path('streams/', StreamAPI.as_view()),
    path('streams/<int:pk>/', StreamAPI.as_view()),

    path('states/', StateAPI.as_view()),
    path('states/<int:pk>/', StateAPI.as_view()),

    path('districts/', DistrictAPI.as_view()),
    path('districts/<int:pk>/', DistrictAPI.as_view()),

    path('schools/', SchoolAPI.as_view()),
    path('schools/<int:pk>/', SchoolAPI.as_view()),

    path('colleges/', CollegeAPI.as_view()),
    path('colleges/<int:pk>/', CollegeAPI.as_view()),

    path('courses/', CourseAPI.as_view()),
    path('courses/<int:pk>/', CourseAPI.as_view()),
    path('course-years/', CourseYearsAPI.as_view()),

    path('departments/', DepartmentAPI.as_view()),
    path('departments/<int:pk>/', DepartmentAPI.as_view()),

    path('subjects/', SubjectAPI.as_view()),
    path('subjects/<int:pk>/', SubjectAPI.as_view()),
]