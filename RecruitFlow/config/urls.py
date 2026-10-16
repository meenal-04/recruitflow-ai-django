"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path, include


urlpatterns = [
    path("admin/", admin.site.urls),

    # Logout (POST only, redirects home)
    path(
        "logout/",
        auth_views.LogoutView.as_view(next_page="home"),
        name="logout",
    ),

    # Recruitment app
    path("", include("recruitment.urls")),
]


if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT,
    )

# from django.contrib import admin
# from django.urls import path, include
# from django.conf import settings
# from django.conf.urls.static import static
# from recruitment.views import (
#     home,
#     job_list,
#     apply_job,
#     candidate_login,
#     recruiter_login,
#     interviewer_login,
#     candidate_dashboard,
#     candidate_profile,
#     create_job,
#     role_redirect,
#     recruiter_dashboard,
#     recruiter_applications,
#     candidate_detail,
#     interviewer_dashboard,
#     interview_feedback,
#     job_detail,
#     schedule_interview,
#     generate_questions,
#     ai_resume_screening,
#     register_user,
#     notifications,
#     mark_notification_read,
#     clear_all_notifications,
# )


# urlpatterns = [
#     path('admin/', admin.site.urls),
#     path('', home, name='home'),
#     path('jobs/', job_list, name='job_list'),
#     path('apply/<int:job_id>/', apply_job, name='apply_job'),
#     path('accounts/', include('django.contrib.auth.urls')),
#     path('register/',register_user,name='register'),
#     path('candidate/login/',candidate_login,name='candidate_login'),
#     path('recruiter/login/',recruiter_login,name='recruiter_login'),
#     path('interviewer/login/',interviewer_login,name='interviewer_login'), 
#     path('candidate/dashboard/', candidate_dashboard, name='candidate_dashboard'),
#     path('candidate/profile/', candidate_profile, name='candidate_profile'),
#     path('recruiter/create-job/', create_job, name='create_job'),
#     path('role-redirect/', role_redirect, name='role_redirect'),
#     path('recruiter/dashboard/', recruiter_dashboard, name='recruiter_dashboard'),
#     path('recruiter/applications/', recruiter_applications, name='recruiter_applications'),
#     path('recruiter/candidate/<int:application_id>/', candidate_detail, name='candidate_detail'), 
#     path('interviewer/dashboard/',interviewer_dashboard,name='interviewer_dashboard'),
#     path('interviewer/feedback/<int:interview_id>/',interview_feedback, name='interview_feedback'), 
#     path('jobs/<int:job_id>/', job_detail, name='job_detail'), 
#     path('interviewer/questions/<int:interview_id>/',generate_questions,name='generate_questions'),
#     path('interviewer/schedule/<int:application_id>/',schedule_interview,name='schedule_interview'),
#     path('recruiter/ai-screening/<int:application_id>/',ai_resume_screening,name='ai_resume_screening'),
#     path('notifications/',notifications,name='notifications'),
#     path('notifications/read/<int:notification_id>/',mark_notification_read,name='mark_notification_read'),
#     path('notifications/clear/',clear_all_notifications,name='clear_all_notifications'),
# ]

# urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# if settings.DEBUG:
#     urlpatterns += static(
#         settings.MEDIA_URL,
#         document_root=settings.MEDIA_ROOT
#     )