from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Q
from django.shortcuts import redirect, render
from django.utils import timezone

from .ai_services import (
    generate_interview_questions,
    generate_job_explanation,
    get_job_match,
    get_job_recommendations,
    generate_resume_screening,
)

from .forms import (
    CandidateProfileForm,
    InterviewFeedbackForm,
    InterviewForm,
    JobForm,
    RegistrationForm,
)

from .models import (
    Job,
    Candidate,
    Application,
    Recruiter,
    Interviewer,
    Interview,
    InterviewFeedback,
    Notification,
)

def create_notification(
    user,
    title,
    message,
    notification_type="general",
    link=None,
):
    if user is None:
        return
    Notification.objects.create(
        recipient=user,
        title=title,
        message=message,
        notification_type=notification_type,
        link=link,
    )


@login_required
def notifications(request):
    notification_list = Notification.objects.filter(
        recipient=request.user
    ).order_by("-created_at")

    return render(
        request,
        "recruitment/notifications.html",
        {"notifications": notification_list},
    )


@login_required
def mark_notification_read(request, notification_id):
    notification = Notification.objects.filter(
        id=notification_id,
        recipient=request.user,
    ).first()

    if notification:
        notification.is_read = True
        notification.save()

        if notification.link:
            return redirect(notification.link)

    return redirect("notifications")


@login_required
def clear_all_notifications(request):
    Notification.objects.filter(
        recipient=request.user
    ).update(is_read=True)

    messages.success(request, "All notifications marked as read.")
    return redirect("notifications")


# =========================================================
# HOME
# =========================================================

def home(request):

    return render(
        request,
        "home.html"
    )


# =========================================================
# LOGIN
# =========================================================

def _login_for_role(
    request,
    role_model,
    success_url,
    template_name
):

    if request.method == "POST":

        username = request.POST.get(
            "username",
            ""
        ).strip()

        password = request.POST.get(
            "password",
            ""
        )

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if (
            user is not None
            and role_model.objects.filter(
                user=user
            ).exists()
        ):

            login(
                request,
                user
            )

            return redirect(
                success_url
            )

        messages.error(
            request,
            "Invalid username/password or wrong role."
        )

    return render(
        request,
        template_name
    )


def candidate_login(request):

    return _login_for_role(
        request,
        Candidate,
        "candidate_dashboard",
        "registration/candidate_login.html"
    )


def recruiter_login(request):

    return _login_for_role(
        request,
        Recruiter,
        "recruiter_dashboard",
        "registration/recruiter_login.html"
    )


def interviewer_login(request):

    return _login_for_role(
        request,
        Interviewer,
        "interviewer_dashboard",
        "registration/interviewer_login.html"
    )


# =========================================================
# ROLE REDIRECT
# =========================================================

@login_required
def role_redirect(request):

    if Candidate.objects.filter(user=request.user).exists():
        return redirect('candidate_dashboard')

    if Recruiter.objects.filter(user=request.user).exists():
        return redirect('recruiter_dashboard')

    if Interviewer.objects.filter(user=request.user).exists():
        return redirect('interviewer_dashboard')

    messages.error(
        request,
        'Your account does not have a valid RecruitFlow role.'
    )

    return redirect('home')


# =========================================================
# REGISTER USER
# =========================================================

def register_user(request):

    if request.user.is_authenticated:
        return redirect('role_redirect')

    if request.method == 'POST':

        form = RegistrationForm(request.POST)

        if form.is_valid():

            username = form.cleaned_data['username']
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            role = form.cleaned_data['role']
            phone = form.cleaned_data.get('phone', '')
            company = form.cleaned_data.get('company', '')

            try:

                with transaction.atomic():

                    user = User.objects.create_user(
                        username=username,
                        email=email,
                        password=password
                    )

                    if role == 'Candidate':

                        Candidate.objects.create(
                            user=user,
                            phone=phone
                        )

                    elif role == 'Recruiter':

                        Recruiter.objects.create(
                            user=user,
                            company=company,
                            phone=phone
                        )

                    elif role == 'Interviewer':

                        Interviewer.objects.create(
                            user=user,
                            company=company,
                            phone=phone
                        )

                    login(request, user)

                    messages.success(
                        request,
                        f'Welcome to RecruitFlow, {username}! '
                        'Your account has been created successfully.'
                    )

                    return redirect('role_redirect')

            except Exception as e:

                print("REGISTRATION ERROR:", e)

                messages.error(
                    request,
                    'Account could not be created. Please try again.'
                )

    else:

        form = RegistrationForm()

    return render(
        request,
        'recruitment/register.html',
        {
            'form': form
        }
    )                     

