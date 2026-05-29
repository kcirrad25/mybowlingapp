from django.conf import settings
from django.db import models


class UserProfile(models.Model):
	user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
	display_name = models.CharField(max_length=120, blank=True)
	favorite_team = models.ForeignKey(
		"league.Team",
		null=True,
		blank=True,
		on_delete=models.SET_NULL,
		related_name="fans",
	)
	is_league_admin = models.BooleanField(default=False)
	is_approved = models.BooleanField(default=False)
	approved_at = models.DateTimeField(null=True, blank=True)
	approved_by = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		null=True,
		blank=True,
		on_delete=models.SET_NULL,
		related_name="approved_user_profiles",
	)

	def __str__(self) -> str:
		return self.display_name or self.user.get_username()


class AccessRequest(models.Model):
	class Status(models.TextChoices):
		NEW = "new", "New"
		REVIEWED = "reviewed", "Reviewed"
		APPROVED = "approved", "Approved"
		REJECTED = "rejected", "Rejected"

	full_name = models.CharField(max_length=120)
	email = models.EmailField()
	message = models.TextField(blank=True)
	status = models.CharField(max_length=20, choices=Status.choices, default=Status.NEW)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ["-created_at"]

	def __str__(self) -> str:
		return f"{self.full_name} ({self.email})"
