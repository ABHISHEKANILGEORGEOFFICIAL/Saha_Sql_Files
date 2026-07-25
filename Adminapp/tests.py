from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIRequestFactory
from rest_framework.test import force_authenticate

from .models import Classes, College, Course, Department, District, School, State, Stream, Subject
from .views import CollegeAPI, CourseAPI, CourseYearsAPI, SchoolAPI, StreamAPI, SubjectAPI


class SubjectAPITestCase(TestCase):
	def setUp(self):
		self.factory = APIRequestFactory()
		self.view = SubjectAPI.as_view()
		self.user = User.objects.create_user(username='admin', password='secret123')

		self.state = State.objects.create(statename='Kerala')
		self.district = District.objects.create(state=self.state, district_name='Kollam')
		self.school_one = School.objects.create(
			school_name='School One',
			state=self.state,
			district=self.district,
		)
		self.school_two = School.objects.create(
			school_name='School Two',
			state=self.state,
			district=self.district,
		)

		Subject.objects.create(subject_name='Maths', type='school', school=self.school_one)
		Subject.objects.create(subject_name='Science', type='school', school=self.school_two)

	def test_subjects_are_not_restricted_by_school_selection(self):
		request = self.factory.get('/subjects/', {'type': 'school', 'school': self.school_one.id})
		force_authenticate(request, user=self.user)

		response = self.view(request)

		self.assertEqual(response.status_code, 200)
		self.assertEqual(len(response.data), 2)


class InstitutionAPITestCase(TestCase):
	def setUp(self):
		self.factory = APIRequestFactory()
		self.school_view = SchoolAPI.as_view()
		self.college_view = CollegeAPI.as_view()
		self.user = User.objects.create_user(username='staff', password='secret123')

		self.state = State.objects.create(statename='Kerala')
		self.district = District.objects.create(state=self.state, district_name='Ernakulam')
		self.school = School.objects.create(
			school_name='Govt School Kochi',
			state=self.state,
			district=self.district,
		)
		self.college = College.objects.create(
			college_name='Cochin University',
			state=self.state,
			district=self.district,
		)

	def test_school_list_exposes_generic_name_field(self):
		request = self.factory.get('/schools/')
		force_authenticate(request, user=self.user)

		response = self.school_view(request)

		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.data[0]['school_name'], 'Govt School Kochi')
		self.assertEqual(response.data[0]['name'], 'Govt School Kochi')

	def test_college_list_exposes_generic_name_field(self):
		request = self.factory.get('/colleges/')
		force_authenticate(request, user=self.user)

		response = self.college_view(request)

		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.data[0]['college_name'], 'Cochin University')
		self.assertEqual(response.data[0]['name'], 'Cochin University')


