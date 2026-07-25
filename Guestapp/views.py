from django.contrib.auth.models import User
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from django.db import transaction
from django.contrib.auth import authenticate
from .models import ClassTeacher, Student, UserProfile
from rest_framework_simplejwt.tokens import RefreshToken


class TeacherRegister(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        try:
            email = request.data.get('email')
            password = request.data.get('password')
            name = request.data.get('name')
            gender = request.data.get('gender')

            # 🔥 VALIDATION
            if not email or not password:
                return Response(
                    {'error': 'Email and password are required'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if User.objects.filter(username=email).exists():
                return Response(
                    {'error': 'Email already exists'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # 🔥 TRANSACTION (IMPORTANT)
            with transaction.atomic():

                # ✅ CREATE USER (email as username)
                user = User.objects.create_user(
                    username=email,
                    email=email,
                    password=password,
                    first_name=name or "",
                )

                # ✅ USER ROLE PROFILE
                UserProfile.objects.create(user=user, role='teacher')


                # ✅ TEACHER PROFILE
                ClassTeacher.objects.create(
                    user=user,
                    name=name,
                    gender=gender,

                    school_id=request.data.get('school') or None,
                    college_id=request.data.get('college') or None,
                    department_id=request.data.get('department') or None,

                    previous_institute=request.data.get('previous_institute'),
                    years_of_experience=request.data.get('years_of_experience') or None,
                    achievements=request.data.get('achievements'),
                )

            return Response(
                {'message': 'Teacher registered successfully'},
                status=status.HTTP_201_CREATED
            )

        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
            
            
class StudentRegister(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        try:
            email = request.data.get('email')
            password = request.data.get('password')
            name = request.data.get('name')
            gender = request.data.get('gender')

            # 🔥 VALIDATION
            if not email or not password:
                return Response(
                    {'error': 'Email and password are required'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if User.objects.filter(username=email).exists():
                return Response(
                    {'error': 'Email already exists'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # 🔥 TRANSACTION
            with transaction.atomic():

                # ✅ CREATE USER
                user = User.objects.create_user(
                    username=email,
                    email=email,
                    password=password,
                    first_name=name or "",
                )

                # ✅ PROFILE
                UserProfile.objects.create(user=user, role='student')

                # ✅ STUDENT PROFILE
                school_id = request.data.get('school') or None
                college_id = request.data.get('college') or None
                # class_name is a school-only FK; ignore it for college students
                class_name_id = (request.data.get('class_name') or None) if school_id else None
                Student.objects.create(
                    user=user,
                    gender=gender,
                    class_name_id=class_name_id,
                    school_id=school_id,
                    college_id=college_id,
                    course_id=request.data.get('course') or None,
                    department_id=request.data.get('department') or None,
                )

            return Response(
                {'message': 'Student registered successfully'},
                status=status.HTTP_201_CREATED
            )

        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    
class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = (request.data.get('email') or '').strip().lower()
        password = request.data.get('password')

        if not email or not password:
            return Response(
                {'error': 'Email and password are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Email is the only supported login identifier.
        user_obj = User.objects.filter(email__iexact=email).first()
        user = None

        if user_obj:
            user = authenticate(username=user_obj.username, password=password)

        if user is None:
            return Response({'error': 'Invalid credentials'}, status=401)

        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)

        # ADMIN
        if user.is_superuser:
            return Response({
                'message': 'Admin login successful',
                'role': 'admin',
                'user_id': user.id,
                'email': user.email,
                'access_token': access_token,
                'refresh_token': str(refresh),
            })

        # ROLE
        try:
            profile = UserProfile.objects.get(user=user)
        except UserProfile.DoesNotExist:
            return Response({'error': 'User role not assigned'}, status=400)

        return Response({
            'message': 'Login successful',
            'role': profile.role,
            'user_id': user.id,
            'email': user.email,
            'access_token': access_token,
            'refresh_token': str(refresh),
        })