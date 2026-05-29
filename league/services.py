from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from io import BytesIO

import boto3
from django.conf import settings
from pypdf import PdfReader

from .models import Bowler, BowlerScore, LeagueWeek, ScoreSheetUpload, Team, TeamScore


@dataclass
class ImportResult:
    created_bowler_scores: int = 0
    created_team_scores: int = 0
    updated_bowler_scores: int = 0
    updated_team_scores: int = 0


# Expected line format example:
# WEEK,1,2026-01-10
# BOWLER,B001,120,140,130,45
# TEAM,Team A,540,520,500,100
def parse_scores_text(raw_text: str) -> ImportResult:
    current_week = None
    result = ImportResult()

    for line in (line.strip() for line in raw_text.splitlines()):
        if not line:
            continue
        parts = [part.strip() for part in line.split(",")]
        tag = parts[0].upper()

        if tag == "WEEK" and len(parts) >= 3:
            week_number = int(parts[1])
            week_date = date.fromisoformat(parts[2])
            current_week, _ = LeagueWeek.objects.get_or_create(
                week_number=week_number,
                defaults={"week_date": week_date},
            )
            if current_week.week_date != week_date:
                current_week.week_date = week_date
                current_week.save(update_fields=["week_date"])
        elif tag == "BOWLER" and len(parts) >= 6 and current_week:
            bowler = Bowler.objects.get(bowler_code=parts[1])
            obj, created = BowlerScore.objects.get_or_create(
                week=current_week,
                bowler=bowler,
                defaults={
                    "game1": int(parts[2]),
                    "game2": int(parts[3]),
                    "game3": int(parts[4]),
                    "handicap": int(parts[5]),
                },
            )
            if created:
                result.created_bowler_scores += 1
            else:
                obj.game1 = int(parts[2])
                obj.game2 = int(parts[3])
                obj.game3 = int(parts[4])
                obj.handicap = int(parts[5])
                obj.save()
                result.updated_bowler_scores += 1
        elif tag == "TEAM" and len(parts) >= 6 and current_week:
            team = Team.objects.get(name=parts[1])
            obj, created = TeamScore.objects.get_or_create(
                week=current_week,
                team=team,
                defaults={
                    "game1": int(parts[2]),
                    "game2": int(parts[3]),
                    "game3": int(parts[4]),
                    "handicap": int(parts[5]),
                },
            )
            if created:
                result.created_team_scores += 1
            else:
                obj.game1 = int(parts[2])
                obj.game2 = int(parts[3])
                obj.game3 = int(parts[4])
                obj.handicap = int(parts[5])
                obj.save()
                result.updated_team_scores += 1

    return result


def extract_text_from_pdf(content: bytes) -> str:
    reader = PdfReader(BytesIO(content))
    extracted = []
    for page in reader.pages:
        extracted.append(page.extract_text() or "")
    return "\n".join(extracted)


def start_textract_job(upload: ScoreSheetUpload) -> str:
    if not settings.AWS_TEXTRACT_ENABLED or not settings.AWS_STORAGE_BUCKET_NAME:
        raise RuntimeError("AWS Textract OCR is not configured.")

    client = boto3.client("textract", region_name=settings.AWS_S3_REGION_NAME or None)
    request = {
        "DocumentLocation": {
            "S3Object": {
                "Bucket": settings.AWS_STORAGE_BUCKET_NAME,
                "Name": upload.source_pdf.name,
            }
        }
    }
    if settings.AWS_TEXTRACT_SNS_TOPIC_ARN and settings.AWS_TEXTRACT_ROLE_ARN:
        request["NotificationChannel"] = {
            "SNSTopicArn": settings.AWS_TEXTRACT_SNS_TOPIC_ARN,
            "RoleArn": settings.AWS_TEXTRACT_ROLE_ARN,
        }

    response = client.start_document_text_detection(**request)
    return response["JobId"]


def poll_textract_job(upload: ScoreSheetUpload) -> tuple[str, str]:
    if not upload.textract_job_id:
        raise RuntimeError("No Textract job ID is stored for this upload.")

    client = boto3.client("textract", region_name=settings.AWS_S3_REGION_NAME or None)
    next_token = None
    lines = []
    status = "IN_PROGRESS"

    while True:
        kwargs = {"JobId": upload.textract_job_id}
        if next_token:
            kwargs["NextToken"] = next_token
        response = client.get_document_text_detection(**kwargs)
        status = response["JobStatus"]
        if status != "SUCCEEDED":
            break

        for block in response.get("Blocks", []):
            if block.get("BlockType") == "LINE" and block.get("Text"):
                lines.append(block["Text"])
        next_token = response.get("NextToken")
        if not next_token:
            break

    return status, "\n".join(lines)