# =========================================================
# JOB LIST
# =========================================================

@login_required
def job_list(request):

    jobs = Job.objects.filter(
        status="Open"
    ).order_by(
        "-created_at"
    )

    return render(
        request,
        "recruitment/job_list.html",
        {
            "jobs": jobs
        }
    )


# =========================================================
# JOB DETAIL + AI JOB FIT
# =========================================================

@login_required
def job_detail(
    request,
    job_id
):

    job = (
        Job.objects
        .filter(
            id=job_id,
            status="Open"
        )
        .select_related(
            "recruiter"
        )
        .first()
    )

    if job is None:

        return redirect(
            "job_list"
        )

    candidate = Candidate.objects.filter(
        user=request.user
    ).first()

    already_applied = False

    match = None

    ai_explanation = None

    if candidate:

        already_applied = Application.objects.filter(
            candidate=candidate,
            job=job
        ).exists()

        # ---------------------------------------------
        # FACTUAL SKILL MATCH
        # ---------------------------------------------

        match = get_job_match(
            candidate,
            job
        )

        matched_skills = match.get(
            "matched_skills",
            []
        )

        missing_skills = match.get(
            "missing_skills",
            []
        )

        ai_explanation = generate_job_explanation(
            candidate,
            job,
            matched_skills,
            missing_skills
        )

    return render(
        request,
        "recruitment/job_detail.html",
        {
            "job": job,
            "candidate": candidate,
            "already_applied": already_applied,
            "match": match,
            "ai_explanation": ai_explanation,
        }
    )


# =========================================================
# APPLY
# =========================================================

@login_required
def apply_job(
    request,
    job_id
):

    job = Job.objects.filter(
        id=job_id,
        status="Open"
    ).first()

    candidate = Candidate.objects.filter(
        user=request.user
    ).first()

    if job is None or candidate is None:

        return redirect(
            "job_list"
        )

    Application.objects.get_or_create(
        candidate=candidate,
        job=job
    )

    messages.success(
        request,
        f"Application submitted for {job.title}."
    )

    return redirect(
        "candidate_dashboard"
    )


# =========================================================
# CANDIDATE DASHBOARD
# =========================================================

@login_required
def candidate_dashboard(request):

    candidate = Candidate.objects.filter(
        user=request.user
    ).first()

    if candidate is None:

        return redirect(
            "home"
        )

    applications = (
        Application.objects
        .filter(
            candidate=candidate
        )
        .select_related(
            "job"
        )
        .order_by(
            "-applied_at"
        )
    )

    applied_job_ids = Application.objects.filter(
        candidate=candidate
    ).values_list(
        "job_id",
        flat=True
    )

    open_jobs = (
        Job.objects
        .filter(
            status="Open"
        )
        .exclude(
            id__in=applied_job_ids
        )
        .order_by(
            "-created_at"
        )
    )

    recommendations = get_job_recommendations(
        candidate,
        open_jobs
    )[:6]

    upcoming_interviews = (
        Interview.objects
        .filter(
            application__candidate=candidate,
            status="Scheduled"
        )
        .select_related(
            "application__job",
            "interviewer__user"
        )
        .order_by(
            "scheduled_at"
        )
    )

    completed_interviews = (
        Interview.objects
        .filter(
            application__candidate=candidate,
            status="Completed"
        )
        .select_related(
            "application__job"
        )
        .order_by(
            "-scheduled_at"
        )
    )

    feedbacks = (
        InterviewFeedback.objects
        .filter(
            interview__application__candidate=candidate,
            interview__status="Completed"
        )
        .select_related(
            "interview__application__job"
        )
        .order_by(
            "-created_at"
        )
    )

    return render(
        request,
        "recruitment/candidate_dashboard.html",
        {
            "candidate": candidate,
            "applications": applications,
            "recommendations": recommendations,
            "upcoming_interviews": upcoming_interviews,
            "completed_interviews": completed_interviews,
            "feedbacks": feedbacks,
        }
    )


# =========================================================
# CANDIDATE PROFILE
# =========================================================

