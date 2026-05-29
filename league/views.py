from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Sum
from django.shortcuts import get_object_or_404, redirect, render

from .forms import BowlerForm, ScoreSheetUploadForm
from .models import Bowler, ScoreSheetUpload, Team
from .services import extract_text_from_pdf, parse_scores_text, poll_textract_job, start_textract_job


@login_required
def dashboard_view(request):
	rankings = Team.objects.annotate(
		season_total=Sum("team_scores__total_with_handicap"),
		season_scratch=Sum("team_scores__scratch_total"),
	).order_by("-season_total", "name")

	trend_series = []
	max_total = max((team.season_total or 0 for team in rankings), default=1)
	for team in rankings[:4]:
		weekly_scores = list(team.team_scores.select_related("week").order_by("week__week_number"))
		if not weekly_scores:
			continue
		points = []
		for index, score in enumerate(weekly_scores):
			x = 20 + index * 65
			y = 180 - int(((score.total_with_handicap or 0) / max_total) * 150)
			points.append(f"{x},{y}")
		trend_series.append({"team": team, "points": " ".join(points)})

	top_bowlers = Bowler.objects.annotate(avg_total=Avg("scores__total_with_handicap")).order_by("-avg_total", "last_name")[:8]
	context = {
		"rankings": rankings,
		"trend_series": trend_series,
		"top_bowlers": top_bowlers,
	}
	return render(request, "league/dashboard.html", context)


@login_required
def team_detail_view(request, team_id):
	team = get_object_or_404(Team.objects.prefetch_related("bowlers", "team_scores__week"), pk=team_id)
	return render(request, "league/team_detail.html", {"team": team})


@login_required
def bowler_detail_view(request, bowler_id):
	bowler = get_object_or_404(Bowler.objects.select_related("team"), pk=bowler_id)
	scores = bowler.scores.select_related("week").order_by("week__week_number")
	return render(request, "league/bowler_detail.html", {"bowler": bowler, "scores": scores})


@login_required
def add_bowler_view(request):
	if request.method == "POST":
		form = BowlerForm(request.POST)
		if form.is_valid():
			bowler = form.save(commit=False)
			bowler.created_by = request.user
			bowler.save()
			messages.success(request, "Bowler added successfully.")
			return redirect("league:team_detail", team_id=bowler.team_id)
	else:
		form = BowlerForm()
	return render(request, "league/add_bowler.html", {"form": form})


@staff_member_required
def upload_scoresheet_view(request):
	if request.method == "POST":
		form = ScoreSheetUploadForm(request.POST, request.FILES)
		if form.is_valid():
			upload = form.save(commit=False)
			upload.uploaded_by = request.user
			upload.save()

			try:
				pdf_bytes = upload.source_pdf.read()
				upload.extracted_text = extract_text_from_pdf(pdf_bytes)
				if upload.extracted_text.strip():
					result = parse_scores_text(upload.extracted_text)
					upload.ocr_status = upload.OCRStatus.NOT_REQUIRED
					upload.parse_status = upload.ParseStatus.PROCESSED
					upload.parse_notes = (
						f"Created bowler scores: {result.created_bowler_scores}, "
						f"updated bowler scores: {result.updated_bowler_scores}, "
						f"created team scores: {result.created_team_scores}, "
						f"updated team scores: {result.updated_team_scores}"
					)
					upload.save(update_fields=["extracted_text", "ocr_status", "parse_status", "parse_notes"])
					messages.success(request, "PDF imported successfully.")
				else:
					upload.ocr_status = upload.OCRStatus.PENDING
					upload.parse_notes = "No extractable text found. OCR has been requested."
					upload.textract_job_id = start_textract_job(upload)
					upload.ocr_status = upload.OCRStatus.PROCESSING
					upload.save(update_fields=["extracted_text", "ocr_status", "parse_notes", "textract_job_id"])
					messages.success(request, "PDF uploaded. OCR processing was started with AWS Textract.")
			except Exception as exc:
				upload.parse_status = upload.ParseStatus.FAILED
				upload.ocr_status = upload.OCRStatus.FAILED
				upload.parse_notes = str(exc)
				upload.save(update_fields=["parse_status", "ocr_status", "parse_notes"])
				messages.error(
					request,
					"PDF uploaded but parsing failed. Check Parse Notes in admin for details.",
				)
			return redirect("league:upload_scoresheet")
	else:
		form = ScoreSheetUploadForm()

	return render(request, "league/upload_scoresheet.html", {"form": form})


@staff_member_required
def process_textract_view(request, upload_id):
	upload = get_object_or_404(ScoreSheetUpload, pk=upload_id)
	status, extracted_text = poll_textract_job(upload)
	if status == "SUCCEEDED":
		upload.extracted_text = extracted_text
		result = parse_scores_text(extracted_text)
		upload.ocr_status = upload.OCRStatus.COMPLETED
		upload.parse_status = upload.ParseStatus.PROCESSED
		upload.parse_notes = (
			f"Textract OCR complete. Created bowler scores: {result.created_bowler_scores}, "
			f"updated bowler scores: {result.updated_bowler_scores}, "
			f"created team scores: {result.created_team_scores}, "
			f"updated team scores: {result.updated_team_scores}"
		)
		upload.save(update_fields=["extracted_text", "ocr_status", "parse_status", "parse_notes"])
		messages.success(request, "Textract OCR output processed successfully.")
	elif status == "IN_PROGRESS":
		messages.info(request, "Textract OCR is still processing.")
	else:
		upload.ocr_status = upload.OCRStatus.FAILED
		upload.parse_status = upload.ParseStatus.FAILED
		upload.parse_notes = f"Textract OCR returned status: {status}"
		upload.save(update_fields=["ocr_status", "parse_status", "parse_notes"])
		messages.error(request, "Textract OCR did not complete successfully.")
	return redirect("league:upload_scoresheet")
