"""
Section-by-section candidate scoring against a JD.

Skill and experience scores are computed in plain Python from the structured
JD requirements and parsed resume - both are things that can be counted or
measured exactly (does the skill appear? how many months of experience vs.
how many required?), and LLMs are unreliable at precise arithmetic, so we
never ask the LLM to invent these numbers itself.

Project relevance and education-field relatedness genuinely need judgment
(e.g. "JD wants Computer Science, candidate has Electrical Engineering -
how related is that, really?"), so those two scores come from one LLM call
that's given an explicit rubric to follow.
"""

from src.llm.llm_config import get_llm
from src.models.schema import JDRequirements, ParsedResume, SectionJudgment


# ======================================================
# WEIGHTS
# Priority order requested: skill > project > experience > education
# ======================================================
SKILL_WEIGHT = 0.40
PROJECT_WEIGHT = 0.30
EXPERIENCE_WEIGHT = 0.20
EDUCATION_WEIGHT = 0.10


# ======================================================
# SKILL SCORE (deterministic)
# ======================================================
def _normalize(skill: str) -> str:
    return skill.strip().lower()


def _skill_present(required_skill: str, candidate_skills: list) -> bool:
    req = _normalize(required_skill)
    if not req:
        return False

    for cs in candidate_skills:
        cs_norm = _normalize(cs)
        if not cs_norm:
            continue
        # exact match, or one contains the other (handles "React" vs "React.js" etc.)
        if req == cs_norm or req in cs_norm or cs_norm in req:
            return True

    return False


def score_skills(jd: JDRequirements, resume: ParsedResume):
    candidate_skills = [s for s in resume.candidate_skills if s and s.strip()]
    required = [s for s in jd.required_skills if s and s.strip()]
    preferred = [s for s in jd.preferred_skills if s and s.strip()]

    if not required and not preferred:
        # JD didn't specify concrete skills - nothing to penalize against
        return 100, [], []

    matched_required = [s for s in required if _skill_present(s, candidate_skills)]
    matched_preferred = [s for s in preferred if _skill_present(s, candidate_skills)]
    missing_required = [s for s in required if s not in matched_required]

    required_weight = len(required) * 1.0
    preferred_weight = len(preferred) * 0.5
    total_weight = required_weight + preferred_weight

    earned = len(matched_required) * 1.0 + len(matched_preferred) * 0.5

    skill_score = round(min(earned / total_weight, 1.0) * 100) if total_weight > 0 else 100
    matched_skills = matched_required + matched_preferred

    return skill_score, matched_skills, missing_required


# ======================================================
# EXPERIENCE SCORE (deterministic)
# ======================================================
def _format_months(months) -> str:
    months = int(round(months))
    if months <= 0:
        return "No experience"

    years, rem_months = divmod(months, 12)
    parts = []
    if years:
        parts.append(f"{years} year{'s' if years != 1 else ''}")
    if rem_months:
        parts.append(f"{rem_months} month{'s' if rem_months != 1 else ''}")

    return " ".join(parts) if parts else "No experience"


def score_experience(jd: JDRequirements, resume: ParsedResume):
    required_months = max(jd.required_experience_years, 0) * 12
    candidate_months = max(resume.total_experience_months, 0)
    candidate_text = _format_months(candidate_months)

    if required_months <= 0:
        # JD doesn't ask for experience at all - never penalize for this,
        # just report what the candidate actually has for context.
        detail = f"{candidate_text} (not required for this role)"
        return 100, detail

    if candidate_months <= 0:
        detail = f"No experience (JD requires {_format_months(required_months)})"
        return 0, detail

    ratio = candidate_months / required_months
    experience_score = round(min(ratio, 1.0) * 100)

    if candidate_months >= required_months:
        detail = f"{candidate_text} (meets/exceeds JD requirement of {_format_months(required_months)})"
    else:
        detail = f"{candidate_text} (JD requires {_format_months(required_months)} - {experience_score}% match)"

    return experience_score, detail


