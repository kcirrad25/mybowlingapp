from datetime import date
from unittest.mock import MagicMock, patch

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings

from .models import Bowler, BowlerScore, LeagueWeek, ScoreSheetUpload, Team, TeamScore
from .services import ImportResult, parse_scores_text, poll_textract_job, start_textract_job

User = get_user_model()


class LeagueServicesTests(TestCase):
    def setUp(self):
        self.team = Team.objects.create(name="Team A")
        self.bowler = Bowler.objects.create(
            bowler_code="B001",
            first_name="Jane",
            last_name="Doe",
            age=30,
            team=self.team,
        )

    def test_parse_scores_text_creates_scores_and_updates_totals(self):
        raw_text = (
            "WEEK,1,2026-01-10\n"
            "BOWLER,B001,120,140,130,45\n"
            "TEAM,Team A,540,520,500,100"
        )

        result = parse_scores_text(raw_text)

        self.assertEqual(result, ImportResult(created_bowler_scores=1, created_team_scores=1))
        self.assertTrue(LeagueWeek.objects.filter(week_number=1).exists())
        self.assertTrue(BowlerScore.objects.filter(bowler=self.bowler).exists())
        self.assertTrue(TeamScore.objects.filter(team=self.team).exists())

        bowler_score = BowlerScore.objects.get(bowler=self.bowler)
        self.assertEqual(bowler_score.scratch_total, 390)
        self.assertEqual(bowler_score.total_with_handicap, 435)

        team_score = TeamScore.objects.get(team=self.team)
        self.assertEqual(team_score.scratch_total, 1560)
        self.assertEqual(team_score.total_with_handicap, 1660)

    def test_parse_scores_text_updates_existing_scores_and_week_date(self):
        raw_text = (
            "WEEK,1,2026-01-10\n"
            "BOWLER,B001,120,140,130,45\n"
            "TEAM,Team A,540,520,500,100"
        )
        parse_scores_text(raw_text)

        updated_text = (
            "WEEK,1,2026-01-17\n"
            "BOWLER,B001,150,160,170,30\n"
            "TEAM,Team A,600,610,620,80"
        )
        result = parse_scores_text(updated_text)

        self.assertEqual(result.updated_bowler_scores, 1)
        self.assertEqual(result.updated_team_scores, 1)
        week = LeagueWeek.objects.get(week_number=1)
        self.assertEqual(week.week_date, date(2026, 1, 17))

        bowler_score = BowlerScore.objects.get(bowler=self.bowler)
        self.assertEqual(bowler_score.scratch_total, 480)
        self.assertEqual(bowler_score.total_with_handicap, 510)

    @override_settings(
        AWS_TEXTRACT_ENABLED=True,
        AWS_STORAGE_BUCKET_NAME="bucket-name",
        AWS_TEXTRACT_SNS_TOPIC_ARN="arn:aws:sns:us-east-1:123456789012:topic",
        AWS_TEXTRACT_ROLE_ARN="arn:aws:iam::123456789012:role/textract-role",
    )
    @patch("league.services.boto3.client")
    def test_start_textract_job_returns_job_id_with_notification_channel(self, mock_boto_client):
        upload = ScoreSheetUpload.objects.create(
            source_pdf=SimpleUploadedFile("test.pdf", b"%PDF-1.4 test content", content_type="application/pdf"),
        )
        mock_client = MagicMock()
        mock_client.start_document_text_detection.return_value = {"JobId": "job-123"}
        mock_boto_client.return_value = mock_client

        job_id = start_textract_job(upload)

        self.assertEqual(job_id, "job-123")
        mock_client.start_document_text_detection.assert_called_once()
        request_args = mock_client.start_document_text_detection.call_args.kwargs
        self.assertEqual(request_args["DocumentLocation"]["S3Object"]["Bucket"], "bucket-name")
        self.assertEqual(request_args["DocumentLocation"]["S3Object"]["Name"], upload.source_pdf.name)
        self.assertIn("NotificationChannel", request_args)

    @override_settings(AWS_TEXTRACT_ENABLED=False, AWS_STORAGE_BUCKET_NAME="")
    def test_start_textract_job_raises_when_not_configured(self):
        upload = ScoreSheetUpload.objects.create(
            source_pdf=SimpleUploadedFile("test.pdf", b"%PDF-1.4 test content", content_type="application/pdf"),
        )

        with self.assertRaises(RuntimeError):
            start_textract_job(upload)

    def test_poll_textract_job_raises_without_job_id(self):
        upload = ScoreSheetUpload.objects.create(
            source_pdf=SimpleUploadedFile("test.pdf", b"%PDF-1.4 test content", content_type="application/pdf"),
        )

        with self.assertRaises(RuntimeError):
            poll_textract_job(upload)

    @patch("league.services.boto3.client")
    def test_poll_textract_job_collects_lines_and_handles_pagination(self, mock_boto_client):
        upload = ScoreSheetUpload.objects.create(
            source_pdf=SimpleUploadedFile("test.pdf", b"%PDF-1.4 test content", content_type="application/pdf"),
            textract_job_id="job-123",
        )
        mock_client = MagicMock()
        mock_client.get_document_text_detection.side_effect = [
            {
                "JobStatus": "SUCCEEDED",
                "Blocks": [{"BlockType": "LINE", "Text": "Line 1"}],
                "NextToken": "token",
            },
            {
                "JobStatus": "SUCCEEDED",
                "Blocks": [{"BlockType": "LINE", "Text": "Line 2"}],
            },
        ]
        mock_boto_client.return_value = mock_client

        status, text = poll_textract_job(upload)

        self.assertEqual(status, "SUCCEEDED")
        self.assertEqual(text, "Line 1\nLine 2")
        self.assertEqual(mock_client.get_document_text_detection.call_count, 2)
