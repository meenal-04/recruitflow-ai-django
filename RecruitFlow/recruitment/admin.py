from django.contrib import admin
from .models import (
    Job,
    Candidate,
    Application,
    Recruiter,
    Interviewer,
    Interview,
    InterviewFeedback
)

admin.site.register(Job)
admin.site.register(Candidate)
admin.site.register(Application)
admin.site.register(Recruiter)
admin.site.register(Interviewer)
admin.site.register(Interview)
admin.site.register(InterviewFeedback)