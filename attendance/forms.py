from django import forms
from .models import Grade, Student

class GradeForm(forms.ModelForm):
    class Meta:
        model = Grade
        fields = ['student', 'subject', 'exam_type', 'marks']
