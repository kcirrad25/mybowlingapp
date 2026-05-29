from django import forms

from .models import Bowler, ScoreSheetUpload


class BowlerForm(forms.ModelForm):
    class Meta:
        model = Bowler
        fields = ("bowler_code", "first_name", "last_name", "age", "team")


class ScoreSheetUploadForm(forms.ModelForm):
    class Meta:
        model = ScoreSheetUpload
        fields = ("source_pdf",)