class StreamAndSubjectSelectionTestCase(TestCase):
	def setUp(self):
		self.factory = APIRequestFactory()
		self.stream_view = StreamAPI.as_view()
		self.subject_view = SubjectAPI.as_view()
		self.user = User.objects.create_user(username='selector', password='secret123')

		self.state = State.objects.create(statename='Kerala')
		self.district = District.objects.create(state=self.state, district_name='Thrissur')
		self.school = School.objects.create(
			school_name='Model School',
			state=self.state,
			district=self.district,
		)

		self.class_10 = Classes.objects.create(class_name='10th', type='school')
		self.class_11 = Classes.objects.create(class_name='11th', type='school')

		self.general_stream = Stream.objects.create(stream_name='general', school_class=self.class_10)
		self.science_stream = Stream.objects.create(stream_name='science', school_class=self.class_11)
		self.commerce_stream = Stream.objects.create(stream_name='commerce', school_class=self.class_11)

		Subject.objects.create(
			subject_name='Mathematics',
			type='school',
			school=self.school,
			school_class=self.class_10,
			stream=None,
		)
		Subject.objects.create(
			subject_name='Physics',
			type='school',
			school=self.school,
			school_class=self.class_11,
			stream=self.science_stream,
		)
		Subject.objects.create(
			subject_name='Accountancy',
			type='school',
			school=self.school,
			school_class=self.class_11,
			stream=self.commerce_stream,
		)

	def test_streams_can_be_filtered_by_class(self):
		request = self.factory.get('/streams/', {'school_class': self.class_11.id})
		force_authenticate(request, user=self.user)

		response = self.stream_view(request)

		self.assertEqual(response.status_code, 200)
		self.assertEqual(len(response.data), 2)
		self.assertSetEqual(
			{row['stream_name'] for row in response.data},
			{'science', 'commerce'},
		)

	def test_subjects_for_stream_split_class_require_stream_query(self):
		request = self.factory.get(
			'/subjects/',
			{'type': 'school', 'school_class': self.class_11.id},
		)
		force_authenticate(request, user=self.user)

		response = self.subject_view(request)

		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.data, [])

	def test_subjects_for_stream_split_class_return_when_stream_selected(self):
		request = self.factory.get(
			'/subjects/',
			{
				'type': 'school',
				'school_class': self.class_11.id,
				'stream': self.science_stream.id,
			},
		)
		force_authenticate(request, user=self.user)

		response = self.subject_view(request)

		self.assertEqual(response.status_code, 200)
		self.assertEqual(len(response.data), 1)
		self.assertEqual(response.data[0]['subject_name'], 'Physics')

	def test_stream_create_accepts_case_insensitive_choice_value(self):
		request = self.factory.post(
			'/streams/',
			{'stream_name': 'Science', 'school_class': self.class_10.id},
			format='json',
		)
		force_authenticate(request, user=self.user)

		response = self.stream_view(request)

		self.assertEqual(response.status_code, 201)
		self.assertEqual(response.data['stream_name'], 'science')


class CourseAPITestCase(TestCase):
	def setUp(self):
		self.factory = APIRequestFactory()
		self.view = CourseAPI.as_view()
		self.user = User.objects.create_user(username='course-admin', password='secret123')
		self.department = Department.objects.create(department_name='Computer Science')

	def test_invalid_course_create_returns_bad_request(self):
		request = self.factory.post(
			'/courses/',
			{'course_name': 'BSc Computer Science', 'year': 1},
			format='json',
		)
		force_authenticate(request, user=self.user)

		response = self.view(request)

		self.assertEqual(response.status_code, 400)
		self.assertIn('department', response.data)
		self.assertEqual(Course.objects.count(), 0)

	def test_valid_course_create_persists_and_returns_created(self):
		request = self.factory.post(
			'/courses/',
			{'course_name': 'BSc Computer Science', 'year': 1, 'department': self.department.id},
			format='json',
		)
		force_authenticate(request, user=self.user)

		response = self.view(request)

		self.assertEqual(response.status_code, 201)
		self.assertEqual(Course.objects.count(), 1)
		self.assertEqual(response.data['course_name'], 'BSc Computer Science')
		self.assertEqual(response.data['department'], self.department.id)

	def test_courses_can_be_filtered_by_year(self):
		dept2 = Department.objects.create(department_name='Physics')
		Course.objects.create(course_name='BSc Physics', year=1, department=dept2)
		Course.objects.create(course_name='MSc Physics', year=2, department=dept2)

		request = self.factory.get('/courses/', {'year': 1})

		response = CourseAPI.as_view()(request)

		self.assertEqual(response.status_code, 200)
		self.assertEqual(len(response.data), 1)
		self.assertEqual(response.data[0]['course_name'], 'BSc Physics')

	def test_course_years_endpoint_returns_all_choices(self):
		request = self.factory.get('/course-years/')

		response = CourseYearsAPI.as_view()(request)

		self.assertEqual(response.status_code, 200)
		values = [row['value'] for row in response.data]
		self.assertEqual(values, [1, 2, 3, 4, 5])
