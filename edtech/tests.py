from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User

from .models import Subject, UserProfile, TeacherProfile


class EdTechSmokeTests(TestCase):
    def setUp(self):
        self.subject = Subject.objects.create(name="Mathematics", category="School", active=True)

    def test_home_page(self):
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Learn Today")

    def test_student_registration_and_dashboard(self):
        response = self.client.post(reverse("register", args=["student"]), {
            "first_name": "Test", "last_name": "Student", "username": "student1",
            "email": "student@example.com", "password": "StrongPass123!",
            "confirm_password": "StrongPass123!",
        })
        self.assertRedirects(response, reverse("dashboard"))
        self.assertTrue(UserProfile.objects.filter(user__username="student1", role="student").exists())

    def test_subject_detail(self):
        response = self.client.get(reverse("subject_detail", args=[self.subject.slug]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Mathematics")

    def test_find_tutor_filter(self):
        user = User.objects.create_user("teacher1", password="StrongPass123!")
        UserProfile.objects.create(user=user, role="teacher")
        teacher = TeacherProfile.objects.create(user=user, hourly_fee=500)
        teacher.subjects.add(self.subject)
        response = self.client.get(reverse("find_tutor"), {"subject": self.subject.pk})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "teacher1")
