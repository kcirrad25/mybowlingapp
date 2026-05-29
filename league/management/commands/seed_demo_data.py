from datetime import date, timedelta
from random import Random

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from accounts.models import UserProfile
from league.models import Bowler, BowlerScore, LeagueWeek, Team, TeamScore


class Command(BaseCommand):
    help = "Seed demo teams, bowlers, weeks, and scores for local exploration."

    def handle(self, *args, **options):
        rng = Random(42)
        teams = []
        team_names = ["Pin Pioneers", "Strike Force", "Lucky Frames", "Split Happens"]

        demo_admin, created = User.objects.get_or_create(
            username="leagueadmin",
            defaults={"email": "admin@example.com", "is_staff": True, "is_superuser": True, "is_active": True},
        )
        if created:
            demo_admin.set_password("ChangeMe123!")
            demo_admin.save()
        UserProfile.objects.get_or_create(user=demo_admin, defaults={"display_name": "League Admin", "is_league_admin": True, "is_approved": True})

        for team_name in team_names:
            team, _ = Team.objects.get_or_create(name=team_name)
            teams.append(team)

        for index, team in enumerate(teams, start=1):
            for slot in range(1, 4):
                Bowler.objects.get_or_create(
                    bowler_code=f"T{index}B{slot}",
                    defaults={
                        "first_name": f"Bowler{index}{slot}",
                        "last_name": team.name.split()[0],
                        "age": 20 + index + slot,
                        "team": team,
                    },
                )

        start_date = date(2026, 1, 7)
        for week_number in range(1, 21):
            week, _ = LeagueWeek.objects.get_or_create(
                week_number=week_number,
                defaults={"week_date": start_date + timedelta(days=(week_number - 1) * 7)},
            )
            for team in teams:
                bowlers = list(team.bowlers.all())
                team_games = [0, 0, 0]
                team_handicap = 0
                for bowler in bowlers:
                    g1 = rng.randint(110, 220)
                    g2 = rng.randint(110, 220)
                    g3 = rng.randint(110, 220)
                    handicap = rng.randint(15, 60)
                    BowlerScore.objects.update_or_create(
                        week=week,
                        bowler=bowler,
                        defaults={"game1": g1, "game2": g2, "game3": g3, "handicap": handicap},
                    )
                    team_games[0] += g1
                    team_games[1] += g2
                    team_games[2] += g3
                    team_handicap += handicap
                TeamScore.objects.update_or_create(
                    week=week,
                    team=team,
                    defaults={
                        "game1": team_games[0],
                        "game2": team_games[1],
                        "game3": team_games[2],
                        "handicap": team_handicap,
                    },
                )

        self.stdout.write(self.style.SUCCESS("Demo data seeded. Login with leagueadmin / ChangeMe123! and approve users as needed."))