@login_required
def candidate_profile(request):

    candidate = Candidate.objects.get(user=request.user)

    if request.method == 'POST':

        form = CandidateProfileForm(
            request.POST,
            request.FILES,
            instance=candidate
        )

        if form.is_valid():

            form.save()

            messages.success(
                request,
                'Profile updated successfully.'
            )

            return redirect('candidate_dashboard')

    else:

        form = CandidateProfileForm(
            instance=candidate
        )

    return render(
        request,
        'recruitment/candidate_profile.html',
        {
            'form': form,
            'candidate': candidate,
        }
    )


# =========================================================
# CREATE JOB
# =========================================================

@login_required
def create_job(request):

    recruiter = Recruiter.objects.filter(
        user=request.user
    ).first()

    if recruiter is None:

        return redirect(
            "home"
        )

    if request.method == "POST":

        form = JobForm(
            request.POST
        )

        if form.is_valid():

            job = form.save(
                commit=False
            )

            job.recruiter = recruiter

            job.save()

            messages.success(
                request,
                "Job created successfully."
            )

            return redirect(
                "recruiter_dashboard"
            )

    else:

        form = JobForm()

    return render(
        request,
        "recruitment/create_job.html",
        {
            "form": form,
            "recruiter": recruiter
        }
    )


# =========================================================
# RECRUITER DASHBOARD
# =========================================================

@login_required
def recruiter_dashboard(request):

    recruiter = Recruiter.objects.filter(
        user=request.user
    ).first()

    if recruiter is None:

        return redirect(
            "home"
        )

    jobs = Job.objects.filter(
        recruiter=recruiter
    ).order_by(
        "-created_at"
    )

    application_count = Application.objects.filter(
        job__recruiter=recruiter
    ).count()

    return render(
        request,
        "recruitment/recruiter_dashboard.html",
        {
            "recruiter": recruiter,
            "jobs": jobs,
            "application_count": application_count
        }
    )


# =========================================================
# RECRUITER APPLICATIONS
# =========================================================

@login_required
def recruiter_applications(request):

    recruiter = Recruiter.objects.filter(
        user=request.user
    ).first()

    if recruiter is None:
        return redirect("home")

    if request.method == "POST":

        application_id = request.POST.get("application_id")
        new_status = request.POST.get("status")

        application = Application.objects.filter(
            id=application_id,
            job__recruiter=recruiter
        ).select_related(
            "candidate__user",
            "job"
        ).first()

        if application is None:

            messages.error(
                request,
                "Application not found."
            )

            return redirect("recruiter_applications")

        if application.status in [
            "Selected",
            "Rejected"
        ]:

            messages.warning(
                request,
                f"This application is already "
                f"{application.status.lower()}."
            )

            return redirect("recruiter_applications")

        valid_statuses = [
            "Applied",
            "Under Review",
            "Shortlisted",
            "Interview",
            "Selected",
            "Rejected"
        ]

        if new_status not in valid_statuses:

            messages.error(
                request,
                "Invalid application status."
            )

            return redirect("recruiter_applications")

        # Remember the previous status
        old_status = application.status

        # Update application status
        application.status = new_status
        application.save()

        # -----------------------------------------
        # FINAL SUCCESS BLOCK FOR SELECTION/REJECTION
        # -----------------------------------------
        
        if new_status == "Selected":

            create_notification(
                user=application.candidate.user,
                title="Congratulations — Selected",
                message=(
                    f"You have been selected for "
                    f"'{application.job.title}'."
                ),
                notification_type="selected",
            )

        elif new_status == "Rejected":

            create_notification(
                user=application.candidate.user,
                title="Application Update",
                message=(
                    f"Your application for "
                    f"'{application.job.title}' "
                    f"was not selected at this time. "
                    f"Thank you for applying."
                ),
                notification_type="rejected",
            )

        # -----------------------------------------
        # CREATE NOTIFICATION FOR CANDIDATE
        # -----------------------------------------

        if old_status != new_status:

            create_notification(
                user=application.candidate.user,
                title="Application Status Updated",
                message=(
                    f"Your application for "
                    f"'{application.job.title}' "
                    f"has been updated from "
                    f"'{old_status}' to "
                    f"'{new_status}'."
                ),
                notification_type="application_status",
            )

        # -----------------------------------------
        # INTERVIEW NOTIFICATION
        # -----------------------------------------

        if new_status == "Interview" and old_status != "Interview":

            interviewer = Interviewer.objects.first()

            if interviewer:

                create_notification(
                    user=interviewer.user,
                    title="Interview Scheduling Required",
                    message=(
                        f"Candidate "
                        f"{application.candidate.user.username} "
                        f"has been moved to Interview stage "
                        f"for '{application.job.title}'. "
                        f"Please schedule the interview."
                    ),
                    notification_type="interview_scheduling",
                )

            create_notification(
                user=application.candidate.user,
                title="Interview Stage Reached",
                message=(
                    f"Your application for "
                    f"'{application.job.title}' "
                    f"has reached the Interview stage. "
                    f"Please prepare for your upcoming interview."
                ),
                notification_type="interview_stage",
            )

        # -----------------------------------------
        # SUCCESS MESSAGE FOR RECRUITER
        # -----------------------------------------

        messages.success(
            request,
            f"Application status updated to "
            f"{new_status}."
        )

        return redirect(
            "recruiter_applications"
        )

    # -----------------------------------------
    # SEARCH
    # -----------------------------------------

    search = request.GET.get(
        "search",
        ""
    ).strip()

    applications = (
        Application.objects
        .filter(
            job__recruiter=recruiter
        )
        .select_related(
            "candidate__user",
            "job"
        )
        .order_by(
            "-applied_at"
        )
    )

    if search:

        applications = applications.filter(

            Q(
                candidate__user__username__icontains=search
            )

            |
            Q(
                candidate__user__email__icontains=search
            )

            |
            Q(
                job__title__icontains=search
            )
        )

    return render(
        request,
        "recruitment/recruiter_applications.html",
        {
            "applications": applications,
            "search": search
        }
    )


