import os
from openai import OpenAI

# ============================================================
# OMNIROUTE CONFIGURATION (Local Gateway)
# ============================================================

# The "auto" model lets OmniRoute pick the best free provider automatically.
# You can also use "auto/best-free" or a specific provider prefix like "oc/".
MODEL_NAME = os.getenv("OMNIROUTE_MODEL", "auto")


def _get_client():
    """
    Create a client for the local OmniRoute gateway.
    """
    # Use a distinct env var name to avoid confusion with OpenRouter
    api_key = os.getenv("OMNIROUTE_API_KEY")

    if not api_key:
        print("OMNIROUTE DEBUG: API key not set")
        return None

    try:
        return OpenAI(
            # This is the default local OmniRoute API endpoint
            base_url="http://localhost:20128/v1",
            api_key=api_key,
            timeout=30.0,
        )
    except Exception as e:
        print("OMNIROUTE CLIENT ERROR:", e)
        return None

# ============================================================
# SKILL MATCHING
# ============================================================

def _normalise_skills(value):
    return {
        skill.strip().lower()
        for skill in (value or "").split(",")
        if skill.strip()
    }


def get_job_match(candidate, job):
    candidate_skills = _normalise_skills(candidate.skills)
    required_skills = _normalise_skills(job.required_skills)

    matched_skills = sorted(
        candidate_skills.intersection(required_skills)
    )

    missing_skills = sorted(
        required_skills.difference(candidate_skills)
    )

    total_required = len(required_skills)

    match_percentage = (
        round((len(matched_skills) / total_required) * 100)
        if total_required > 0
        else 0
    )

    return {
        "match_percentage": match_percentage,
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "total_required": total_required,
        "total_matched": len(matched_skills),
    }


# ============================================================
# JOB RECOMMENDATIONS
# ============================================================

def get_job_recommendations(candidate, jobs):
    recommendations = []

    for job in jobs:
        match = get_job_match(candidate, job)

        if match["total_matched"] > 0:
            recommendations.append({
                "job": job,
                "matched_skills": match["matched_skills"],
                "missing_skills": match["missing_skills"],
                "match_percentage": match["match_percentage"],
            })

    recommendations.sort(
        key=lambda item: item["match_percentage"],
        reverse=True
    )

    return recommendations


# ============================================================
# AI JOB FIT EXPLANATION
# ============================================================

def generate_job_explanation(
    candidate,
    job,
    matched_skills,
    missing_skills
):
    client = _get_client()

    if client is None:
        return (
            "AI explanation is unavailable because the "
            "OPENROUTER_API_KEY environment variable is not set."
        )

    matched = ", ".join(matched_skills) if matched_skills else "None"
    missing = ", ".join(missing_skills) if missing_skills else "None"

    prompt = f"""
You are an AI assistant inside RecruitFlow, an applicant
tracking and recruitment management system.

Analyze the candidate's listed skills against the job
requirements.

JOB TITLE:
{job.title}

REQUIRED SKILLS:
{job.required_skills}

JOB DESCRIPTION:
{job.description}

CANDIDATE SKILLS:
{candidate.skills}

CANDIDATE EXPERIENCE:
{candidate.experience}

MATCHED SKILLS:
{matched}

MISSING SKILLS:
{missing}

Write a professional explanation in 60-90 words.

Explain:
1. Why the matched skills are relevant to the role.
2. Which required skills are missing.
3. What the candidate could improve or learn.

Important:
- Do NOT make a hiring decision.
- Do NOT say the candidate should be hired or rejected.
- Do NOT invent skills, experience, education or qualifications.
- Base the explanation only on the information provided.
"""

    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a professional recruitment "
                        "assistant. Be factual and concise."
                    ),
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            temperature=0.2,
            max_tokens=220,
        )

        return response.choices[0].message.content.strip()

    except Exception as e:
        print("OPENROUTER JOB EXPLANATION ERROR:", e)

        return (
            "AI explanation is temporarily unavailable. "
            "The skill match shown above is calculated "
            "from the candidate's listed skills."
        )


# ============================================================
# AI INTERVIEW QUESTIONS
# ============================================================

def generate_interview_questions(candidate, job):
    client = _get_client()

    fallback_questions = [
        "Explain one project where you used your strongest technical skill.",
        "How would you debug a problem in a Django application?",
        "How do you approach learning a technology you have not used before?",
        "Describe a difficult technical problem you solved.",
        "How do you respond to technical feedback?",
        "Explain one practical use of a skill required for this role.",
    ]

    if client is None:
        return fallback_questions

    prompt = f"""
Generate exactly 6 interview questions for a candidate
applying for the following job.

JOB TITLE:
{job.title}

REQUIRED SKILLS:
{job.required_skills}

JOB DESCRIPTION:
{job.description}

CANDIDATE SKILLS:
{candidate.skills}

CANDIDATE EXPERIENCE:
{candidate.experience}

Requirements:
- Include technical questions.
- Include practical/project questions.
- Include one problem-solving question.
- Include one behavioural question.
- Questions should be appropriate for the candidate's
  listed skills and the job.
- Do not invent candidate experience.
- Do not make a hiring decision.

Return ONLY the numbered questions.
"""

    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an interview preparation "
                        "assistant for recruiters and interviewers."
                    ),
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            temperature=0.3,
            max_tokens=400,
        )

        text = response.choices[0].message.content.strip()

        questions = [
            line.strip()
            for line in text.splitlines()
            if line.strip()
        ]

        return questions if questions else fallback_questions

    except Exception as e:
        print("OPENROUTER INTERVIEW QUESTION ERROR:", e)

        return fallback_questions

