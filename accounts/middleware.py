from django.conf import settings
from django.http import HttpResponseForbidden
from django.shortcuts import redirect
from django.utils.deprecation import MiddlewareMixin
from django_otp import user_has_device


class AdminSecurityMiddleware(MiddlewareMixin):
    def process_request(self, request):
        if not request.path.startswith("/admin"):
            return None

        client_ip = self._get_client_ip(request)
        if settings.ADMIN_ALLOWED_IPS and client_ip not in settings.ADMIN_ALLOWED_IPS:
            return HttpResponseForbidden("Admin access is restricted to approved network addresses.")

        if not request.user.is_authenticated or not request.user.is_staff:
            return None

        if request.path.startswith(settings.OTP_ADMIN_SETUP_URL) or request.path.startswith(settings.OTP_ADMIN_VERIFY_URL):
            return None

        if request.path.startswith("/admin/logout"):
            return None

        is_verified = getattr(request.user, "is_verified", lambda: False)()
        if is_verified:
            return None

        if user_has_device(request.user):
            return redirect("accounts:admin_mfa_verify")
        return redirect("accounts:admin_mfa_setup")

    def _get_client_ip(self, request):
        if settings.TRUST_X_FORWARDED_FOR:
            forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR", "")
            if forwarded_for:
                return forwarded_for.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR", "")
