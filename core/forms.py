from django import forms

from core.models import TestRun, BinderGrade


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


class BinderGradeForm(forms.ModelForm):
    class Meta:
        model = BinderGrade
        fields = ['name', 'max_rut', 'passes_to_rut']