# ============================================================
# AI RESUME SCREENING / EVIDENCE ANALYSIS
# ============================================================

def generate_resume_screening(candidate, job):
    client = _get_client()

    fallback_result = {
        "summary": (
            "AI screening is temporarily unavailable. "
            "Please review the candidate's profile and resume manually."
        ),
        "skills": [],
        "evidence": [],
        "gaps": [],
    }

    if client is None:
        return fallback_result

    prompt = f"""
You are an AI-assisted resume screening assistant inside
RecruitFlow.

Your job is to help a recruiter understand whether the
candidate's submitted information provides evidence for
the skills required by the job.

You MUST NOT make the hiring decision.

JOB:
Title: {job.title}

Required Skills:
{job.required_skills}

Job Description:
{job.description}

CANDIDATE:
Skills listed:
{candidate.skills}

Experience:
{candidate.experience}

Resume text:
{_extract_resume_text(candidate)}

Analyze every important required skill.

For each skill classify the evidence as exactly one of:

"Demonstrated"
"Listed Only"
"Not Found"

Meaning:

Demonstrated:
The resume/profile contains meaningful evidence such as
a project, work experience, achievement, certification,
or other concrete evidence showing use of the skill.

Listed Only:
The candidate mentions the skill but there is not enough
supporting evidence in the provided information.

Not Found:
The skill is not found in the provided information.

IMPORTANT:
- Do not assume that a candidate knows a skill merely
  because it is related to another skill.
- Do not invent projects, experience, achievements,
  certifications or qualifications.
- "Not Found" means there is no evidence in the submitted
  information. It does NOT prove the candidate lacks the skill.
- Do not recommend hiring or rejection.
- Do not use age, gender, religion, caste, nationality or
  other personal characteristics.
- Focus only on job-related information.

Return ONLY valid JSON in this exact structure:

{{
  "summary": "A 60-100 word factual screening summary.",
  "skills": [
    {{
      "skill": "Python",
      "status": "Demonstrated",
      "evidence": "Used in the candidate's machine learning projects."
    }}
  ],
  "evidence": [
    "Important concrete evidence found in the candidate information."
  ],
  "gaps": [
    "Important job requirement for which sufficient evidence was not found."
  ]
}}
"""

    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a factual and explainable "
                        "recruitment screening assistant."
                    ),
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            temperature=0.1,
            max_tokens=900,
        )

        text = response.choices[0].message.content.strip()

        # Remove markdown code fences if the model adds them
        if text.startswith("```"):
            text = text.replace("```json", "")
            text = text.replace("```", "")
            text = text.strip()

        import json

        result = json.loads(text)

        return {
            "summary": result.get("summary", ""),
            "skills": result.get("skills", []),
            "evidence": result.get("evidence", []),
            "gaps": result.get("gaps", []),
        }

    except Exception as e:
        print("OPENROUTER RESUME SCREENING ERROR:", e)
        return fallback_result


# ============================================================
# RESUME TEXT EXTRACTION
# ============================================================

def _extract_resume_text(candidate):
    """
    Extract text from uploaded PDF/DOCX/TXT resume.

    If extraction is unavailable, the candidate's manually
    entered profile information is still analyzed.
    """

    if not candidate.resume:
        return "No resume file uploaded."

    try:
        file_name = candidate.resume.name.lower()

        # PDF
        if file_name.endswith(".pdf"):
            import PyPDF2

            with candidate.resume.open("rb") as file:
                reader = PyPDF2.PdfReader(file)

                pages = []

                for page in reader.pages:
                    text = page.extract_text()

                    if text:
                        pages.append(text)

                return "\n".join(pages)[:15000]

        # DOCX
        elif file_name.endswith(".docx"):
            from docx import Document

            document = Document(candidate.resume.path)

            paragraphs = [
                paragraph.text
                for paragraph in document.paragraphs
                if paragraph.text.strip()
            ]

            return "\n".join(paragraphs)[:15000]

        # TXT
        elif file_name.endswith(".txt"):
            with candidate.resume.open("r") as file:
                return file.read()[:15000]

        return "Resume uploaded, but automatic text extraction is not supported for this file type."

    except Exception as e:
        print("RESUME TEXT EXTRACTION ERROR:", e)

        return (
            "Resume was uploaded but could not be automatically "
            "read. Use the candidate profile information."
        )