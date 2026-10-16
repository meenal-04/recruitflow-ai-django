from django.db import models
from django.contrib.auth.models import User

class Job(models.Model):
    title = models.CharField(max_length=200, blank=True, default='')
    description = models.TextField()
    required_skills = models.CharField(max_length=500)
    experience_required = models.CharField(max_length=100)
    location = models.CharField(max_length=100)
    status = models.CharField(max_length=20, default='Open')
    created_at = models.DateTimeField(auto_now_add=True)

    recruiter = models.ForeignKey(
        'Recruiter',
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    def __str__(self):
        return self.title

class Candidate(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=15, blank=True)
    skills = models.CharField(max_length=500, blank=True)
    experience = models.CharField(max_length=100, blank=True)
    resume = models.FileField(upload_to='resumes/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    profile_picture = models.ImageField(
        upload_to='profile_pictures/',
        blank=True,
        null=True)

    def __str__(self):
        return self.user.username

class Application(models.Model):
    STATUS_CHOICES = [
        ('Applied', 'Applied'),
        ('Under Review', 'Under Review'),
        ('Shortlisted', 'Shortlisted'),
        ('Interview', 'Interview'),
        ('Selected', 'Selected'),
        ('Rejected', 'Rejected'),
    ]

    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE)
    job = models.ForeignKey(Job, on_delete=models.CASCADE)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='Applied'
    )
    applied_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['candidate', 'job'],
                name='unique_candidate_job_application'
            )
        ]

    def __str__(self):
        return f"{self.candidate} - {self.job}"

class Recruiter(models.Model):

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE
    )

    company = models.CharField(
        max_length=200
    )

    company_description = models.TextField(
        blank=True
    )

    company_website = models.URLField(
        blank=True
    )

    company_location = models.CharField(
        max_length=200,
        blank=True
    )

    phone = models.CharField(
        max_length=15
    )

    def __str__(self):
        return self.user.username

class Interviewer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    company = models.CharField(max_length=200)
    phone = models.CharField(max_length=15, blank=True)

    def __str__(self):
        return self.user.username

class Interview(models.Model):
    MODE_CHOICES = [
        ('Online', 'Online'),
        ('Offline', 'Offline'),
    ]

    STATUS_CHOICES = [
        ('Scheduled', 'Scheduled'),
        ('Completed', 'Completed'),
        ('Cancelled', 'Cancelled'),
    ]

    application = models.ForeignKey(
        Application,
        on_delete=models.CASCADE
    )

    interviewer = models.ForeignKey(
        Interviewer,
        on_delete=models.CASCADE
    )

    scheduled_at = models.DateTimeField()

    mode = models.CharField(
        max_length=20,
        choices=MODE_CHOICES,
        default='Online'
    )

    meeting_link = models.URLField(blank=True)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='Scheduled'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.application.candidate} - {self.application.job}"

class InterviewFeedback(models.Model):
    interview = models.OneToOneField(
        Interview,
        on_delete=models.CASCADE
    )

    strengths = models.TextField(blank=True)

    areas_to_explore = models.TextField(blank=True)

    technical_feedback = models.TextField(blank=True)

    overall_feedback = models.TextField(blank=True)

    recommendation = models.CharField(
        max_length=50,
        blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Feedback - {self.interview}"

class Notification(models.Model):

    recipient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notifications'
    )

    title = models.CharField(max_length=200)

    message = models.TextField()

    notification_type = models.CharField(
        max_length=50,
        default='general'
    )

    # Optional page to open when notification is clicked
    link = models.CharField(
        max_length=300,
        blank=True,
        null=True
    )

    is_read = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.recipient.username} - {self.title}"