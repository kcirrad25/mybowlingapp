from django.urls import path

from .views import (
    add_bowler_view,
    bowler_detail_view,
    dashboard_view,
    process_textract_view,
    team_detail_view,
    upload_scoresheet_view,
)

app_name = "league"

urlpatterns = [
    path("", dashboard_view, name="dashboard"),
    path("teams/<int:team_id>/", team_detail_view, name="team_detail"),
    path("bowlers/<int:bowler_id>/", bowler_detail_view, name="bowler_detail"),
    path("bowlers/add/", add_bowler_view, name="add_bowler"),
    path("admin/upload-scoresheet/", upload_scoresheet_view, name="upload_scoresheet"),
    path("admin/upload-scoresheet/<int:upload_id>/process-ocr/", process_textract_view, name="process_textract"),
]
