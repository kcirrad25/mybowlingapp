import base64
from io import BytesIO

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django_otp import login as otp_login
from django_otp import verify_token
from django_otp.plugins.otp_totp.models import TOTPDevice
import qrcode

from .forms import AccessRequestForm, AdminMFASetupForm, AdminMFAVerifyForm, SignUpForm, UserProfileForm
from .models import AccessRequest, UserProfile


def signup_view(request):
	if request.method == "POST":
		form = SignUpForm(request.POST)
		if form.is_valid():
			user = form.save()
			user.is_active = False
			user.save(update_fields=["is_active"])
			UserProfile.objects.get_or_create(user=user)
			AccessRequest.objects.get_or_create(
				email=user.email,
				defaults={
					"full_name": f"{user.first_name} {user.last_name}".strip() or user.username,
					"message": "Created from signup form and awaiting admin approval.",
				},
			)
			messages.success(request, "Your account request has been submitted for admin approval.")
			return redirect("accounts:login")
	else:
		form = SignUpForm()
	return render(request, "accounts/signup.html", {"form": form})


@login_required
def profile_view(request):
	profile, _ = UserProfile.objects.get_or_create(user=request.user)
	if request.method == "POST":
		form = UserProfileForm(request.POST, instance=profile)
		if form.is_valid():
			form.save()
			messages.success(request, "Profile updated.")
			return redirect("accounts:profile")
	else:
		form = UserProfileForm(instance=profile)
	return render(request, "accounts/profile.html", {"form": form})


def request_access_view(request):
	if request.method == "POST":
		form = AccessRequestForm(request.POST)
		if form.is_valid():
			form.save()
			messages.success(request, "Request submitted. An admin will contact you.")
			return redirect("accounts:request_access")
	else:
		form = AccessRequestForm()
	return render(request, "accounts/request_access.html", {"form": form})


@login_required
def admin_mfa_setup_view(request):
	if not request.user.is_staff:
		messages.error(request, "Admin MFA setup is only available to staff users.")
		return redirect("league:dashboard")

	device = TOTPDevice.objects.filter(user=request.user, name="Admin authenticator").first()
	if device and device.confirmed:
		messages.info(request, "Admin MFA is already configured for your account.")
		return redirect("accounts:admin_mfa_verify")
	if not device:
		device = TOTPDevice.objects.create(user=request.user, name="Admin authenticator", confirmed=False)

	qr = qrcode.make(device.config_url)
	buffer = BytesIO()
	qr.save(buffer, format="PNG")
	qr_code = base64.b64encode(buffer.getvalue()).decode("ascii")

	if request.method == "POST":
		form = AdminMFASetupForm(request.POST)
		if form.is_valid() and device.verify_token(form.cleaned_data["otp_token"]):
			device.confirmed = True
			device.save(update_fields=["confirmed"])
			otp_login(request, device)
			messages.success(request, "Admin MFA is now enabled for your account.")
			return redirect("/admin/")
		if form.is_bound:
			messages.error(request, "The authenticator code could not be verified.")
	else:
		form = AdminMFASetupForm()

	context = {
		"form": form,
		"device": device,
		"qr_code": qr_code,
	}
	return render(request, "accounts/admin_mfa_setup.html", context)


@login_required
def admin_mfa_verify_view(request):
	if not request.user.is_staff:
		messages.error(request, "Admin MFA verification is only available to staff users.")
		return redirect("league:dashboard")
	if not TOTPDevice.objects.filter(user=request.user, confirmed=True).exists():
		messages.info(request, "Set up an authenticator app before verifying admin MFA.")
		return redirect("accounts:admin_mfa_setup")

	if request.method == "POST":
		form = AdminMFAVerifyForm(request.POST, user=request.user)
		if form.is_valid():
			device = verify_token(
				request.user,
				form.cleaned_data["otp_device"],
				form.cleaned_data["otp_token"],
			)
			if device:
				otp_login(request, device)
				messages.success(request, "Admin MFA verification complete.")
				return redirect("/admin/")
			messages.error(request, "The authenticator code could not be verified.")
	else:
		form = AdminMFAVerifyForm(user=request.user)

	return render(request, "accounts/admin_mfa_verify.html", {"form": form})