# =========================================================
# CANDIDATE DETAIL FOR RECRUITER
# =========================================================

@login_required
def candidate_detail(
    request,
    application_id
):

    recruiter = Recruiter.objects.filter(
        user=request.user
    ).first()

    if recruiter is None:

        return redirect(
            "home"
        )

    application = (
        Application.objects
        .select_related(
            "candidate__user",
            "job"
        )
        .filter(
            id=application_id,
            job__recruiter=recruiter
        )
        .first()
    )

    if application is None:

        return redirect(
            "recruiter_applications"
        )

    interviewers = Interviewer.objects.order_by(
        "user__username"
    )

    return render(
        request,
        "recruitment/candidate_detail.html",
        {
            "application": application,
            "interviewers": interviewers
        }
    )

# ----------------------------------------------------
# AI RESUME SCREENING
# ----------------------------------------------------

@login_required
def ai_resume_screening(request, application_id):
    recruiter = Recruiter.objects.filter(
        user=request.user
    ).first()

    if recruiter is None:
        return redirect('home')

    application = Application.objects.filter(
        id=application_id,
        job__recruiter=recruiter
    ).select_related(
        'candidate__user',
        'job'
    ).first()

    if application is None:
        messages.error(
            request,
            'Candidate application not found.'
        )
        return redirect('recruiter_applications')

    candidate = application.candidate
    job = application.job

    screening = generate_resume_screening(
        candidate,
        job
    )

    return render(
        request,
        'recruitment/ai_resume_screening.html',
        {
            'application': application,
            'candidate': candidate,
            'job': job,
            'screening': screening,
        }
    )


# =========================================================
# INTERVIEWER DASHBOARD
# =========================================================

@login_required
def interviewer_dashboard(request):

    interviewer = Interviewer.objects.filter(
        user=request.user
    ).first()

    if interviewer is None:
        return redirect('home')

    interviews = Interview.objects.filter(
        interviewer=interviewer
    ).select_related(
        'application__candidate__user',
        'application__job'
    ).order_by('scheduled_at')

    feedback_ids = set(
        InterviewFeedback.objects.filter(
            interview__in=interviews
        ).values_list(
            'interview_id',
            flat=True
        )
    )

    # Applications waiting for interview scheduling
    scheduled_application_ids = Interview.objects.values_list(
        'application_id',
        flat=True
    )

    pending_interviews = Application.objects.filter(
        status='Interview'
    ).exclude(
        id__in=scheduled_application_ids
    ).select_related(
        'candidate__user',
        'job'
    ).order_by('-updated_at')

    return render(
        request,
        'recruitment/interviewer_dashboard.html',
        {
            'interviewer': interviewer,
            'interviews': interviews,
            'feedback_ids': feedback_ids,
            'pending_interviews': pending_interviews,
        }
    )


