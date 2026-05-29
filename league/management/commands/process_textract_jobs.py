from django.core.management.base import BaseCommand

from league.models import ScoreSheetUpload
from league.services import parse_scores_text, poll_textract_job


class Command(BaseCommand):
    help = "Poll pending Textract OCR jobs and import extracted score data when ready."

    def handle(self, *args, **options):
        uploads = ScoreSheetUpload.objects.exclude(textract_job_id="").filter(ocr_status=ScoreSheetUpload.OCRStatus.PROCESSING)
        for upload in uploads:
            status, extracted_text = poll_textract_job(upload)
            if status == "SUCCEEDED":
                result = parse_scores_text(extracted_text)
                upload.extracted_text = extracted_text
                upload.ocr_status = upload.OCRStatus.COMPLETED
                upload.parse_status = upload.ParseStatus.PROCESSED
                upload.parse_notes = (
                    f"Textract OCR complete. Created bowler scores: {result.created_bowler_scores}, "
                    f"updated bowler scores: {result.updated_bowler_scores}, "
                    f"created team scores: {result.created_team_scores}, "
                    f"updated team scores: {result.updated_team_scores}"
                )
                upload.save(update_fields=["extracted_text", "ocr_status", "parse_status", "parse_notes"])
                self.stdout.write(self.style.SUCCESS(f"Processed upload {upload.pk}"))
            elif status == "IN_PROGRESS":
                self.stdout.write(f"Upload {upload.pk} still processing")
            else:
                upload.ocr_status = upload.OCRStatus.FAILED
                upload.parse_status = upload.ParseStatus.FAILED
                upload.parse_notes = f"Textract OCR returned status: {status}"
                upload.save(update_fields=["ocr_status", "parse_status", "parse_notes"])
                self.stdout.write(self.style.WARNING(f"Upload {upload.pk} failed with status {status}"))
