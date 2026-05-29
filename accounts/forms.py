from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django_otp import devices_for_user

from .models import AccessRequest, UserProfile


class SignUpForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=60, required=False)
    last_name = forms.CharField(max_length=60, required=False)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email", "first_name", "last_name", "password1", "password2")


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ("display_name", "favorite_team")


class AccessRequestForm(forms.ModelForm):
    class Meta:
        model = AccessRequest
        fields = ("full_name", "email", "message")


class AdminMFASetupForm(forms.Form):
    otp_token = forms.CharField(max_length=12, label="Authenticator code")


class AdminMFAVerifyForm(forms.Form):
    otp_device = forms.ChoiceField(label="Authenticator device")
    otp_token = forms.CharField(max_length=12, label="Authenticator code")

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        self.fields["otp_device"].choices = [
            (device.persistent_id, device.name) for device in devices_for_user(user)
        ]
