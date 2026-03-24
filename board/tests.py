from django.contrib.auth.models import User
from django.core import mail
from django.test import Client, TestCase
from django.urls import reverse

from .models import Advertisement, RegistrationConfirmation, Response


class RegistrationFlowTests(TestCase):
    def test_signup_sends_confirmation_code(self):
        response = self.client.post(
            reverse("board:signup"),
            {
                "email": "hero@example.com",
                "password1": "StrongPassword123",
                "password2": "StrongPassword123",
            },
        )

        self.assertRedirects(response, reverse("board:confirm_registration"))
        user = User.objects.get(email="hero@example.com")
        self.assertFalse(user.is_active)
        self.assertTrue(RegistrationConfirmation.objects.filter(user=user).exists())
        self.assertEqual(len(mail.outbox), 1)

    def test_confirmation_activates_user(self):
        user = User.objects.create_user(
            username="hero@example.com",
            email="hero@example.com",
            password="StrongPassword123",
            is_active=False,
        )
        RegistrationConfirmation.objects.create(user=user, code="123456")

        response = self.client.post(
            reverse("board:confirm_registration"),
            {"email": "hero@example.com", "code": "123456"},
        )

        self.assertRedirects(response, reverse("board:advertisement_list"))
        user.refresh_from_db()
        self.assertTrue(user.is_active)


class ResponseFlowTests(TestCase):
    def setUp(self):
        self.author = User.objects.create_user(
            username="author@example.com",
            email="author@example.com",
            password="StrongPassword123",
        )
        self.reader = User.objects.create_user(
            username="reader@example.com",
            email="reader@example.com",
            password="StrongPassword123",
        )
        self.advertisement = Advertisement.objects.create(
            author=self.author,
            category="tanks",
            title="Ищу танка",
            content="<p>Рейд в субботу</p>",
        )

    def test_response_creation_sends_email(self):
        self.client.login(username="reader@example.com", password="StrongPassword123")

        response = self.client.post(
            reverse("board:create_response", args=[self.advertisement.pk]),
            {"text": "Готов присоединиться"},
        )

        self.assertRedirects(response, reverse("board:advertisement_detail", args=[self.advertisement.pk]))
        self.assertEqual(Response.objects.count(), 1)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("Новый отклик", mail.outbox[0].subject)

    def test_owner_can_accept_response(self):
        feedback = Response.objects.create(
            advertisement=self.advertisement,
            author=self.reader,
            text="Готов присоединиться",
        )
        self.client.login(username="author@example.com", password="StrongPassword123")

        response = self.client.post(reverse("board:accept_response", args=[feedback.pk]))

        self.assertRedirects(response, reverse("board:response_list"))
        feedback.refresh_from_db()
        self.assertEqual(feedback.status, Response.Status.ACCEPTED)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("принят", mail.outbox[0].subject.lower())
