from itertools import count
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework import status
from Guestapp.models import ClassTeacher

from communityapp.models import Report
from .models import (
    Classes, Stream, State, District, School,
    College, Course, Department, Subject
)

from .serializers import (
    ClassesSerializer, StreamSerializer, StateSerializer, DistrictSerializer,
    SchoolSerializer, CollegeSerializer, CourseSerializer,
    DepartmentSerializer, SubjectSerializer
)


class ClassAPI(APIView):

    def get_permissions(self):
        if self.request.method in ('GET', 'HEAD', 'OPTIONS'):
            return [AllowAny()]
        return [IsAuthenticated()]

    def get(self, request, pk=None):
        if pk:
            try:
                obj = Classes.objects.get(pk=pk)
            except Classes.DoesNotExist:
                return Response({'error': 'Not found'}, status=404)
            return Response(ClassesSerializer(obj).data)

        data = Classes.objects.all()
        return Response(ClassesSerializer(data, many=True).data)

    def post(self, request):
        serializer = ClassesSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)

    def put(self, request, pk):
        try:
            obj = Classes.objects.get(pk=pk)
        except Classes.DoesNotExist:
            return Response({'error': 'Not found'}, status=404)

        serializer = ClassesSerializer(obj, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

    def delete(self, request, pk):
        try:
            obj = Classes.objects.get(pk=pk)
        except Classes.DoesNotExist:
            return Response({'error': 'Not found'}, status=404)

        obj.delete()
        return Response({'message': 'Deleted'}, status=204)


class StreamAPI(APIView):

    def get_permissions(self):
        if self.request.method in ('GET', 'HEAD', 'OPTIONS'):
            return [AllowAny()]
        return [IsAuthenticated()]

    def get(self, request, pk=None):
        if pk:
            try:
                obj = Stream.objects.get(pk=pk)
            except Stream.DoesNotExist:
                return Response({'error': 'Not found'}, status=404)
            return Response(StreamSerializer(obj).data)

        data = Stream.objects.all()
        school_class_id = request.query_params.get('school_class')
        if school_class_id:
            data = data.filter(school_class_id=school_class_id)

        return Response(StreamSerializer(data, many=True).data)

    def post(self, request):
        serializer = StreamSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)

    def put(self, request, pk):
        try:
            obj = Stream.objects.get(pk=pk)
        except Stream.DoesNotExist:
            return Response({'error': 'Not found'}, status=404)

        serializer = StreamSerializer(obj, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

    def delete(self, request, pk):
        try:
            obj = Stream.objects.get(pk=pk)
        except Stream.DoesNotExist:
            return Response({'error': 'Not found'}, status=404)

        obj.delete()
        return Response({'message': 'Deleted'}, status=204)
    
class StateAPI(APIView):

    def get_permissions(self):
        if self.request.method in ('GET', 'HEAD', 'OPTIONS'):
            return [AllowAny()]
        return [IsAuthenticated()]

    def get(self, request, pk=None):
        if pk:
            try:
                obj = State.objects.get(pk=pk)
            except State.DoesNotExist:
                return Response({'error': 'Not found'}, status=404)
            return Response(StateSerializer(obj).data)

        data = State.objects.all()
        return Response(StateSerializer(data, many=True).data)

    def post(self, request):
        serializer = StateSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors)

    def put(self, request, pk):
        try:
            obj = State.objects.get(pk=pk)
        except State.DoesNotExist:
            return Response({'error': 'Not found'}, status=404)

        serializer = StateSerializer(obj, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors)

    def delete(self, request, pk):
        obj = State.objects.get(pk=pk)
        obj.delete()
        return Response({'message': 'Deleted'})
    
class DistrictAPI(APIView):

    def get_permissions(self):
        if self.request.method in ('GET', 'HEAD', 'OPTIONS'):
            return [AllowAny()]
        return [IsAuthenticated()]

    def get(self, request, pk=None):
        if pk:
            obj = District.objects.get(pk=pk)
            return Response(DistrictSerializer(obj).data)

        data = District.objects.all()
        return Response(DistrictSerializer(data, many=True).data)

    def post(self, request):
        serializer = DistrictSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors)

    def put(self, request, pk):
        obj = District.objects.get(pk=pk)
        serializer = DistrictSerializer(obj, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors)

    def delete(self, request, pk):
        obj = District.objects.get(pk=pk)
        obj.delete()
        return Response({'message': 'Deleted'})
    
class SchoolAPI(APIView):

    def get_permissions(self):
        if self.request.method in ('GET', 'HEAD', 'OPTIONS'):
            return [AllowAny()]
        return [IsAuthenticated()]

    def get(self, request, pk=None):
        if pk:
            obj = School.objects.get(pk=pk)
            return Response(SchoolSerializer(obj).data)

        data = School.objects.all()
        return Response(SchoolSerializer(data, many=True).data)

    def post(self, request):
        serializer = SchoolSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors)

    def put(self, request, pk):
        obj = School.objects.get(pk=pk)
        serializer = SchoolSerializer(obj, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors)

    def delete(self, request, pk):
        obj = School.objects.get(pk=pk)
        obj.delete()
        return Response({'message': 'Deleted'})
    
