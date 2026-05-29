from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory, TestCase, override_settings
from django.urls import reverse
from unittest.mock import patch

from .middleware import AdminSecurityMiddleware

User = get_user_model()


class AdminSecurityMiddlewareTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.middleware = AdminSecurityMiddleware(lambda request: None)

    @override_settings(TRUST_X_FORWARDED_FOR=True)
    def test_get_client_ip_uses_x_forwarded_for_when_trusted(self):
        request = self.factory.get("/admin/", HTTP_X_FORWARDED_FOR="203.0.113.5, 198.51.100.7")
        request.user = AnonymousUser()

        self.assertEqual(self.middleware._get_client_ip(request), "203.0.113.5")

    @override_settings(ADMIN_ALLOWED_IPS=["10.0.0.1"], TRUST_X_FORWARDED_FOR=False)
    def test_process_request_forbidden_for_unapproved_ip(self):
        request = self.factory.get("/admin/")
        request.META["REMOTE_ADDR"] = "10.0.0.2"
        request.user = AnonymousUser()

        response = self.middleware.process_request(request)

        self.assertEqual(response.status_code, 403)
        self.assertIn("Admin access is restricted", response.content.decode())

    @override_settings(ADMIN_ALLOWED_IPS=["127.0.0.1"], TRUST_X_FORWARDED_FOR=False)
    @patch("accounts.middleware.user_has_device", return_value=True)
    def test_process_request_redirects_to_verify_when_device_registered(self, mocked_user_has_device):
        user = User.objects.create_user(username="staff", password="secret")
        user.is_staff = True
        user.save()
        user.is_verified = lambda: False

        request = self.factory.get("/admin/")
        request.META["REMOTE_ADDR"] = "127.0.0.1"
        request.user = user

        response = self.middleware.process_request(request)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("accounts:admin_mfa_verify"))

    @override_settings(ADMIN_ALLOWED_IPS=["127.0.0.1"], TRUST_X_FORWARDED_FOR=False)
    @patch("accounts.middleware.user_has_device", return_value=False)
    def test_process_request_redirects_to_setup_when_no_device(self, mocked_user_has_device):
        user = User.objects.create_user(username="staff2", password="secret")
        user.is_staff = True
        user.save()
        user.is_verified = lambda: False

        request = self.factory.get("/admin/")
        request.META["REMOTE_ADDR"] = "127.0.0.1"
        request.user = user

        response = self.middleware.process_request(request)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("accounts:admin_mfa_setup"))

    @override_settings(ADMIN_ALLOWED_IPS=["127.0.0.1"], TRUST_X_FORWARDED_FOR=False)
    @patch("accounts.middleware.user_has_device", return_value=True)
    def test_process_request_returns_none_for_verified_staff_user(self, mocked_user_has_device):
        user = User.objects.create_user(username="staff3", password="secret")
        user.is_staff = True
        user.save()
        user.is_verified = lambda: True

        request = self.factory.get("/admin/")
        request.META["REMOTE_ADDR"] = "127.0.0.1"
        request.user = user

        response = self.middleware.process_request(request)

        self.assertIsNone(response)
