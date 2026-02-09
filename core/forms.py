from django import forms

from core.models import TestRun


class TestRunForm(forms.ModelForm):
    class Meta:
        model = TestRun
        fields = [
            'specimen',
            'binder_grade',
            'file_type',
            'allowed_rut_depth',
            'notes',
            'file',
        ]
        widgets = {
            'file': forms.ClearableFileInput(attrs={'accept': '.csv'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }
