from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from league.services import parse_scores_text


class Command(BaseCommand):
    help = "Import score rows from a text file extracted from score sheets."

    def add_arguments(self, parser):
        parser.add_argument("source", type=str, help="Path to text file containing score lines")

    def handle(self, *args, **options):
        source = Path(options["source"])
        if not source.exists():
            raise CommandError(f"Source file not found: {source}")

        raw_text = source.read_text(encoding="utf-8")
        result = parse_scores_text(raw_text)
        self.stdout.write(self.style.SUCCESS("Score import completed."))
        self.stdout.write(
            f"Created bowler scores: {result.created_bowler_scores}; "
            f"updated bowler scores: {result.updated_bowler_scores}; "
            f"created team scores: {result.created_team_scores}; "
            f"updated team scores: {result.updated_team_scores}"
        )
