from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APIRequestFactory

from .models import UserProfile
from .views import LoginView


class LoginViewTestCase(TestCase):
	def setUp(self):
		self.factory = APIRequestFactory()
		self.view = LoginView.as_view()
		self.user = User.objects.create_user(
			username='teacher@example.com',
			email='teacher@example.com',
			password='secret123',
		)
		UserProfile.objects.create(user=self.user, role='teacher')

	def test_login_succeeds_with_email(self):
		request = self.factory.post(
			'/login/',
			{'email': 'Teacher@Example.com', 'password': 'secret123'},
			format='json',
		)

		response = self.view(request)

		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.data['role'], 'teacher')
		self.assertEqual(response.data['email'], 'teacher@example.com')
		self.assertIn('access_token', response.data)

	def test_login_requires_email(self):
		request = self.factory.post('/login/', {'password': 'secret123'}, format='json')

		response = self.view(request)

		self.assertEqual(response.status_code, 400)
		self.assertEqual(response.data['error'], 'Email and password are required')
