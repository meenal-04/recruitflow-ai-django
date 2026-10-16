from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

from .models import (
    Candidate,
    Job,
    Interview,
    InterviewFeedback,
)


class CandidateProfileForm(forms.ModelForm):
    class Meta:
        model = Candidate
        fields = [
            "profile_picture",
            "phone",
            "skills",
            "experience",
            "resume",
        ]


class JobForm(forms.ModelForm):
    class Meta:
        model = Job
        fields = [
            "title",
            "description",
            "required_skills",
            "experience_required",
            "location",
            "status",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 5}),
            "required_skills": forms.TextInput(
                attrs={"placeholder": "Python, Django, SQL, Git"}
            ),
        }


class InterviewForm(forms.ModelForm):
    class Meta:
        model = Interview
        fields = [
            "scheduled_at",
            "mode",
            "meeting_link",
        ]
        widgets = {
            "scheduled_at": forms.DateTimeInput(
                attrs={
                    "type": "datetime-local",
                    "class": "form-control",
                }
            ),
            "mode": forms.Select(attrs={"class": "form-select"}),
            "meeting_link": forms.URLInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "https://meet.google.com/...",
                }
            ),
        }


class InterviewFeedbackForm(forms.ModelForm):
    class Meta:
        model = InterviewFeedback
        fields = [
            "strengths",
            "areas_to_explore",
            "technical_feedback",
            "overall_feedback",
            "recommendation",
        ]
        widgets = {
            "recommendation": forms.TextInput(
                attrs={
                    "placeholder": "Further Review / Positive / Not Recommended"
                }
            )
        }


class RegistrationForm(forms.Form):

    ROLE_CHOICES = [
        ("Candidate", "Candidate"),
        ("Recruiter", "Recruiter"),
        ("Interviewer", "Interviewer"),
    ]

    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Choose a username",
            }
        ),
    )

    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(
            attrs={
                "class": "form-control",
                "placeholder": "Enter your email",
            }
        ),
    )

    password = forms.CharField(
        min_length=6,
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Create a password",
            }
        ),
    )

    confirm_password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Confirm your password",
            }
        ),
    )

    role = forms.ChoiceField(
        choices=ROLE_CHOICES,
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    phone = forms.CharField(
        max_length=15,
        required=True,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Phone number",
            }
        ),
    )

    company = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Company name",
            }
        ),
    )

    # ---------- validators ----------

    def clean_phone(self):
        phone = (self.cleaned_data.get("phone") or "").strip()
        if not phone.isdigit():
            raise ValidationError("Phone number must contain only digits.")
        if len(phone) != 10:
            raise ValidationError("Enter a valid 10-digit phone number.")
        return phone

    def clean_username(self):
        username = self.cleaned_data["username"]
        if User.objects.filter(username=username).exists():
            raise ValidationError(
                "This username is already taken. Please choose another."
            )
        return username

    def clean_email(self):
        email = self.cleaned_data["email"]
        if User.objects.filter(email=email).exists():
            raise ValidationError(
                "An account with this email already exists."
            )
        return email

    def clean(self):
        cleaned_data = super().clean()

        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")
        role = cleaned_data.get("role")
        company = cleaned_data.get("company")

        if password and confirm_password and password != confirm_password:
            raise ValidationError("Passwords do not match.")

        if role in ["Recruiter", "Interviewer"] and not company:
            self.add_error(
                "company",
                "Company name is required for this role.",
            )

        return cleaned_data

