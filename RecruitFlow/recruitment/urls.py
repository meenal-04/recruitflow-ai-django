from django.urls import path
from . import views


urlpatterns = [

    # Home
    path("", views.home, name="home"),

    # Registration
    path("register/", views.register_user, name="register"),

    # Login
    path("login/candidate/", views.candidate_login, name="candidate_login"),
    path("login/recruiter/", views.recruiter_login, name="recruiter_login"),
    path("login/interviewer/", views.interviewer_login, name="interviewer_login"),

    path("role-redirect/", views.role_redirect, name="role_redirect"),

    # Jobs
    path("jobs/", views.job_list, name="job_list"),
    path("jobs/<int:job_id>/", views.job_detail, name="job_detail"),
    path("apply/<int:job_id>/", views.apply_job, name="apply_job"),

    # Candidate
    path("candidate/dashboard/", views.candidate_dashboard, name="candidate_dashboard"),
    path("candidate/profile/", views.candidate_profile, name="candidate_profile"),

    # Recruiter
    path("recruiter/dashboard/", views.recruiter_dashboard, name="recruiter_dashboard"),
    path("recruiter/create-job/", views.create_job, name="create_job"),
    path("recruiter/applications/", views.recruiter_applications, name="recruiter_applications"),
    path("recruiter/candidate/<int:application_id>/", views.candidate_detail, name="candidate_detail"),
    path("recruiter/schedule/<int:application_id>/", views.schedule_interview, name="schedule_interview"),
    path(
        "recruiter/ai-screening/<int:application_id>/",
        views.ai_resume_screening,
        name="ai_resume_screening",
    ),

    # Interviewer
    path("interviewer/dashboard/", views.interviewer_dashboard, name="interviewer_dashboard"),
    path("interviewer/feedback/<int:interview_id>/", views.interview_feedback, name="interview_feedback"),
    path("interviewer/questions/<int:interview_id>/", views.generate_questions, name="generate_questions"),

    # Notifications
    path("notifications/", views.notifications, name="notifications"),
    path(
        "notifications/<int:notification_id>/read/",
        views.mark_notification_read,
        name="mark_notification_read",
    ),
    path(
        "notifications/clear/",
        views.clear_all_notifications,
        name="clear_all_notifications",
    ),
]