class CollegeAPI(APIView):

    def get_permissions(self):
        if self.request.method in ('GET', 'HEAD', 'OPTIONS'):
            return [AllowAny()]
        return [IsAuthenticated()]

    def get(self, request, pk=None):
        if pk:
            obj = College.objects.get(pk=pk)
            return Response(CollegeSerializer(obj).data)

        data = College.objects.all()
        return Response(CollegeSerializer(data, many=True).data)

    def post(self, request):
        serializer = CollegeSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors)

    def put(self, request, pk):
        obj = College.objects.get(pk=pk)
        serializer = CollegeSerializer(obj, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors)

    def delete(self, request, pk):
        obj = College.objects.get(pk=pk)
        obj.delete()
        return Response({'message': 'Deleted'})
    
class CourseAPI(APIView):

    def get_permissions(self):
        if self.request.method in ('GET', 'HEAD', 'OPTIONS'):
            return [AllowAny()]
        return [IsAuthenticated()]

    def get(self, request, pk=None):
        if pk:
            obj = Course.objects.get(pk=pk)
            return Response(CourseSerializer(obj).data)

        data = Course.objects.all()
        department_id = request.query_params.get('department')
        year = request.query_params.get('year')
        if department_id:
            data = data.filter(department_id=department_id)
        if year:
            data = data.filter(year=year)
        return Response(CourseSerializer(data, many=True).data)

    def post(self, request):
        serializer = CourseSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)

    def put(self, request, pk):
        obj = Course.objects.get(pk=pk)
        serializer = CourseSerializer(obj, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

    def delete(self, request, pk):
        obj = Course.objects.get(pk=pk)
        obj.delete()
        return Response({'message': 'Deleted'})
    
class CourseYearsAPI(APIView):
    """Return the valid year choices so the frontend can populate the year selector."""

    def get_permissions(self):
        return [AllowAny()]

    def get(self, request):
        years = [
            {'value': value, 'label': label}
            for value, label in Course.YEAR_CHOICES
        ]
        return Response(years)


class DepartmentAPI(APIView):

    def get_permissions(self):
        if self.request.method in ('GET', 'HEAD', 'OPTIONS'):
            return [AllowAny()]
        return [IsAuthenticated()]

    def get(self, request, pk=None):
        if pk:
            obj = Department.objects.get(pk=pk)
            return Response(DepartmentSerializer(obj).data)

        data = Department.objects.all()
        return Response(DepartmentSerializer(data, many=True).data)

    def post(self, request):
        serializer = DepartmentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors)

    def put(self, request, pk):
        obj = Department.objects.get(pk=pk)
        serializer = DepartmentSerializer(obj, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors)

    def delete(self, request, pk):
        obj = Department.objects.get(pk=pk)
        obj.delete()
        return Response({'message': 'Deleted'})
    
class SubjectAPI(APIView):

    def get_permissions(self):
        if self.request.method in ('GET', 'HEAD', 'OPTIONS'):
            return [AllowAny()]
        return [IsAuthenticated()]

    def get(self, request, pk=None):
        if pk:
            obj = Subject.objects.get(pk=pk)
            return Response(SubjectSerializer(obj).data)

        data = Subject.objects.all()

        # ✅ NEW: filter subjects for logged-in teacher
        my_subjects = request.query_params.get('my_subjects')

        if my_subjects == 'true' and request.user.is_authenticated:
            try:
                teacher = ClassTeacher.objects.get(user=request.user)

                if teacher.school:
                    data = data.filter(type='school')

                elif teacher.college:
                    data = data.filter(type='college')

                    if teacher.department:
                        data = data.filter(department=teacher.department)

                else:
                    data = data.none()

            except ClassTeacher.DoesNotExist:
                data = data.none()

        subject_type = request.query_params.get('type')
        department_id = request.query_params.get('department')
        school_class_id = request.query_params.get('school_class')
        stream_id = request.query_params.get('stream')

        if subject_type:
            data = data.filter(type=subject_type)

        if department_id:
            data = data.filter(department_id=department_id)

        if school_class_id:
            data = data.filter(school_class_id=school_class_id)

        if stream_id:
            data = data.filter(stream_id=stream_id)

        if school_class_id and not stream_id:
            class_streams = Stream.objects.filter(school_class_id=school_class_id)
            has_non_general_streams = class_streams.exclude(stream_name='general').exists()

            if has_non_general_streams:
                data = data.none()
            else:
                data = data.filter(stream__isnull=True)

        return Response(SubjectSerializer(data, many=True).data)

    def post(self, request):
        serializer = SubjectSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors)

    def put(self, request, pk):
        obj = Subject.objects.get(pk=pk)
        serializer = SubjectSerializer(obj, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors)

    def delete(self, request, pk):
        obj = Subject.objects.get(pk=pk)
        obj.delete()
        return Response({'message': 'Deleted'})
    
class AdminReports(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not request.user.is_staff:
            return Response({"error": "Admin only"}, status=403)

        reports = (
            Report.objects
            .values(
                'post',
                'post__content',
                'post__author__username'
            )
            .annotate(total=count('id'))
            .order_by('-total')
        )

        return Response(reports)
    
class AdminPostReportDetails(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, post_id):
        if not request.user.is_staff:
            return Response({"error": "Admin only"}, status=403)

        reports = Report.objects.filter(post_id=post_id)

        data = [
            {
                "id": r.id,
                "reported_by": r.reported_by.username,
                "reason": r.reason,
                "message": r.message,
                "status": r.status,
                "created_at": r.created_at,
            }
            for r in reports
        ]

        return Response(data)
