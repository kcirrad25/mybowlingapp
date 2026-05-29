from django.contrib import admin
from django.utils import timezone

from .models import AccessRequest, UserProfile


@admin.action(description="Approve selected user profiles")
def approve_user_profiles(modeladmin, request, queryset):
	approved_at = timezone.now()
	for profile in queryset.select_related("user"):
		profile.is_approved = True
		profile.approved_at = approved_at
		profile.approved_by = request.user
		profile.user.is_active = True
		profile.user.save(update_fields=["is_active"])
		profile.save(update_fields=["is_approved", "approved_at", "approved_by"])
		AccessRequest.objects.filter(email=profile.user.email).update(status=AccessRequest.Status.APPROVED)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
	list_display = ("user", "display_name", "favorite_team", "is_league_admin", "is_approved", "approved_at", "approved_by")
	list_filter = ("is_league_admin", "is_approved")
	search_fields = ("user__username", "display_name")
	actions = (approve_user_profiles,)


@admin.register(AccessRequest)
class AccessRequestAdmin(admin.ModelAdmin):
	list_display = ("full_name", "email", "status", "created_at")
	list_filter = ("status", "created_at")
	search_fields = ("full_name", "email")