# ======================================================
# PROJECT + EDUCATION SCORE (LLM judgment)
# ======================================================
PROJECT_EDU_PROMPT = """
You are an expert technical recruiter judging ONE candidate for a specific role.

========================
ROLE REQUIREMENTS
========================
Role: {role_title}
What HR needs: {key_requirements_summary}
Required skills: {required_skills}
Required education field: {required_education_field}
Required education level: {required_education_level}

========================
CANDIDATE'S PROJECTS
========================
{projects}

========================
CANDIDATE'S EDUCATION
========================
{education_details}
(Field: {education_field}, Level: {education_level})

Score this candidate on:

1. project_score (0-100): how relevant and strong are their projects for this specific
   role's requirements? No projects listed should not automatically mean 0 - use a low
   but non-zero score (10-20) if everything else about the resume is otherwise reasonable,
   since not every good candidate lists projects.

2. education_score (0-100): how well their education matches what the JD needs.
   - Same/matching field as required = 85-100
   - A closely related technical field (e.g. JD wants Computer Science and candidate
     studied Electrical/Electronics/IT/Information Systems, or vice versa) = 45-65,
     this is PARTIAL CREDIT - never treat a related engineering field as a total mismatch
   - Clearly unrelated field (e.g. JD wants Computer Science, candidate studied
     Commerce/Arts with no technical coursework) = 10-30
   - If the JD does not specify a required field at all, judge based on level only and
     lean toward 80-100 unless the candidate has no formal education mentioned.

Explain both scores briefly, and give one overall one-to-two sentence summary of why
this candidate lands where they do.
"""


def score_projects_and_education(jd: JDRequirements, resume: ParsedResume) -> SectionJudgment:
    llm = get_llm()
    structured_llm = llm.with_structured_output(SectionJudgment)

    prompt = PROJECT_EDU_PROMPT.format(
        role_title=jd.role_title or "N/A",
        key_requirements_summary=jd.key_requirements_summary or "N/A",
        required_skills=", ".join(jd.required_skills) or "N/A",
        required_education_field=jd.required_education_field or "Not specified",
        required_education_level=jd.required_education_level or "Not specified",
        projects="\n".join(f"- {p}" for p in resume.projects) or "No projects listed",
        education_details=resume.education_details or "Not specified",
        education_field=resume.education_field or "Not specified",
        education_level=resume.education_level or "Not specified",
    )

    try:
        return structured_llm.invoke(prompt)
    except Exception as e:
        return SectionJudgment(
            project_score=0,
            project_reason=f"Scoring failed: {e}",
            education_score=0,
            education_reason=f"Scoring failed: {e}",
            overall_reason=f"Section scoring failed: {e}",
        )


# ======================================================
# COMBINE EVERYTHING INTO ONE CANDIDATE RESULT
# ======================================================
def score_candidate(jd: JDRequirements, resume: ParsedResume, file_name: str) -> dict:
    skill_score, matched_skills, missing_skills = score_skills(jd, resume)
    experience_score, experience_detail = score_experience(jd, resume)
    judgment = score_projects_and_education(jd, resume)

    final_score = round(
        skill_score * SKILL_WEIGHT
        + judgment.project_score * PROJECT_WEIGHT
        + experience_score * EXPERIENCE_WEIGHT
        + judgment.education_score * EDUCATION_WEIGHT
    )
    final_score = max(0, min(final_score, 100))

    if final_score >= 80:
        recommendation = "Strong Fit"
    elif final_score >= 60:
        recommendation = "Moderate Fit"
    elif final_score >= 40:
        recommendation = "Stretch Fit"
    else:
        recommendation = "Not Recommended"

    return {
        "Candidate Name": file_name,
        "Skill Score": skill_score,
        "Matched Skills": matched_skills,
        "Missing Skills": missing_skills,
        "Experience Score": experience_score,
        "Experience Detail": experience_detail,
        "Project Score": judgment.project_score,
        "Project Notes": judgment.project_reason,
        "Education Score": judgment.education_score,
        "Education Detail": judgment.education_reason,
        "Final Score": final_score,
        "Recommendation": recommendation,
        "Reason": judgment.overall_reason,
    }
