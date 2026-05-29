from django.contrib import admin

from .models import AuditLog, Bowler, BowlerScore, LeagueWeek, ScoreSheetUpload, SiteBranding, Team, TeamScore


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
	list_display = ("name", "created_at")
	search_fields = ("name",)


@admin.register(Bowler)
class BowlerAdmin(admin.ModelAdmin):
	list_display = ("bowler_code", "first_name", "last_name", "team", "age")
	list_filter = ("team",)
	search_fields = ("bowler_code", "first_name", "last_name")


@admin.register(LeagueWeek)
class LeagueWeekAdmin(admin.ModelAdmin):
	list_display = ("week_number", "week_date")
	ordering = ("week_number",)


@admin.register(BowlerScore)
class BowlerScoreAdmin(admin.ModelAdmin):
	list_display = (
		"week",
		"bowler",
		"game1",
		"game2",
		"game3",
		"handicap",
		"scratch_total",
		"total_with_handicap",
	)
	list_filter = ("week", "bowler__team")
	search_fields = ("bowler__first_name", "bowler__last_name", "bowler__bowler_code")


@admin.register(TeamScore)
class TeamScoreAdmin(admin.ModelAdmin):
	list_display = (
		"week",
		"team",
		"game1",
		"game2",
		"game3",
		"handicap",
		"scratch_total",
		"total_with_handicap",
	)
	list_filter = ("week", "team")
	search_fields = ("team__name",)


@admin.register(SiteBranding)
class SiteBrandingAdmin(admin.ModelAdmin):
	list_display = ("name", "is_active", "updated_at")
	list_filter = ("is_active",)


@admin.register(ScoreSheetUpload)
class ScoreSheetUploadAdmin(admin.ModelAdmin):
	list_display = ("id", "uploaded_by", "ocr_status", "parse_status", "uploaded_at")
	list_filter = ("ocr_status", "parse_status", "uploaded_at")


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
	list_display = ("created_at", "actor", "action", "model_name", "object_pk")
	list_filter = ("action", "model_name", "created_at")
	search_fields = ("object_pk", "object_repr", "actor__username")
	readonly_fields = ("created_at", "actor", "action", "model_name", "object_pk", "object_repr", "changed_fields")
