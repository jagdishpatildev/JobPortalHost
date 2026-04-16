from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, Job, Application, Resume
from .models import ResumeBuilder

class ResumeBuilderForm(forms.ModelForm):
    class Meta:
        model  = ResumeBuilder
        exclude = ('user',)
        widgets = {
            'summary':    forms.Textarea(attrs={'rows': 3, 'placeholder': 'Brief professional summary...'}),
            'skills':     forms.TextInput(attrs={'placeholder': 'Python, Django, React, SQL...'}),
            'experience': forms.Textarea(attrs={'rows': 5, 'placeholder': '''[
  {"company": "TechCorp", "role": "Developer", "duration": "2022-2024", "description": "Built APIs"}
]'''}),
            'education':  forms.Textarea(attrs={'rows': 3, 'placeholder': '''[
  {"institution": "MIT", "degree": "B.Tech CS", "year": "2022"}
]'''}),
        }
class RegisterForm(UserCreationForm):
    role = forms.ChoiceField(
        choices=(('seeker', 'Job Seeker'), ('employer', 'Employer')),
        widget=forms.RadioSelect
    )
    class Meta:
        model  = User
        fields = ['username', 'email', 'first_name', 'last_name', 'role', 'password1', 'password2']

class JobForm(forms.ModelForm):
    class Meta:
        model  = Job
        fields = ['title', 'company', 'category', 'location', 'job_type', 'description', 'requirements', 'salary', 'status']
        widgets = {
            'description':  forms.Textarea(attrs={'rows': 5}),
            'requirements': forms.Textarea(attrs={'rows': 5}),
        }

class ApplicationForm(forms.ModelForm):
    class Meta:
        model  = Application
        fields = ['resume', 'cover_letter']
        widgets = {
            'cover_letter': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Why are you a great fit?'})
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user:
            self.fields['resume'].queryset = Resume.objects.filter(user=user)

class ResumeUploadForm(forms.ModelForm):
    class Meta:
        model  = Resume
        fields = ['title', 'file']