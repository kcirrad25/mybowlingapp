from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Team(models.Model):
	name = models.CharField(max_length=120, unique=True)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ["name"]

	def __str__(self) -> str:
		return self.name


class Bowler(models.Model):
	bowler_code = models.CharField(max_length=24, unique=True)
	first_name = models.CharField(max_length=60)
	last_name = models.CharField(max_length=60)
	age = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(120)])
	team = models.ForeignKey(Team, related_name="bowlers", on_delete=models.PROTECT)
	created_by = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		null=True,
		blank=True,
		on_delete=models.SET_NULL,
		related_name="created_bowlers",
	)

	class Meta:
		ordering = ["last_name", "first_name"]

	def __str__(self) -> str:
		return f"{self.first_name} {self.last_name}"


class LeagueWeek(models.Model):
	week_number = models.PositiveSmallIntegerField(
		unique=True,
		validators=[MinValueValidator(1), MaxValueValidator(20)],
	)
	week_date = models.DateField(unique=True)

	class Meta:
		ordering = ["week_number"]

	def __str__(self) -> str:
		return f"Week {self.week_number} ({self.week_date})"


class BowlerScore(models.Model):
	week = models.ForeignKey(LeagueWeek, related_name="bowler_scores", on_delete=models.CASCADE)
	bowler = models.ForeignKey(Bowler, related_name="scores", on_delete=models.CASCADE)
	game1 = models.PositiveSmallIntegerField(validators=[MinValueValidator(0), MaxValueValidator(300)])
	game2 = models.PositiveSmallIntegerField(validators=[MinValueValidator(0), MaxValueValidator(300)])
	game3 = models.PositiveSmallIntegerField(validators=[MinValueValidator(0), MaxValueValidator(300)])
	handicap = models.IntegerField(default=0)
	scratch_total = models.PositiveSmallIntegerField(default=0)
	total_with_handicap = models.PositiveSmallIntegerField(default=0)

	class Meta:
		constraints = [
			models.UniqueConstraint(fields=["week", "bowler"], name="uq_bowler_score_week_bowler"),
		]
		ordering = ["week__week_number", "bowler__last_name"]

	def save(self, *args, **kwargs):
		self.scratch_total = self.game1 + self.game2 + self.game3
		self.total_with_handicap = self.scratch_total + self.handicap
		super().save(*args, **kwargs)

	def __str__(self) -> str:
		return f"{self.bowler} - Week {self.week.week_number}"


class TeamScore(models.Model):
	week = models.ForeignKey(LeagueWeek, related_name="team_scores", on_delete=models.CASCADE)
	team = models.ForeignKey(Team, related_name="team_scores", on_delete=models.CASCADE)
	game1 = models.PositiveSmallIntegerField(validators=[MinValueValidator(0), MaxValueValidator(900)])
	game2 = models.PositiveSmallIntegerField(validators=[MinValueValidator(0), MaxValueValidator(900)])
	game3 = models.PositiveSmallIntegerField(validators=[MinValueValidator(0), MaxValueValidator(900)])
	handicap = models.IntegerField(default=0)
	scratch_total = models.PositiveSmallIntegerField(default=0)
	total_with_handicap = models.PositiveSmallIntegerField(default=0)

	class Meta:
		constraints = [
			models.UniqueConstraint(fields=["week", "team"], name="uq_team_score_week_team"),
		]
		ordering = ["week__week_number", "-total_with_handicap"]

	def save(self, *args, **kwargs):
		self.scratch_total = self.game1 + self.game2 + self.game3
		self.total_with_handicap = self.scratch_total + self.handicap
		super().save(*args, **kwargs)

	def __str__(self) -> str:
		return f"{self.team} - Week {self.week.week_number}"


class SiteBranding(models.Model):
	name = models.CharField(max_length=80, default="Default")
	logo = models.ImageField(upload_to="branding/logos/", blank=True, null=True)
	background_image = models.ImageField(upload_to="branding/backgrounds/", blank=True, null=True)
	is_active = models.BooleanField(default=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		verbose_name_plural = "Site branding"

	def __str__(self) -> str:
		return f"{self.name} ({'active' if self.is_active else 'inactive'})"


class ScoreSheetUpload(models.Model):
	class OCRStatus(models.TextChoices):
		NOT_REQUIRED = "not_required", "Not Required"
		PENDING = "pending", "Pending"
		PROCESSING = "processing", "Processing"
		COMPLETED = "completed", "Completed"
		FAILED = "failed", "Failed"

	class ParseStatus(models.TextChoices):
		PENDING = "pending", "Pending"
		PROCESSED = "processed", "Processed"
		FAILED = "failed", "Failed"

	uploaded_by = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.SET_NULL,
		null=True,
		blank=True,
		related_name="uploaded_score_sheets",
	)
	source_pdf = models.FileField(upload_to="score_sheets/")
	uploaded_at = models.DateTimeField(auto_now_add=True)
	ocr_status = models.CharField(max_length=20, choices=OCRStatus.choices, default=OCRStatus.NOT_REQUIRED)
	textract_job_id = models.CharField(max_length=120, blank=True)
	parse_status = models.CharField(max_length=20, choices=ParseStatus.choices, default=ParseStatus.PENDING)
	extracted_text = models.TextField(blank=True)
	parse_notes = models.TextField(blank=True)

	class Meta:
		ordering = ["-uploaded_at"]

	def __str__(self) -> str:
		return f"Score Sheet {self.pk} ({self.parse_status})"


class AuditLog(models.Model):
	class Action(models.TextChoices):
		CREATED = "created", "Created"
		UPDATED = "updated", "Updated"
		DELETED = "deleted", "Deleted"

	actor = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		null=True,
		blank=True,
		on_delete=models.SET_NULL,
		related_name="audit_entries",
	)
	action = models.CharField(max_length=20, choices=Action.choices)
	model_name = models.CharField(max_length=80)
	object_pk = models.CharField(max_length=50)
	object_repr = models.CharField(max_length=255)
	changed_fields = models.JSONField(default=dict, blank=True)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ["-created_at"]

	def __str__(self) -> str:
		return f"{self.model_name} {self.action} ({self.object_pk})"
