from django.urls import path
from .views import TeacherRegister, StudentRegister, LoginView

urlpatterns = [

    # 🔐 AUTH
    path('login/', LoginView.as_view()),

    # 👨‍🏫 TEACHER
    path('register/teacher/', TeacherRegister.as_view()),

    # 🎓 STUDENT
    path('register/student/', StudentRegister.as_view()),
]