from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APITestCase

from Adminapp.models import Classes, College, Department, District, School, State, Subject
from Guestapp.models import ClassTeacher
from .models import Tuition


class TuitionListCreateTests(APITestCase):
	def setUp(self):
		self.user = User.objects.create_user(username='teacher1', password='testpass123')

		self.state = State.objects.create(statename='Kerala')
		self.district = District.objects.create(state=self.state, district_name='Kollam')
		self.school = School.objects.create(
			school_name='Govt School',
			state=self.state,
			district=self.district,
		)
		self.class_level = Classes.objects.create(class_name='10', type='school')
		self.subject = Subject.objects.create(
			subject_name='Mathematics',
			type='school',
			school=self.school,
			school_class=self.class_level,
		)
		self.teacher = ClassTeacher.objects.create(
			user=self.user,
			name='Teacher One',
			gender='male',
			school=self.school,
		)

	def test_create_tuition_uses_authenticated_teacher_school_when_body_omits_it(self):
		self.client.force_authenticate(user=self.user)

		response = self.client.post(
			'/api/tuition/',
			{
				'title': 'Evening Maths Tuition',
				'subject': self.subject.id,
				'class_level': self.class_level.id,
				'description': 'For class 10 students',
				'days': ['monday', 'wednesday'],
			},
			format='json',
		)

		self.assertEqual(response.status_code, status.HTTP_201_CREATED)
		tuition = Tuition.objects.get()
		self.assertEqual(tuition.teacher, self.teacher)
		self.assertEqual(tuition.school, self.school)

	def test_college_teacher_can_create_college_tuition_without_school(self):
		college_user = User.objects.create_user(username='teacher2', password='testpass123')
		department = Department.objects.create(department_name='Physics')
		college = College.objects.create(
			college_name='City College',
			state=self.state,
			district=self.district,
		)
		college_subject = Subject.objects.create(
			subject_name='Quantum Mechanics',
			type='college',
			department=department,
		)
		college_teacher = ClassTeacher.objects.create(
			user=college_user,
			name='Teacher Two',
			gender='female',
			college=college,
			department=department,
		)

		self.client.force_authenticate(user=college_user)

		response = self.client.post(
			'/api/tuition/',
			{
				'title': 'BSc Physics Tuition',
				'subject': college_subject.id,
				'description': 'For undergraduate physics students',
			},
			format='json',
		)

		self.assertEqual(response.status_code, status.HTTP_201_CREATED)
		tuition = Tuition.objects.get(title='BSc Physics Tuition')
		self.assertEqual(tuition.teacher, college_teacher)
		self.assertEqual(tuition.college, college)

	def test_college_teacher_gets_profile_error_for_school_subject(self):
		college_user = User.objects.create_user(username='teacher3', password='testpass123')
		department = Department.objects.create(department_name='Mathematics')
		college = College.objects.create(
			college_name='Science College',
			state=self.state,
			district=self.district,
		)
		ClassTeacher.objects.create(
			user=college_user,
			name='Teacher Three',
			gender='female',
			college=college,
			department=department,
		)

		self.client.force_authenticate(user=college_user)

		response = self.client.post(
			'/api/tuition/',
			{
				'title': 'School Maths Tuition',
				'subject': self.subject.id,
				'class_level': self.class_level.id,
			},
			format='json',
		)

		self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
		self.assertEqual(
			response.data['error'],
			'Your teacher profile does not have a school assigned. Choose a college subject or contact admin.',
		)