# =========================================================
# SCHEDULE INTERVIEW
# =========================================================

@login_required
def schedule_interview(request, application_id):

    interviewer = Interviewer.objects.filter(
        user=request.user
    ).first()

    if interviewer is None:
        return redirect('home')

    application = Application.objects.filter(
        id=application_id,
        status='Interview'
    ).select_related(
        'candidate__user',
        'job'
    ).first()

    if application is None:
        messages.error(
            request,
            'This candidate is not currently ready for interview scheduling.'
        )
        return redirect('interviewer_dashboard')

    # Prevent duplicate interview scheduling
    existing_interview = Interview.objects.filter(
        application=application
    ).first()

    if existing_interview:
        messages.info(
            request,
            'An interview has already been scheduled for this candidate.'
        )
        return redirect('interviewer_dashboard')

    if request.method == 'POST':

        form = InterviewForm(request.POST)

        if form.is_valid():

            interview = form.save(commit=False)

            interview.application = application
            interview.interviewer = interviewer
            interview.status = 'Scheduled'

            interview.save()

            create_notification(
                user=application.candidate.user,
                title="Interview Scheduled",
                message=(
                    f"Your interview for "
                    f"'{application.job.title}' "
                    f"has been scheduled on "
                    f"{interview.scheduled_at:%d %b %Y, %I:%M %p}. "
                    f"Mode: {interview.mode}."
                ),
                notification_type="interview_scheduled",
            )

            messages.success(
                request,
                'Interview scheduled successfully.'
            )

            return redirect('interviewer_dashboard')

    else:

        form = InterviewForm()

    return render(
        request,
        'recruitment/schedule_interview.html',
        {
            'form': form,
            'application': application,
            'interviewer': interviewer,
        }
    )

# =========================================================
# INTERVIEW FEEDBACK
# =========================================================

@login_required
def interview_feedback(request,interview_id):

    interviewer = Interviewer.objects.filter(
        user=request.user
    ).first()

    if interviewer is None:

        return redirect(
            "home"
        )

    interview = (
        Interview.objects
        .filter(
            id=interview_id,
            interviewer=interviewer
        )
        .select_related(
            "application__candidate__user",
            "application__job"
        )
        .first()
    )

    if interview is None:

        return redirect(
            "interviewer_dashboard"
        )

    feedback = InterviewFeedback.objects.filter(
        interview=interview
    ).first()

    if request.method == "POST":

        form = InterviewFeedbackForm(
            request.POST,
            instance=feedback
        )

        if form.is_valid():

            feedback = form.save(
                commit=False
            )

            feedback.interview = interview

            feedback.save()

            interview.status = "Completed"

            interview.save()

            recruiter = interview.application.job.recruiter

            if recruiter:

                create_notification(
                    user=recruiter.user,
                    title="Interview Feedback Submitted",
                    message=(
                        f"Feedback for "
                        f"{interview.application.candidate.user.username} "
                        f"on '{interview.application.job.title}' "
                        f"is now available."
                    ),
                    notification_type="feedback_submitted",
                )

            messages.success(
                request,
                "Interview feedback submitted successfully."
            )

            return redirect(
                "interviewer_dashboard"
            )

    else:

        form = InterviewFeedbackForm(
            instance=feedback
        )

    return render(
        request,
        "recruitment/interview_feedback.html",
        {
            "interview": interview,
            "form": form
        }
    )


# =========================================================
# AI INTERVIEW QUESTIONS
# =========================================================

@login_required
def generate_questions(request, interview_id):

    interviewer = Interviewer.objects.filter(
        user=request.user
    ).first()

    if interviewer is None:
        return redirect('home')

    interview = Interview.objects.filter(
        id=interview_id,
        interviewer=interviewer
    ).select_related(
        'application__candidate__user',
        'application__job'
    ).first()

    if interview is None:
        messages.error(
            request,
            'Interview not found.'
        )
        return redirect('interviewer_dashboard')

    candidate = interview.application.candidate
    job = interview.application.job

    questions = generate_interview_questions(
        candidate,
        job
    )

    return render(
        request,
        'recruitment/interview_questions.html',
        {
            'interview': interview,
            'candidate': candidate,
            'job': job,
            'questions': questions,
        }
    )