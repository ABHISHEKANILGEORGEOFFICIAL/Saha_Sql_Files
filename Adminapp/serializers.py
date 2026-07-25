from rest_framework import serializers
from .models import Classes, Stream, State, District, School, College, Course, Department, Subject


class ClassesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Classes
        fields = '__all__'


class CaseInsensitiveChoiceField(serializers.ChoiceField):
    def to_internal_value(self, data):
        if isinstance(data, str):
            data = data.strip().lower()
        return super().to_internal_value(data)


class StreamSerializer(serializers.ModelSerializer):
    stream_name = CaseInsensitiveChoiceField(choices=Stream.STREAM_CHOICES)
    school_class_name = serializers.CharField(source='school_class.class_name', read_only=True)

    class Meta:
        model = Stream
        fields = ['id', 'stream_name', 'school_class', 'school_class_name']


class StateSerializer(serializers.ModelSerializer):
    class Meta:
        model = State
        fields = '__all__'


class DistrictSerializer(serializers.ModelSerializer):
    state_name = serializers.CharField(source='state.statename', read_only=True)

    class Meta:
        model = District
        fields = ['id', 'district_name', 'state', 'state_name']


class SchoolSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='school_name', read_only=True)
    state_name = serializers.CharField(source='state.statename', read_only=True)
    district_name = serializers.CharField(source='district.district_name', read_only=True)

    class Meta:
        model = School
        fields = ['id', 'school_name', 'name', 'state', 'state_name', 'district', 'district_name']

    def validate(self, data):
        if data['district'].state != data['state']:
            raise serializers.ValidationError("District does not belong to selected state")
        return data

class CollegeSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='college_name', read_only=True)
    state_name = serializers.CharField(source='state.statename', read_only=True)
    district_name = serializers.CharField(source='district.district_name', read_only=True)

    class Meta:
        model = College
        fields = ['id', 'college_name', 'name', 'state', 'state_name', 'district', 'district_name']

    def validate(self, data):
        if data['district'].state != data['state']:
            raise serializers.ValidationError("District does not belong to selected state")
        return data

class CourseSerializer(serializers.ModelSerializer):
    department_name = serializers.CharField(source='department.department_name', read_only=True)

    class Meta:
        model = Course
        fields = '__all__'

    def to_internal_value(self, data):
        # Accept common frontend key variants without breaking existing clients.
        if hasattr(data, 'copy'):
            data = data.copy()

        if 'department' not in data:
            if 'departmentId' in data:
                data['department'] = data.get('departmentId')
            elif 'department_id' in data:
                data['department'] = data.get('department_id')

        department_value = data.get('department')
        if isinstance(department_value, dict):
            # Handle select option objects like {value: 5, label: 'CS'}.
            data['department'] = (
                department_value.get('value')
                or department_value.get('id')
                or department_value.get('pk')
            )

        if 'course_name' not in data and 'courseName' in data:
            data['course_name'] = data.get('courseName')

        if 'year' in data:
            year_value = data.get('year')
            if isinstance(year_value, dict):
                year_value = (
                    year_value.get('value')
                    or year_value.get('id')
                    or year_value.get('label')
                )
            if isinstance(year_value, str):
                normalized = year_value.strip().lower()
                year_map = {
                    '1': 1,
                    '1st': 1,
                    '1st year': 1,
                    'first year': 1,
                    '2': 2,
                    '2nd': 2,
                    '2nd year': 2,
                    'second year': 2,
                    '3': 3,
                    '3rd': 3,
                    '3rd year': 3,
                    'third year': 3,
                    '4': 4,
                    '4th': 4,
                    '4th year': 4,
                    'fourth year': 4,
                    '5': 5,
                    '5th': 5,
                    '5th year': 5,
                    'fifth year': 5,
                }
                if normalized in year_map:
                    data['year'] = year_map[normalized]
            else:
                data['year'] = year_value

        return super().to_internal_value(data)

class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = '__all__'


class SubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = '__all__'

    def validate(self, data):
        subject_type = data.get('type', getattr(self.instance, 'type', None))
        department = data.get('department', getattr(self.instance, 'department', None))
        school = data.get('school', getattr(self.instance, 'school', None))
        school_class = data.get('school_class', getattr(self.instance, 'school_class', None))
        stream = data.get('stream', getattr(self.instance, 'stream', None))

        if subject_type == 'school':
            if not school_class:
                raise serializers.ValidationError("School subject requires a class")
            if department:
                raise serializers.ValidationError("School subject cannot have a department")
            if school:
                raise serializers.ValidationError("School subject cannot have a school")

            class_streams = school_class.streams.all()
            has_non_general_streams = class_streams.exclude(stream_name='general').exists()
            if has_non_general_streams and not stream:
                raise serializers.ValidationError("This class requires a stream for subject selection")
            if stream and stream.school_class_id != school_class.id:
                raise serializers.ValidationError("Selected stream does not belong to selected class")

        if subject_type == 'college':
            if not department:
                raise serializers.ValidationError("College subject requires a department")
            if school:
                raise serializers.ValidationError("College subject cannot have a school")

        return data