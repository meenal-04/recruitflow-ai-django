# RecruitFlow

**An AI-Assisted Applicant Tracking & Recruitment Management System**

RecruitFlow is a Django-based recruitment management system that manages the recruitment lifecycle across three user roles: Candidate, Recruiter, and Interviewer. It provides AI assistance for skill matching, resume screening, and interview preparation.

## Features

### Candidate
- Register, log in, and manage a profile, including skills, experience, phone number, and profile picture.
- Upload and update resumes in PDF, DOCX, and TXT formats.
- Browse open jobs with detailed descriptions.
- View AI-assisted job-fit analysis, including matched and missing skills.
- Apply for jobs, with duplicate applications prevented at the database level.
- Track application status.
- Receive notifications when application status changes.
- View scheduled interviews and interviewer feedback.

### Recruiter
- Create and manage job postings.
- Review applications for their own jobs using role-scoped querysets.
- Search candidates by name, email, or job title.
- Move candidates through the hiring pipeline:

  `Applied → Under Review → Shortlisted → Interview → Selected / Rejected`

- View AI-assisted resume screening results.
- Review interviewer feedback and make the final hiring decision.

### Interviewer
- Receive notifications when candidates reach the Interview stage.
- Schedule interviews with a date, mode, and meeting link.
- Generate role-specific interview questions using AI.
- Submit structured feedback covering strengths, areas to explore, technical performance, and overall assessment.
- Mark interviews as completed.

### Notifications
- In-app notification bell with unread count.
- Persistent notification list with mark-as-read functionality.
- Notifications triggered by meaningful application status changes, with duplicate notifications avoided.

## Architecture

RecruitFlow follows a layered architecture with separate responsibilities for the user interface, application logic, data management, and AI integration.

```text
┌──────────────────────────────────────────────────────┐
│ Layer 1 — Presentation                               │
│ HTML, CSS, Bootstrap 5, JavaScript                   │
├──────────────────────────────────────────────────────┤
│ Layer 2 — Application                                │
│ Django Views, Forms, URL Routing, Authentication      │
├──────────────────────────┬───────────────────────────┤
│ Layer 3A — Data          │ Layer 3B — AI             │
│ SQLite + Django ORM      │ OmniRoute → LLM Provider  │
│                          │ Deterministic Fallback    │
└──────────────────────────┴───────────────────────────┘
```

**Key design principle: AI is assistive, not authoritative.**

AI supports matching, screening, and interview preparation; it does not make the final hiring decision. When an AI provider is unavailable, the application can fall back to deterministic logic for supported operations.

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python, Django |
| Frontend | HTML, CSS, Bootstrap 5, JavaScript |
| Database | SQLite via Django ORM |
| AI Gateway | OmniRoute, using an OpenAI-compatible interface |
| Resume Parsing | PyPDF2 for PDF, python-docx for DOCX |
| Configuration | python-dotenv |
| Version Control | Git and GitHub |

## Project Structure

```text
RecruitFlow/
├── config/
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── recruitment/
│   ├── models.py
│   ├── views.py
│   ├── forms.py
│   ├── urls.py
│   ├── ai_services.py
│   ├── context_processors.py
│   └── admin.py
├── templates/
│   ├── recruitment/
│   └── registration/
├── media/
├── manage.py
├── requirements.txt
├── .gitignore
├── .env.example
└── README.md
```

- `config/` — Project settings and root URL configuration.
- `recruitment/` — Main application containing models, views, forms, routing, and AI integration.
- `templates/` — HTML templates for the application and authentication.
- `media/` — User-uploaded files; should not be committed to Git.
- `ai_services.py` — AI integration and fallback logic.
- `.env.example` — Template for required environment variables.

## Data Model

The application uses eight models organized into three groups.

### User Roles
- `Candidate` — Candidate profile, skills, experience, and resume.
- `Recruiter` — Recruiter and company information.
- `Interviewer` — Interviewer information, including company and phone.

### Recruitment Workflow
- `Job` — Job postings created by recruiters.
- `Application` — Connects a candidate to a job and tracks application status. A database constraint prevents duplicate applications.
- `Interview` — Connects an application to an interviewer and stores scheduling information.
- `InterviewFeedback` — Stores structured feedback associated with an interview.

### Communication
- `Notification` — Stores notifications for users.

## Application Workflow

```text
Candidate applies for a job
          ↓
       Applied
          ↓
     Under Review
          ↓
      Shortlisted
          ↓
       Interview
          ↓
  Selected / Rejected
```

- **Recruiter:** Manages job postings, application status transitions, and the final hiring decision.
- **Interviewer:** Schedules interviews and submits feedback.
- **Candidate:** Tracks application progress and receives notifications.
- **AI:** Assists with job matching, resume screening, and interview preparation.

## Setup Instructions

### Prerequisites
- Python installed on your system.
- Git installed on your system.
- An OmniRoute API key if you want to use AI-powered features.

### 1. Clone the repository

Replace the URL below with actual GitHub repository URL.

```bash
git clone https://github.com/meenal-04/Django-project.git
cd RecruitFlow
```

### 2. Create and activate a virtual environment

**Windows:**

```bash
python -m venv .venv
.venv\Scripts\activate
```

**macOS / Linux:**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Copy `.env.example` to `.env`.

**Windows Command Prompt:**

```cmd
copy .env.example .env
```

**macOS / Linux:**

```bash
cp .env.example .env
```

Open `.env` and configure the variables supported by your application. For example:

```dotenv
OMNIROUTE_API_KEY=your-key-here
OMNIROUTE_MODEL=auto
```

Replace the placeholder with your own API key. Never commit your real `.env` file or expose your API key publicly.

### 5. Apply database migrations

```bash
python manage.py migrate
```

### 6. Create an administrator account

```bash
python manage.py createsuperuser
```

Follow the prompts to create your account.

### 7. Start the development server

```bash
python manage.py runserver
```

Open [http://127.0.0.1:8000/](http://127.0.0.1:8000/) in your browser.

## Testing the Application Workflow

After starting the application, you can test the recruitment process:

1. Register a Candidate account at `/register/`.
2. Register a Recruiter account at `/register/`.
3. Register an Interviewer account at `/register/`.
4. Log in as Recruiter and create a job posting.
5. Log in as Candidate and apply for the job.
6. Log in as Recruiter and update the application status.
7. When the application reaches the Interview stage, log in as Interviewer and schedule the interview.
8. Log in as Interviewer and submit interview feedback.
9. Log in as Recruiter to review the feedback and make the final hiring decision.

## AI Integration Notes

- AI is optional; the application should remain usable without an API key for supported non-AI operations.
- AI-assisted operations use fallback behavior when the provider is unavailable, where implemented.
- Deterministic skill matching uses set intersection rather than an LLM.
- The API key should be loaded from environment variables and never hardcoded in source code.
- Configure the AI provider using `.env` or environment variables according to the application's settings.

## Limitations

- SQLite is intended primarily for development and may not be suitable for production workloads with substantial concurrent writes.
- Notifications are in-app; email and SMS notifications are not implemented.
- Resume parsing may not extract text from scanned or image-only PDFs.
- Interview assignment currently uses the first available interviewer rather than routing based on skills or availability.
- An analytics dashboard is not currently implemented.

## Future Scope

- Migrate to PostgreSQL for production readiness.
- Add email and SMS notifications.
- Build recruiter analytics for stage conversion and time-to-hire.
- Improve interview assignment using skill matching and interviewer availability.
- Explore NLP-based resume parsing with spaCy or a hosted service.
- Add multi-company support.
- Enable PDF report exports.

## License

This project is developed for educational and portfolio purposes.
